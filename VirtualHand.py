# Addon metadata
bl_info = {
    "name": "Virtual Hand",
    "author": "Kai Puth",
    "version": (0, 1),
    "blender": (2, 65, 0),
    "location": "View3D > Add > Mesh > New Object TODO",
    "description": "Show a virtual version of your hands using Leap Motion.",
    "warning": "This addon is experimental.",
    "wiki_url": "",
    "tracker_url": "",
    "category": "System"}


import bpy, mathutils
import Leap


class Finger(object):
    def __init__(self, leap_finger):
        self.id = leap_finger.id
        self.label = "fingertip{0}ofHand{1}".format(leap_finger.id, leap_finger.hand.id)

        # generate fingertip model
        bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=leap_finger.width/2.0, radius2=leap_finger.width/2.0, depth=leap_finger.length, end_fill_type='NGON',
        view_align=False, enter_editmode=False,
        location=(leap_finger.tip_position.x, leap_finger.tip_position.y, leap_finger.tip_position.z),
        rotation=(leap_finger.direction.x, leap_finger.direction.y, leap_finger.direction.z))
        self.ob = bpy.context.object
        self.ob.scale = (VirtualHandsOperator.SCALE, VirtualHandsOperator.SCALE, VirtualHandsOperator.SCALE)
        self.ob.name = self.label

    # update finger model
    def update(self, leap_finger, view, position_offset):
        # update fingertip position
        tip_position = mathutils.Vector((leap_finger.tip_position.x, leap_finger.tip_position.y, leap_finger.tip_position.z))
        tip_position *= VirtualHandsOperator.SCALE
        tip_position.rotate(view.view_rotation)
        self.ob.location = view.view_location + tip_position + position_offset
        
        # update finger direction
        #directionEuler = mathutils.Euler((-leap_finger.direction.pitch, leap_finger.direction.yaw, -leap_finger.direction.roll), 'XYZ')
        directionEuler = mathutils.Euler((leap_finger.direction.pitch, -leap_finger.direction.yaw, leap_finger.direction.roll), 'XYZ')
        directionQuaternion = directionEuler.to_quaternion()
        self.ob.rotation_mode ='QUATERNION'
        self.ob.rotation_quaternion = view.view_rotation * directionQuaternion

        
    # remove finger model
    def removeModel(self):
        bpy.ops.object.select_all(action='DESELECT')
        self.ob.select = True
        bpy.ops.object.delete()
        self.ob = None


class Hand(object):
    def __init__(self, leap_hand):
        self.label = "palmOfHand{}".format(leap_hand.id)

        # generate palm model
        bpy.ops.mesh.primitive_plane_add(rotation=(0,0,0))
        self.palmOb = bpy.context.object
        self.palmOb.name = self.label
        
        # add fingers
        self.fingers = dict()
        for leap_finger in leap_hand.fingers:
            self.fingers[leap_finger.id] = Finger(leap_finger)
    
    # update hand model        
    def update(self, leap_hand, view, position_offset):
        # update hand location
        palm_position = mathutils.Vector((leap_hand.palm_position.x, leap_hand.palm_position.y, leap_hand.palm_position.z))
        palm_position *= VirtualHandsOperator.SCALE
        palm_position.rotate(view.view_rotation)
        self.palmOb.location = view.view_location + palm_position + position_offset
        
        # update hand orientation
        hand_euler = mathutils.Euler((leap_hand.direction.pitch, -leap_hand.direction.yaw, leap_hand.palm_normal.roll), 'XYZ')
        hand_quaternion = hand_euler.to_quaternion()
        self.palmOb.rotation_mode ='QUATERNION'
        self.palmOb.rotation_quaternion = view.view_rotation * hand_quaternion
        
        # update fingers
        leapFingerDict = {finger.id: finger for finger in leap_hand.fingers}
        leapFingerIDs = leapFingerDict.keys()
        blenderFingerIDs = self.fingers.keys()

        # add new fingers
        for id in leapFingerIDs - blenderFingerIDs:
            self.fingers[id] = Finger(leapFingerDict[id])
        
        # delete vanished fingers
        for id in blenderFingerIDs - leapFingerIDs:
            self.fingers[id].removeModel()
            del self.fingers[id]
        
        # update visible fingers
        for id in self.fingers:
            self.fingers[id].update(leapFingerDict[id], view, position_offset)
            
    # remove hand model
    def removeModel(self):
        # remove finger models
        for id in self.fingers:
            self.fingers[id].removeModel()
        self.fingers = None
        
        # remove palm model
        bpy.ops.object.select_all(action='DESELECT')
        self.palmOb.select = True
        bpy.ops.object.delete()
        self.palmOb = None
        

class VirtualHandsOperator(bpy.types.Operator):
    """Show a virtual version of your hands using Leap Motion."""
    bl_idname = "wm.virtual_hands_operator"
    bl_label = "Show virtual hands."

    _timer = None
    controller = Leap.Controller()
    
    #previousFrameID = -1
    #generatedModels = list()
    #hands = dict()
    
    #GROUP_NAME = "virtual_hands"
    
    UPDATE_DELAY = 1. / 30. # seconds
    SCALE = 0.05

    def __init__(self):
        self.hands = dict()

    @classmethod
    def poll(cls, context):
        controller = VirtualHandsOperator.controller
        if not controller.is_connected:
            print("Leap motion controller is not connected to a device.")
            return False
        
        return True

    def modal(self, context, event):
        if event.type == 'ESC':
            return self.cancel(context)

        if event.type == 'TIMER':
            controller = VirtualHandsOperator.controller
            frame = controller.frame()

            '''            
            for hand in frame.hands:
                id = "palmOfHand{}".format(hand.id)
                palmOb = bpy.data.objects.get(id)

                # generate palm model if new
                if palmOb is None:
                    bpy.ops.mesh.primitive_plane_add(rotation=(0,0,0))
                    palmOb = bpy.context.object
                    palmOb.name = id
                    VirtualHandsOperator.generatedModels.append(palmOb)

                # update hand location
                v3d = context.space_data
                rv3d = v3d.region_3d

                palm_position = mathutils.Vector((hand.palm_position.x, hand.palm_position.y, hand.palm_position.z))
                palm_position *= VirtualHandsOperator.SCALE
                palm_position.rotate(rv3d.view_rotation)
                position_offset = mathutils.Vector((0, 0, 0))
                position_offset.rotate(rv3d.view_rotation)
                palmOb.location = rv3d.view_location + palm_position + position_offset
                
                # update virtual hand orientation
                hand_euler = mathutils.Euler((hand.direction.pitch, -hand.direction.yaw, hand.palm_normal.roll), 'XYZ')
                hand_quaternion = hand_euler.to_quaternion()
                palmOb.rotation_mode ='QUATERNION'
                palmOb.rotation_quaternion = rv3d.view_rotation * hand_quaternion
                
                # update fingers
                for finger in hand.fingers:
                    id = "fingertip{0}ofHand{1}".format(finger.id, hand.id)
                    fingerOb = bpy.data.objects.get(id)

                    # generate fingertip model if new
                    if fingerOb is None:
                        bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=finger.width, radius2=finger.width, depth=finger.length, end_fill_type='NGON',
                        view_align=False, enter_editmode=False,
                        location=(finger.tip_position.x, finger.tip_position.y, finger.tip_position.z),
                        rotation=(finger.direction.x, finger.direction.y, finger.direction.z))
                        fingerOb = bpy.context.object
                        fingerOb.scale = (VirtualHandsOperator.SCALE, VirtualHandsOperator.SCALE, VirtualHandsOperator.SCALE)
                        fingerOb.name = id
                        VirtualHandsOperator.generatedModels.append(fingerOb)
                            
                    # update fingertip position
                    tip_position = mathutils.Vector((finger.tip_position.x, finger.tip_position.y, finger.tip_position.z))
                    tip_position *= VirtualHandsOperator.SCALE
                    fingerOb.location = rv3d.view_location + tip_position + position_offset

            # delete vanished hands
            previousFrame = controller.frame(VirtualHandsOperator.previousFrameID)
            oldIDs = set(hand.id for hand in previousFrame.hands)
            currentIDs = set(hand.id for hand in frame.hands)
            missingIDs = oldIDs - currentIDs
            VirtualHandsOperator.previousFrameID = frame.id
            
            bpy.ops.object.select_all(action='DESELECT')
            for id in missingIDs:
                id = "palmOfHand{}".format(hand.id)
                bpy.data.objects[id].select = True
            bpy.ops.object.delete()
            '''
            # update hands
            leapHandDict = {hand.id: hand for hand in frame.hands}
            leapHandIDs = leapHandDict.keys()
            blenderHandIDs = self.hands.keys()
    
            # add new hands
            for id in leapHandIDs - blenderHandIDs:
                self.hands[id] = Hand(leapHandDict[id])
            
            # delete vanished hands
            for id in blenderHandIDs - leapHandIDs:
                self.hands[id].removeModel()
                del self.hands[id]
            
            # all visible remaining hand models
            v3d = context.space_data
            rv3d = v3d.region_3d
            position_offset = mathutils.Vector((0, 0, 0))
            position_offset.rotate(rv3d.view_rotation)
            for id in self.hands:
                self.hands[id].update(leapHandDict[id], rv3d, position_offset)
                
        return {'PASS_THROUGH'}

    def execute(self, context):
        self._timer = context.window_manager.event_timer_add(VirtualHandsOperator.UPDATE_DELAY, context.window)
        context.window_manager.modal_handler_add(self)
        print("Executing operation. (Entering modal mode.)")
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        # delete generated objects
        for id in self.hands:
            self.hands[id].removeModel()
        self.hands.clear()
        
        context.window_manager.event_timer_remove(self._timer)
        print("Operation canceled.")
        
        return {'CANCELLED'}


def register():
    bpy.utils.register_class(VirtualHandsOperator)


def unregister():
    bpy.utils.unregister_class(VirtualHandsOperator)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.wm.virtual_hands_operator()
