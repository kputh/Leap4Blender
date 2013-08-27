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
                depth = 10.0
                bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=1.0, radius2=0.0, depth=depth, end_fill_type='NGON',
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
            for id in self.tracedPointables:
                pointable = leapPointables[id]
                ob = self.tracedPointables[id]
                
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


def register():
    bpy.utils.register_class(PointToSelectOperator)


def unregister():
    bpy.utils.unregister_class(PointToSelectOperator)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.wm.point_to_select_operator()
