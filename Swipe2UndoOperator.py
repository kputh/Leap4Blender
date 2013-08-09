# Addon metadata
bl_info = {
    "name": "Swipe to undo",
    "author": "Kai Puth",
    "version": (0, 1),
    "blender": (2, 65, 0),
    "location": "View3D > Add > Mesh > New Object TODO",
    "description": "Enables Leap Motion swipe gesture to undo.",
    "warning": "This addon is experimental.",
    "wiki_url": "",
    "tracker_url": "",
    "category": "System"}


import bpy
import Leap
from Leap import SwipeGesture


class Swipe2UndoOperator(bpy.types.Operator):
    """Enable swipe to undo."""
    bl_idname = "wm.swipe2undo_operator"
    bl_label = "Use Leap Motion and a swipe gesture to undo."

    _timer = None
    controller = Leap.Controller()
    lastSwipeID = None
    
    UPDATE_DELAY = 0.0334 # seconds

    @classmethod
    def poll(cls, context):
        if not bpy.ops.ed.undo.poll():
            print("bpy.ops.ed.undo() not executable.")
            return False
        
        controller = Leap.Controller()
        if not controller.is_connected:
            print("Leap motion controller is not connected to a device.")
            return False
        
        return True

    def modal(self, context, event):
        if event.type == 'ESC':
            return self.cancel(context)

        if event.type == 'TIMER':
            frame = Swipe2UndoOperator.controller.frame()
            for gesture in frame.gestures():
                if gesture.type == Leap.Gesture.TYPE_SWIPE:
                    swipe = SwipeGesture(gesture)
                    if swipe.state == Leap.Gesture.STATE_STOP and swipe.id != Swipe2UndoOperator.lastSwipeID:
                        Swipe2UndoOperator.lastSwipeID = swipe.id
                        if swipe.direction.x > 0:
                            print("left-to-right swipe detected.")
                        if swipe.direction.x < 0:
                            print("right-to-left swipe detected.")
                        '''
                        if bpy.ops.ed.undo.poll():
                            bpy.ops.ed.undo()
                        '''
                        break

        return {'PASS_THROUGH'}

    def execute(self, context):
        # Enable gestures and filters
        Swipe2UndoOperator.controller.enable_gesture(Leap.Gesture.TYPE_SWIPE);

        if(Swipe2UndoOperator.controller.config.set("Gesture.Swipe.MinLength", 200.0)
            and Swipe2UndoOperator.controller.config.set("Gesture.Swipe.MinVelocity", 750)):
                Swipe2UndoOperator.controller.config.save()

        self._timer = context.window_manager.event_timer_add(Swipe2UndoOperator.UPDATE_DELAY, context.window)
        context.window_manager.modal_handler_add(self)
        print("Executing operation. (Entering modal mode.)")
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        print("Operation canceled.")
        return {'CANCELLED'}


def register():
    bpy.utils.register_class(Swipe2UndoOperator)


def unregister():
    bpy.utils.unregister_class(Swipe2UndoOperator)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.wm.swipe2undo_operator()
