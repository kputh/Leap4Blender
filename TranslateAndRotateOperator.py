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
        self.tracedPointables = dict()

    @classmethod
    def poll(cls, context):
        controller = Leap.Controller()
        '''
        if not controller.is_connected:
            print("Leap motion controller is not connected to a device.")
            return False
        '''
        
        return True

    def modal(self, context, event):
        if event.type == 'ESC':
            return self.cancel(context)

        if event.type == 'TIMER':
            controller = self.controller
            frame = controller.frame()
            
            if self.activeHand is Not None:
                # Trying to track hand.
                if self.activeHand.is_valid:
                    # Hand tracking successfull. Checking fingers.
                    if len(hand.fingers) == 2 and self.finger1.is_valid and self.finger2.is_valid:  # überdenken
                        # Finger tracking succeeded. Update object.
                        self.updateObject()
                    else:
                        # Finger tracking failed. Assuming end of gesture.
                        # Reseting state
                        # TODO
                else:
                    # Hand tracking failed. Searching for gesture.
                    for hand in frame.hands:
                        if len(hand.fingers) == 2:
                            # Replacement hand found. Updating state and object.
                            self.activeHand = hand
                            self.finger1 = hand.fingers[0]
                            self.finger2 = hand.fingers[1]
                            
                            # Update object
                            self.updateObject()
                            
                            break
                    # No replacement hand/gesture found. Assuming hand moved out of sight. Resetting state and object.
                    # TODO
            else:
            # No hand is being tracked. Searching for gesture.
            for hand in frame.hands:
                if len(hand.fingers) == 2:
                    # Gesture found. Memorizing starting position and orientation.
                    self.activeHand = hand
                    self.finger1 = hand.fingers[0]
                    self.finger2 = hand.fingers[1]
                    self.startPosition = self.finger1.stabilized_tip_position - self.finger2.stabilized_tip_position
                    self.startOrientierung = self.finger1.direction - self.finger2.direction
                    
                    self.ob = bpy.context.object
                    self.startLocation = self.ob.location.copy()
                    self.startRotation = self.ob.rotation_quaternion.copy()
                    
                    break
                

            '''                    
            ### alter code ###
            leapHands = {hand.id: hand for hand in frame.hands}
            leapHandIDs = leapHands.keys()

            # filter by gesture
            tmp = dict(leapHands)
            for id in tmp.keys():
                if len(tmp[id].hand.pointables) != 1:
                    del leapHands[id]
    
            # add new pointable
            depth = TranslateAndRotateOperator.RANGE
            offset = mathutils.Vector((0.0, 0.0, -depth / 2.0))
            for id in leapHandIDs - blenderPointableIDs:
                # create model
                bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.01, radius2=0.01, depth=depth, end_fill_type='NGON',
                view_align=False, enter_editmode=False,
                location=(0.0, 0.0, 0.0),#location=(0.0, 0.0, -depth / 2.0),
                rotation=(0.0, 0.0, 0.0))
                ob = bpy.context.object
                ob.name = "pointable{}".format(id)
                for vertex in ob.data.vertices:
                    vertex.co += offset
        
                # add object
                self.tracedPointables[id] = ob
            
            # remove vanished pointables
            bpy.ops.object.select_all(action='DESELECT')
            for id in blenderPointableIDs - leapHandIDs:
                self.tracedPointables[id].select = True
                del self.tracedPointables[id]
            bpy.ops.object.delete()
            
            # update visible pointables
            v3d = context.space_data
            rv3d = v3d.region_3d
            offset = mathutils.Vector((0.0, -300.0, 150.0))    # offset in mm between Leap Motion coordinate system and user coordinate system
            selected1 = list()
            for id in self.tracedPointables:
                pointable = leapHands[id]
                ob = self.tracedPointables[id]
                
                ### update model ###
                # update location
                tip_position = mathutils.Vector((pointable.stabilized_tip_position.x, pointable.stabilized_tip_position.y, pointable.stabilized_tip_position.z))
                tip_position += offset
                tip_position *= TranslateAndRotateOperator.SCALE
                tip_position.rotate(rv3d.view_rotation)
                ob.location = rv3d.view_location + tip_position
        
                # update direction
                directionEuler = mathutils.Euler((pointable.direction.pitch, -pointable.direction.yaw, -pointable.hand.palm_normal.roll), 'XYZ')
                directionQuaternion = directionEuler.to_quaternion()
                ob.rotation_mode ='QUATERNION'
                ob.rotation_quaternion = rv3d.view_rotation * directionQuaternion
                
                ### update selection (1) ###
                selected2 = set()
                selected1.append(selected2)
                rayDirection = mathutils.Vector((0.0, 0.0, 1.0))
                rayDirection.rotate(ob.rotation_quaternion)
                rayOrigin = ob.location
                for obj in bpy.data.objects:
                    # filter "own" objects out
                    if obj in self.tracedPointables:
                        continue
                    
                    # test for intersection between cone and object
                    coordinates = obj.bound_box
                    points = list()
                    for i in range(len(coordinates)):
                        x = coordinates[i][0]
                        y = coordinates[i][1]
                        z = coordinates[i][2]
                        points.append(mathutils.Vector((x, y, z)))
                    doesIntersect = False
                    
                    # test for intersection between cone axis and object bounding box
                    for i in range(len(points) - 2):
                        point1 = points[i]
                        point2 = points[i + 1]
                        point3 = points[i + 2]
                        intersection = mathutils.geometry.intersect_ray_tri(point1, point2, point3, rayDirection, rayOrigin)
                        if intersection is not None:
                            distance = (rayOrigin - intersection).length
                            if distance < TranslateAndRotateOperator.RANGE:
                                doesIntersect = True
                                break
                                
                    # test for intersection between cone axis and object polygons
                    if doesIntersect:
                        doesIntersect = False
                        for polygon in obj.data.polygons:
                            point1 = obj.data.vertices[polygon.vertices[0]].co
                            point2 = obj.data.vertices[polygon.vertices[1]].co
                            point3 = obj.data.vertices[polygon.vertices[2]].co
                            intersection = mathutils.geometry.intersect_ray_tri(point1, point2, point3, rayDirection, rayOrigin)
                            if intersection is not None:
                                distance = (rayOrigin - intersection).length
                                if distance < TranslateAndRotateOperator.RANGE:
                                    doesIntersect = True
                                    break

                    # memorize as selected by this pointable
                    if doesIntersect:
                        selected2.add(obj)
                    
            # perform actual selection
            bpy.ops.object.select_all(action='DESELECT')
            if len(selected1) > 0:
                intersection = selected1[0]
                for selectionSet in selected1:
                    intersection &= selectionSet
                for ob in intersection:
                    ob.select = True
            '''
                
        return {'PASS_THROUGH'}

    def execute(self, context):
        self._timer = context.window_manager.event_timer_add(TranslateAndRotateOperator.UPDATE_DELAY, context.window)
        context.window_manager.modal_handler_add(self)
        print("Executing operation. (Entering modal mode.)")
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        # reset object position and rotation
        # TODO

        context.window_manager.event_timer_remove(self._timer)
        print("Operation canceled.")
        
        return {'CANCELLED'}
    
    def coordinateList2VectorList(self, lst):
        count = int(len(lst) / 3)
        vectors = list()
        for i in range(count):
            base = i * 3
            x = float(lst[base])
            y = float(lst[base + 1])
            z = float(lst[base + 2])
            vectors.append(mathutils.Vector((x, y, z)))
        return vectors
    
    def searchGesture(self, frame):
        for hand in frame.hands:
            if len(hand.fingers) == 2:
                # Gesture found. Memorizing hand and fingers.
                self.activeHand = hand
                self.finger1 = hand.fingers[0]
                self.finger2 = hand.fingers[1]
                return True
            
        return False
                
    def updateObject(self):
        # TODO
        pass


def register():
    bpy.utils.register_class(TranslateAndRotateOperator)


def unregister():
    bpy.utils.unregister_class(TranslateAndRotateOperator)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.wm.translate_and_rotate_operator()
