# Addon metadata
bl_info = {
    "name": "Scale by gesture",
    "author": "Kai Puth",
    "version": (0, 1),
    "blender": (2, 65, 0),
    "location": "View3D > Add > Mesh > New Object TODO",
    "description": "Scale the active object using Leap Motion.",
    "warning": "This addon is experimental.",
    "wiki_url": "",
    "tracker_url": "",
    "category": "System"}


import bpy, mathutils
import Leap


class ScaleByGestureOperator(bpy.types.Operator):
    """Scale the active object using a gesture and Leap Motion."""
    bl_idname = "wm.scale_by_gesture_operator"
    bl_label = "Scale active object by gesture."

    _timer = None

    #previousFrameID = -1
    #generatedModels = list()
    #hands = dict()
    
    #GROUP_NAME = "virtual_hands"
    
    UPDATE_DELAY = 1. / 30. # seconds
    SCALE = 0.05
    EPSILON = PI/36 # 5°
    STATE_ACTIVE = 'active'
    STATE_SUSPENDED = 'suspended'
    STATE_WAITING = 'waiting'

    def __init__(self):
        self.controller = Leap.Controller()
        #self.hands = dict()
        
        self.ob = None
        self.startScale = None
        self.startDistance = None
        self.state = ScaleByGestureOperator.STATE_WAITING
        self.trackedHandIDs = None

    @classmethod
    def poll(cls, context):
        controller = ScaleByGestureOperator.controller
        if not controller.is_connected:
            print("Leap motion controller is not connected to a device.")
            return False
        
        if bpy.context.active_object is None:
            print("There is no active object.")
            return False
        
        return True

    def modal(self, context, event):
        if event.type == 'ESC':
            return self.cancel(context)

        if event.type == 'TIMER':
            controller = self.controller
            frame = controller.frame()
            handCount = len(frame.hands)
            
            if self.state == ScaleByGestureOperator.STATE_WAITING:
                
            if self.state == ScaleByGestureOperator.STATE_ACTIVE:
                hand1 = frame.hand(self.trackedHandIDs[0])
                hand2 = frame.hand(self.trackedHandIDs[1])
                
                # test hand visibility
                if hand1.invalid or hand2.invalid:
                    # suspend scaling
                    self.state = ScaleByGestureOperator.STATE_SUSPENDED
                    self.ob.scale = self.startScale
                    
                    if hand1.invalid and hand2.invalid:
                        self.trackedHandIDs = None
                    elif hand1.invalid:
                        self.trackedHandIDs = (hand2.id)
                    else
                        self.trackedHandIDs = (hand1.id)
                    return {'RUNNING_MODAL'}
                    
                normal1 = hand1.palm_normal
                normal2 = hand2.palm_normal
                angleInRadians = normal1.angle_to(normal2)
                
                distance = hand1.palm_position.distance_to(hand2.palm_position)
                scale = distance / self.startDistance

                # test angle of hand normals
                if angleInRadians > ScaleByGestureOperator.EPSILON:
                    # scaling completed
                    self.ob.scale = (scale, scale, scale)

                    self.state = ScaleByGestureOperator.STATE_WAITING
                    self.ob = None
                    self.startScale = None
                    self.startDistance = None
                    self.trackedHandsIDs = None
                    return {'RUNNING_MODAL'}
                    
                # continue scaling
                self.ob.scale = (scale, scale, scale)

            '''            
            for index1 in range(handcount):
                for index2 in range(index1 + 1, handCount):
                    normal1 = frame.hands[index1].palm_normal
                    normal2 = frame.hands[index2].palm_normal
                    angleInRadians = normal1.angle_to(normal2)
                    
                    if angleInRadians < ScaleByGestureOperator.EPSILON:
                        # scaling gesture detected
                        self.state = ScaleByGestureOperator.STATE_ACTIVE
                    

            for hand in frame.hands:
                id = "palmOfHand{}".format(hand.id)
                palmOb = bpy.data.objects.get(id)

                # generate palm model if new
                if palmOb is None:
                    bpy.ops.mesh.primitive_plane_add(rotation=(0,0,0))
                    palmOb = bpy.context.object
                    palmOb.name = id
                    ScaleByGestureOperator.generatedModels.append(palmOb)

                # update hand location
                v3d = context.space_data
                rv3d = v3d.region_3d

                palm_position = mathutils.Vector((hand.palm_position.x, hand.palm_position.y, hand.palm_position.z))
                palm_position *= ScaleByGestureOperator.SCALE
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
                        fingerOb.scale = (ScaleByGestureOperator.SCALE, ScaleByGestureOperator.SCALE, ScaleByGestureOperator.SCALE)
                        fingerOb.name = id
                        ScaleByGestureOperator.generatedModels.append(fingerOb)
                            
                    # update fingertip position
                    tip_position = mathutils.Vector((finger.tip_position.x, finger.tip_position.y, finger.tip_position.z))
                    tip_position *= ScaleByGestureOperator.SCALE
                    fingerOb.location = rv3d.view_location + tip_position + position_offset

            # delete vanished hands
            previousFrame = controller.frame(ScaleByGestureOperator.previousFrameID)
            oldIDs = set(hand.id for hand in previousFrame.hands)
            currentIDs = set(hand.id for hand in frame.hands)
            missingIDs = oldIDs - currentIDs
            ScaleByGestureOperator.previousFrameID = frame.id
            
            bpy.ops.object.select_all(action='DESELECT')
            for id in missingIDs:
                id = "palmOfHand{}".format(hand.id)
                bpy.data.objects[id].select = True
            bpy.ops.object.delete()
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
            '''
                
        return {'PASS_THROUGH'}

    def execute(self, context):
        self._timer = context.window_manager.event_timer_add(ScaleByGestureOperator.UPDATE_DELAY, context.window)
        context.window_manager.modal_handler_add(self)
        print("Executing operation. (Entering modal mode.)")
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        # restore original scale
        self.ob.scale = self.startScale
        
        # reset variables
        self.startScale = None
        self.startDistance = None
        # todo
        
        context.window_manager.event_timer_remove(self._timer)
        print("Operation canceled.")
        
        return {'CANCELLED'}


def register():
    bpy.utils.register_class(ScaleByGestureOperator)


def unregister():
    bpy.utils.unregister_class(ScaleByGestureOperator)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.wm.scale_by_gesture_operator()
