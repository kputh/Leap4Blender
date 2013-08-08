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


class Swipe2UndoOperator(bpy.types.Operator):
    """Enable swipe to undo."""
    bl_idname = "wm.swipe2undo_operator"
    bl_label = "Use Leap Motion and a swipe gesture to undo."

    _timer = None
    controller = Leap.Controller()
    
    UPDATE_DELAY = 0.0334

    @classmethod
    def poll(cls, context):
        if not bpy.ops.ed.undo.poll():
            return False
        
        controller = Leap.Controller()
        if not controller.is_connected:
            return False
        
        return True

    def modal(self, context, event):
        if event.type == 'ESC':
            return self.cancel(context)

        if event.type == 'TIMER':
            frame = controller.frame()
            for gesture in frame.gestures():
                if gesture.type == Leap.Gesture.TYPE_SWIPE:
                    swipe = SwipeGesture(gesture)
                    if gesture.state == Leap.Gesture.STATE_STOP:
                        print("undo")
                        if bpy.ops.ed.undo.poll():
                            bpy.ops.ed.undo()
                        break

        return {'PASS_THROUGH'}

    def execute(self, context):
        # Enable gestures and filters
        Swipe2UndoOperator.controller.enable_gesture(Leap.Gesture.TYPE_SWIPE);

        if(Swipe2UndoOperator.controller.config.set_float("Gesture.Swipe.MinLength", 200.0)
            and Swipe2UndoOperator.controller.config.set_float("Gesture.Swipe.MinVelocity", 750)):
                Swipe2UndoOperator.controller.config().save()

        self._timer = context.window_manager.event_timer_add(Swipe2UndoOperator.UPDATE_DELAY, context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        Swipe2UndoOperator.controller.disable_gesture(Leap.Gesture.TYPE_SWIPE);
        return {'CANCELLED'}


def register():
    bpy.utils.register_class(Swipe2UndoOperator)


def unregister():
    bpy.utils.unregister_class(Swipe2UndoOperator)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.wm.swipe2undo_operator()
