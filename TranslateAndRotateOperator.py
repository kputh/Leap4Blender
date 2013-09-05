# Addon metadata
bl_info = {
    "name": "Translate and rotate by gesture",
    "author": "Kai Puth",
    "version": (0, 1),
    "blender": (2, 65, 0),
    "location": "View3D > Add > Mesh > New Object TODO",
    "description": "Make a V with your fingers to 'grab' the active object.",
    "warning": "This addon is experimental.",
    "wiki_url": "",
    "tracker_url": "",
    "category": "System"}


import math
import bpy, mathutils
import Leap


class TranslateAndRotateOperator(bpy.types.Operator):
    """Make a V with your fingers to 'grab' the active object."""
    bl_idname = "wm.translate_and_rotate_operator"
    bl_label = "Translate and rotate by gesture"

    _timer = None

    UPDATE_DELAY = 1.0 / 30.0 # seconds
    SCALE = 0.05
    RANGE = 10.0
    EPSILON = math.pi / 18.0 # 10°

    def __init__(self):
        self.controller = Leap.Controller()
        
        # create attributes
        self.handID = None
        self.startPosition = None
        self.startOrientierung = None
        self.ob = None
        self.startLocation = None
        self.startRotation = None

    @classmethod
    def poll(cls, context):
        controller = Leap.Controller()

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
            
            if self.handID is not None:
                # Trying to track hand.
                hand = frame.hand(self.handID)
                if hand.is_valid:
                    # Hand tracking successfull. Checking fingers.
                    if self.isGesture(hand):
                        # Finger tracking succeeded. Update object.
                        self.updateObject(frame, context)
                    else:
                        # Finger tracking failed. Assuming end of gesture.
                        # Reseting state
                        self.handID = None
                        self.startPosition = None
                        self.startOrientierung = None
                        self.ob = None
                        self.startLocation = None
                        self.startRotation = None
                else:
                    # Hand tracking failed. Searching for gesture.
                    for hand in frame.hands:
                        if self.isGesture(hand):
                            # Replacement hand found. Updating state and object.
                            self.handID = hand.id
                            
                            # Update object
                            self.updateObject(frame, context)
                            
                            break
                    # No replacement hand/gesture found. Assuming hand moved out of sight. Resetting state and object.
                    # TODO
            else:
                # No hand is being tracked. Searching for gesture.
                for hand in frame.hands:
                    if self.isGesture(hand):
                        # Gesture found. Memorizing starting position and orientation.
                        print("New gesture found.")
                        self.handID = hand.id
                        self.startPosition = hand.palm_position
                        orientation = Leap.Vector()
                        orientation.pitch = hand.direction.pitch        
                        orientation.yaw = hand.direction.yaw
                        orientation.roll = hand.palm_normal.roll
                        self.startOrientierung = orientation
                        self.ob = bpy.context.object
                        self.ob.rotation_mode ='QUATERNION'
                        self.startLocation = self.ob.location.copy()
                        self.startRotation = self.ob.rotation_quaternion.copy()
                        
                        break
                
        return {'PASS_THROUGH'}

    def execute(self, context):
        self._timer = context.window_manager.event_timer_add(TranslateAndRotateOperator.UPDATE_DELAY, context.window)
        context.window_manager.modal_handler_add(self)
        print("Executing operation. (Entering modal mode.)")
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        # reset object position and rotation
        self.ob.location = self.startLocation
        self.ob.rotation_quaternion = self.startRotation
        
        # reset attributes
        self.handID = None
        self.startPosition = None
        self.startOrientierung = None
        self.ob = None
        self.startLocation = None
        self.startRotation = None

        context.window_manager.event_timer_remove(self._timer)
        print("Operation canceled.")
        
        return {'CANCELLED'}

    def isGesture(self, hand):
        
        if len(hand.fingers) != 2:
            return False
        
        finger1 = hand.fingers[0]
        finger2 = hand.fingers[1]
        angle = finger1.direction.angle_to(finger2.direction)
        min = math.pi / 18  # 10°
        max = math.pi / 4   # 45°
        if min < angle and angle < max:
            return True
        else:
            return False

    def searchGesture(self, frame):
        for hand in frame.hands:
            if self.isGesture(hand):
                # Gesture found. Memorizing hand and fingers.
                self.handID = hand.id
                self.fingerIDs = (hand.fingers[0].id, hand.fingers[1].id)
                return True
                
        return False
                
    def updateObject(self, frame, context):
        v3d = context.space_data
        rv3d = v3d.region_3d
        view = context.space_data.region_3d
    
        # update location
        hand = frame.hand(self.handID)

        difference = hand.palm_position - self.startPosition
        difference = mathutils.Vector((difference.x, difference.y, difference.z))
        difference *= TranslateAndRotateOperator.SCALE
        difference.rotate(view.view_rotation)
        self.ob.location = self.startLocation + difference

        # update direction
        pitch = hand.direction.pitch - self.startOrientierung.pitch     # rotation around the x axis
        yaw = hand.direction.yaw - self.startOrientierung.yaw           # rotation around the y axis
        roll = hand.palm_normal.roll - self.startOrientierung.roll      # rotation around the z axis
        #difference = mathutils.Euler((pitch, -yaw, -roll), 'XYZ').to_quaternion()
        difference = mathutils.Euler((roll, pitch, yaw), 'XYZ').to_quaternion()
        difference.rotate(view.view_rotation)
        print("difference: {}".format(difference))
        print("self.startRotation: {}".format(self.startRotation))
        print("self.startRotation * difference: {}".format(self.startRotation * difference))
        self.ob.rotation_quaternion = self.startRotation * difference   # TODO relative Differenz benutzen?


def register():
    bpy.utils.register_class(TranslateAndRotateOperator)


def unregister():
    bpy.utils.unregister_class(TranslateAndRotateOperator)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.wm.translate_and_rotate_operator()
