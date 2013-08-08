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
import Leap, sys
from Leap import SwipeGesture


class UndoListener(Leap.Listener):
    
    def on_init(self, controller):
        print("Initialized")
    
    def on_connect(self, controller):
        print("Connected")
    
        # Enable gestures
        controller.enable_gesture(Leap.Gesture.TYPE_SWIPE);

        if(controller.config.set_float("Gesture.Swipe.MinLength", 200.0)
          and controller.config.set_float("Gesture.Swipe.MinVelocity", 750)):
            controller.config().save()
    
    def on_disconnect(self, controller):
        # Note: not dispatched when running in a debugger.
        print("Disconnected")
    
    def on_exit(self, controller):
        print("Exited")
    
    def on_frame(self, controller):
        # Get the most recent frame and report some basic information
        frame = controller.frame()
    
        for gesture in frame.gestures():

            if gesture.type == Leap.Gesture.TYPE_SWIPE:
                swipe = SwipeGesture(gesture)
                if gesture.state == Leap.Gesture.STATE_STOP:
                    print("Swipe id: %d, state: %s, position: %s, direction: %s, speed: %f" % (
                            gesture.id, self.state_string(gesture.state),
                            swipe.position, swipe.direction, swipe.speed))
                    if bpy.ops.ed.undo.poll():
                        bpy.ops.ed.undo()
                    break
    
    def state_string(self, state):
        if state == Leap.Gesture.STATE_START:
            return "STATE_START"
    
        if state == Leap.Gesture.STATE_UPDATE:
            return "STATE_UPDATE"
    
        if state == Leap.Gesture.STATE_STOP:
            return "STATE_STOP"
    
        if state == Leap.Gesture.STATE_INVALID:
            return "STATE_INVALID"


class swipe2undo(bpy.types.Operator):
    """Leap Motion swipe to undo"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "object.move_x"        # unique identifier for buttons and menu items to reference.
    bl_label = "Move X by One"         # display name in the interface.
    bl_options = {'REGISTER'}  # enable undo for the operator.
    
    def execute(self, context):
    
        # Create a sample listener and controller
        listener = UndoListener()
        controller = Leap.Controller()
    
        # Have the sample listener receive events from the controller
        controller.add_listener(listener)
    
        # Keep this process running until Enter is pressed
        print("Press Enter to quit...")
        sys.stdin.readline()
    
        # Remove the sample listener when done
        controller.remove_listener(listener)
    
        return {'FINISHED'}
    

# Registration

def register():
    bpy.utils.register_class(swipe2undo)


def unregister():
    bpy.utils.unregister_class(swipe2undo)


if __name__ == "__main__":
    register()
    # Create a sample listener and controller
    listener = UndoListener()
    controller = Leap.Controller()
    
    # Have the sample listener receive events from the controller
    controller.add_listener(listener)

    # Keep this process running until Enter is pressed
    print("Press Enter to quit...")
    sys.stdin.readline()

    # Remove the sample listener when done
    controller.remove_listener(listener)
