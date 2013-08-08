import bpy
from bpy.props import IntProperty, FloatProperty
 
#import Leap Shiznit
import Leap, mathutils
 
#sneak a Leap
controller = Leap.Controller()
 
#experiments some i guess
doLeap = True
fingersPresent = 0
 
#Larmache's Coefficient
coef = 0.04 #def 0.03
 
#define the active object or something
obj = bpy.context.scene.objects.active
 
class ModalTimerOperator(bpy.types.Operator):
    """Operator which runs its self from a timer"""
    bl_idname = "wm.modal_timer_operator"
    bl_label = "Leap Color UI "
 
    _timer = None
 
    def modal(self, context, event):
       
        #SneakMoreLeap
        frame = controller.frame()
        hand = frame.hands[0]
       
        #Create Hand Counter
        numberOfHands = (len(frame.hands))
        print (len(frame.hands))
        numberOfHands = 1
                       
        #gimme more data
        randX = hand.palm_position.x * coef
        randY = -hand.palm_position.z * coef
        randZ = hand.palm_position.y * coef
   
        #print (randX)
        #print (randY)
        #print (randZ)  
       
        #Finger Counters
        i = len(frame.fingers)
        #print (i)
        doLeap = True
                         
        # Get leap orientation
        direction = mathutils.Vector((-hand.direction.x, hand.direction.z, -hand.direction.y))
        normal = mathutils.Vector((hand.palm_normal.x, -hand.palm_normal.z, hand.palm_normal.y))
       
        if numberOfHands == 0:
        #if event.type == 'ESC':
            return self.cancel(context)
       
        if event.type == 'RETKEY':
            return {'FINISHED'}
 
        if event.type == 'TIMER':
            # change theme color, silly!
            color = context.user_preferences.themes[0].view_3d.space.gradients.high_gradient
            color.s = i
            color.h += 0.01
            i = len(frame.fingers)
            obj.location.x = randX #* 0.01
            obj.location.y = randY #* 0.01
            obj.location.z = randZ #* 0.01
           
            #if numberOfHands == 0:
            #    return {'FINISHED'}
                       
        return {'PASS_THROUGH'}
           
    def execute(self, context):
        self._timer = context.window_manager.event_timer_add(0.1, context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
 
    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        return {'CANCELLED'}
 
 
def register():
    bpy.utils.register_class(ModalTimerOperator)
 
 
def unregister():
    bpy.utils.unregister_class(ModalTimerOperator)
 
 
if __name__ == "__main__":
    register()
 
    # test call
    bpy.ops.wm.modal_timer_operator()