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


class VirtualHandsOperator(bpy.types.Operator):
    """Show a virtual version of your hands using Leap Motion."""
    bl_idname = "wm.virtual_hands_operator"
    bl_label = "Show virtual hands."

    _timer = None
    controller = Leap.Controller()
    
    previousFrameID = -1
    generatedModels = list()
    
    GROUP_NAME = "virtual_hands"
    
    UPDATE_DELAY = 1. / 30. # seconds
    SCALE = 0.05

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

        return {'PASS_THROUGH'}

    def execute(self, context):
        self._timer = context.window_manager.event_timer_add(VirtualHandsOperator.UPDATE_DELAY, context.window)
        context.window_manager.modal_handler_add(self)
        print("Executing operation. (Entering modal mode.)")
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        # delete generated objects
        for ob in VirtualHandsOperator.generatedModels:
            ob.select = True
        bpy.ops.object.delete()
        VirtualHandsOperator.generatedModels = list()
        
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
