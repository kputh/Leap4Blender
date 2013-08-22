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

    #previousFrameID = -1
    #generatedModels = list()
    #hands = dict()
    
    #GROUP_NAME = "virtual_hands"
    
    UPDATE_DELAY = 1. / 30. # seconds
    SCALE = 0.05
    EPSILON = math.pi / 36. # 5°
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
            
            if handCount < 2:
                return {'RUNNING_MODAL'}

            hand1 = None
            hand2 = None
            if self.trackedHandIDs is not None and frame.hand(self.trackedHandIDs[0]).is_valid and frame.hand(self.trackedHandIDs[1]).is_valid:
                # two hands trackable
                hand1 = frame.hand(self.trackedHandIDs[0])
                hand2 = frame.hand(self.trackedHandIDs[1])
                
                angleInRadians = hand1.palm_normal.angle_to(hand2.palm_normal)
                distance = hand1.palm_position.distance_to(hand2.palm_position)
                scale = distance / self.startDistance

                self.ob.scale = (self.startScale.x * scale, self.startScale.y * scale, self.startScale.z * scale)
                if angleInRadians > ScaleByGestureOperator.EPSILON:     # todo: prüfen
                # scaling completed
                    self.ob = None
                    self.startScale = None
                    self.startDistance = None
                    self.trackedHandsIDs = None
                else:
                    # scaling continues
                    pass
            else:
                # less than two hands tracked
                for index1 in range(handCount):
                    for index2 in range(index1 + 1, handCount):
                        hand1 = frame.hands[index1]
                        hand2 = frame.hands[index2]
                        angleInRadians = hand1.palm_normal.angle_to(hand2.palm_normal)
                        
                        if angleInRadians < ScaleByGestureOperator.EPSILON:     # todo: prüfen
                            # scaling gesture detected
                            print("scaling gesture detected")
                            self.ob = bpy.context.object
                            self.startScale = self.ob.scale
                            self.startDistance = hand1.palm_position.distance_to(hand2.palm_position)
                            self.trackedHandIDs = (hand1.id, hand2.id)

            
            '''
            # lost track of a hand in mid-gesture
            if self.state == ScaleByGestureOperator.STATE_SUSPENDED:
                print("STATE_SUSPENDED")
                for index1 in range(handCount):
                    for index2 in range(index1 + 1, handCount):
                        hand1 = frame.hands[index1]
                        hand2 = frame.hands[index2]
                        angleInRadians = hand1.palm_normal.angle_to(hand2.palm_normal)
                        
                        if angleInRadians < ScaleByGestureOperator.EPSILON:
                            # scaling gesture detected
                            print("scaling gesture detected")
                            self.state = ScaleByGestureOperator.STATE_ACTIVE
                            self.ob = bpy.context.object
                            self.trackedHandIDs = (hand1.id, hand2.id)
    
            # waiting for a gesture                
            if self.state == ScaleByGestureOperator.STATE_WAITING:
                print("STATE_WAITING")
                
                for index1 in range(handCount):
                    for index2 in range(index1 + 1, handCount):
                        hand1 = frame.hands[index1]
                        hand2 = frame.hands[index2]
                        angleInRadians = hand1.palm_normal.angle_to(hand2.palm_normal)
                        
                        if angleInRadians < ScaleByGestureOperator.EPSILON:
                            # scaling gesture detected
                            print("scaling gesture detected")
                            self.state = ScaleByGestureOperator.STATE_ACTIVE
                            self.ob = bpy.context.object
                            self.startScale = self.ob.scale
                            self.startDistance = hand1.palm_position.distance_to(hand2.palm_position)
                            self.trackedHandIDs = (hand1.id, hand2.id)
            
            # tracking gesture
            if self.state == ScaleByGestureOperator.STATE_ACTIVE:
                print("STATE_ACTIVE")
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
                    else:
                        self.trackedHandIDs = (hand1.id)
                    return {'RUNNING_MODAL'}
                    
                angleInRadians = hand1.palm_normal.angle_to(hand2.palm_normal)
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
                self.ob.scale = (scale, scale, scale)       # todo: Fehler
            '''

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
