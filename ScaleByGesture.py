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


import math
import bpy, mathutils
import Leap


class ScaleByGestureOperator(bpy.types.Operator):
    """Scale the active object using a gesture and Leap Motion."""
    bl_idname = "wm.scale_by_gesture_operator"
    bl_label = "Scale active object by gesture."

    _timer = None

    UPDATE_DELAY = 1.0 / 30.0 # seconds
    EPSILON = math.pi / 18.0 # 10°

    def __init__(self):
        self.controller = Leap.Controller()
        
        # create attributes
        self.ob = None
        self.startScale = None
        self.startDistance = None
        self.trackedHandIDs = None

    @classmethod
    def poll(cls, context):
        controller = Leap.Controller()
        '''
        if not controller.is_connected:
            print("Leap motion controller is not connected to a device.")
            return False
        '''
        
        if bpy.context.active_object is None:
            print("There is no active object.")
            return False
        
        return True

    # todo: prüfen
    def isGesture(self, hand1, hand2):
        isGesture = True
        
        # do both hands point in the same direction?
        # do both palm normals point in opposite directions?
        # do both palms face each other?
        
        # do both hands point in the same direction?
        angleInRadians = hand1.direction.angle_to(hand2.direction)
        if angleInRadians < ScaleByGestureOperator.EPSILON:
            isGesture = isGesture and True
        else:
            isGesture = False
        
        # do both palm normals point in opposite directions?
        angleInRadians = hand1.palm_normal.angle_to(hand2.palm_normal)
        if math.pi - angleInRadians < ScaleByGestureOperator.EPSILON:
            # palm normals point towards each other
            isGesture = isGesture and True
        elif angleInRadians < ScaleByGestureOperator.EPSILON:
            # palms normals point in the same direction (might be a tracking error)
            isGesture = isGesture and True
        else:
            isGesture = False
            
        # do both palms face each other?
        # TODO
        
        return isGesture
        
    def modal(self, context, event):
        if event.type == 'ESC':
            return self.cancel(context)

        if event.type == 'TIMER':
            controller = self.controller
            frame = controller.frame()
            handCount = len(frame.hands)
            
            # are enough hands visible to form a gesture?
            if handCount < 2:
                return {'RUNNING_MODAL'}

            hand1 = None
            hand2 = None
            # gesture in progress?
            if self.trackedHandIDs is not None:
                # yes - trying to continue scaling gesture
                hand1 = frame.hand(self.trackedHandIDs[0])
                hand2 = frame.hand(self.trackedHandIDs[1])

                # can both hands still be tracked?
                if hand1.is_valid and hand2.is_valid:
                    # yes - update model and evaluate gesture state
                    distance = hand1.palm_position.distance_to(hand2.palm_position)
                    scale = distance / self.startDistance
                    self.ob.scale = self.startScale * scale
                    
                    # is the gesture finished?
                    if not self.isGesture(hand1, hand2):
                        # yes - reset state
                        self.ob = None
                        self.startScale = None
                        self.startDistance = None
                        self.trackedHandIDs = None
                    else:
                        # no - continue
                        pass
                else:
                    # no - tracking failed? search for gesture!
                    for index1 in range(handCount):
                        for index2 in range(index1 + 1, handCount):
                            hand1 = frame.hands[index1]
                            hand2 = frame.hands[index2]

                            # has a replacement been detected?
                            if self.isGesture(hand1, hand2):
                                # yes - update model and state, abort search
                                distance = hand1.palm_position.distance_to(hand2.palm_position)
                                scale = distance / self.startDistance
                                self.ob.scale = self.startScale * scale
                                self.trackedHandIDs = (hand1.id, hand2.id)
                                return {'RUNNING_MODAL'}
                            else:
                                # no - continue search
                                continue
            else:
                # no - searching for gesture
                for index1 in range(handCount):
                    for index2 in range(index1 + 1, handCount):
                        hand1 = frame.hands[index1]
                        hand2 = frame.hands[index2]
                        
                        # has a gesture been found?
                        if self.isGesture(hand1, hand2):
                            # yes - start tracking, update state, abort search
                            self.ob = bpy.context.object
                            self.startScale = self.ob.scale.copy()
                            self.startDistance = hand1.palm_position.distance_to(hand2.palm_position)
                            self.trackedHandIDs = (hand1.id, hand2.id)
                            return {'RUNNING_MODAL'}
                        else:
                            # no - continue search
                            continue
        return {'PASS_THROUGH'}

    def execute(self, context):
        self._timer = context.window_manager.event_timer_add(ScaleByGestureOperator.UPDATE_DELAY, context.window)
        context.window_manager.modal_handler_add(self)
        print("Executing operation. (Entering modal mode.)")
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        # restore original scale
        if self.ob is not None:
            self.ob.scale = self.startScale
        
        # reset variables
        self.ob = None
        self.startScale = None
        self.startDistance = None
        self.trackedHandIDs = None
        
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
