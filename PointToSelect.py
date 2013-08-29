# Addon metadata
bl_info = {
    "name": "Point to select",
    "author": "Kai Puth",
    "version": (0, 1),
    "blender": (2, 65, 0),
    "location": "View3D > Add > Mesh > New Object TODO",
    "description": "Point at an object to make it the active object.",
    "warning": "This addon is experimental.",
    "wiki_url": "",
    "tracker_url": "",
    "category": "System"}


import math
import bpy, mathutils
import Leap


class PointToSelectOperator(bpy.types.Operator):
    """Point at an object to make it the active object."""
    bl_idname = "wm.point_to_select_operator"
    bl_label = "Point to select"

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
            
            leapPointables = {pointable.id: pointable for pointable in frame.pointables}
            leapPointableIDs = leapPointables.keys()
            blenderPointableIDs = self.tracedPointables.keys()

            # filter by gesture
            tmp = dict(leapPointables)
            for id in tmp.keys():
                if len(tmp[id].hand.pointables) != 1:
                    del leapPointables[id]
    
            # add new pointable
            for id in leapPointableIDs - blenderPointableIDs:
                # create model
                depth = PointToSelectOperator.RANGE
                bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.01, radius2=0.01, depth=depth, end_fill_type='NGON',
                view_align=False, enter_editmode=False,
                location=(0.0, 0.0, 0.0),#location=(0.0, 0.0, -depth / 2.0),
                rotation=(0.0, 0.0, 0.0))
                ob = bpy.context.object
                ob.name = "pointable{}".format(id)
        
                # add object
                self.tracedPointables[id] = ob
            
            # remove vanished pointables
            bpy.ops.object.select_all(action='DESELECT')
            for id in blenderPointableIDs - leapPointableIDs:
                self.tracedPointables[id].select = True
                del self.tracedPointables[id]
            bpy.ops.object.delete()
            
            # update visible pointables
            v3d = context.space_data
            rv3d = v3d.region_3d
            offset = mathutils.Vector((0.0, -300.0, 150.0))    # offset in mm between Leap Motion coordinate system and user coordinate system
            selected1 = list()
            for id in self.tracedPointables:
                pointable = leapPointables[id]
                ob = self.tracedPointables[id]
                
                ### update model ###
                # update location
                tip_position = mathutils.Vector((pointable.tip_position.x, pointable.tip_position.y, pointable.tip_position.z))
                '''
                point2 = mathutils.Vector((pointable.tip_position.x, pointable.tip_position.y, pointable.tip_position.z))
                endpoint1 = mathutils.geometry.intersect_line_plane(tip_position, line_b, plane_co, plane_no, no_flip=False)
                '''
                tip_position += offset
                tip_position *= PointToSelectOperator.SCALE
                tip_position.rotate(rv3d.view_rotation)
                ob.location = rv3d.view_location + tip_position
                # Fehler: Mittelpunkt des Objekts wird auf die Position der Fingerspitze gelegt.
        
                # update direction
                #directionEuler = mathutils.Euler((pointable.direction.pitch, -pointable.direction.yaw, pointable.hand.palm_normal.roll), 'XYZ')
                directionEuler = mathutils.Euler((pointable.direction.pitch, -pointable.direction.yaw, -pointable.hand.palm_normal.roll), 'XYZ')
                #directionEuler = mathutils.Euler((pointable.direction.pitch, -pointable.direction.yaw, 0.0), 'XYZ')
                #directionEuler = mathutils.Euler((pointable.direction.pitch, 0.0, 0.0), 'XYZ')  # ok
                #directionEuler = mathutils.Euler((0.0, -pointable.direction.yaw, 0.0), 'XYZ')   # ok
                #directionEuler = mathutils.Euler((0.0, 0.0, pointable.direction.roll), 'XYZ')   # ?
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
                        obj.select = False
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
                            if distance < PointToSelectOperator.RANGE:
                                doesIntersect = True
                                break
                                
                    if doesIntersect:
                        # TODO: perform more accurate intersection test
                        pass

                    # memorize as selected by this pointable
                    if doesIntersect:
                        print("selected: "+obj.name)
                        selected2.add(obj)
                    
            # perform actual selection
            bpy.ops.object.select_all(action='DESELECT')
            if len(selected1) > 0:
                intersection = selected1[0]
                for selectionSet in selected1:
                    intersection &= selectionSet
                for ob in intersection:
                    ob.select = True
                
        return {'PASS_THROUGH'}

    def execute(self, context):
        self._timer = context.window_manager.event_timer_add(PointToSelectOperator.UPDATE_DELAY, context.window)
        context.window_manager.modal_handler_add(self)
        print("Executing operation. (Entering modal mode.)")
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        # remove objects
        bpy.ops.object.select_all(action='DESELECT')
        for id in self.tracedPointables:
            self.tracedPointables[id].select = True
        bpy.ops.object.delete()
        self.tracedPointables.clear()

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


def register():
    bpy.utils.register_class(PointToSelectOperator)


def unregister():
    bpy.utils.unregister_class(PointToSelectOperator)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.wm.point_to_select_operator()
