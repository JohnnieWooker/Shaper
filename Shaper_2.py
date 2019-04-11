import bpy
import numpy
import bmesh
from mathutils import Vector
wm = bpy.context.window_manager

offset=1
distance = 0.0
angle_limit=120
angle_limit_rads=angle_limit*3.14/180 
smooth_iterations=10

bl_info = {
    "name" : "Shaper",
    "author" : "Lukasz Hoffmann <https://www.artstation.com/artist/lukaszhoffmann>",
    "version" : (1, 0, 2),
    "blender" : (2, 7, 9),
    "location" : "View 3D > Object Mode > Tool Shelf",
    "description" :
    "Transfer attributes. 1. UV map from another mesh with sharing topology. 2. Shape from another mesh through UV map layout ",
    "warning" : "",
    "wiki_url" : "",
    "tracker_url" : "",
    "category" : "Object",
    }


def shapebyuv():
    scn = bpy.context.scene.name
    LPOBJ=bpy.data.scenes[scn].LPObject
    HPOBJF=bpy.data.scenes[scn].HPFObject
    HPOBJS=bpy.data.scenes[scn].HPObject
    LPOBJ.hide=False
    HPOBJF.hide=False
    HPOBJS.hide=False
    bpy.ops.object.select_all(action='DESELECT')
    HPOBJS.select=True
    bpy.context.scene.objects.active=HPOBJF
    try:
        bpy.ops.object.shape_key_remove(all=True)
    except:
        print("no shape keys")    
    bpy.ops.object.join_shapes()
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.scene.objects.active=LPOBJ
    try:
        bpy.ops.object.modifier_remove(modifier="SURFACE_DEFORM")
    except:
        print("no surf def mod")
    mod_def=LPOBJ.modifiers.new("SURFACE_DEFORM", 'SURFACE_DEFORM') 
    mod_def.target=HPOBJF
    mod_def.falloff = 16
    bpy.ops.object.surfacedeform_bind(modifier="SURFACE_DEFORM")
    bpy.data.shape_keys["Key"].key_blocks[HPOBJS.name].value = 1
    HPOBJS.hide=True
    HPOBJF.hide=True
    

    
class shapetouvoperator(bpy.types.Operator):
    bl_idname="beffio.shapebyuv"
    bl_label="Shape -> UV"
    def execute(self,context):
        scn = bpy.context.scene.name
        if (not bpy.data.scenes[scn].LPObject==None and not bpy.data.scenes[scn].HPFObject==None and not bpy.data.scenes[scn].HPObject==None):
            shapebyuv()
        return{'FINISHED'}
                            
def register():  
    bpy.utils.register_class(shapetouvoperator)     
    
def unregister():
    bpy.utils.unregister_class(shapetouvoperator)  

register()

class Shaper(bpy.types.Panel):
    bl_label = "Shaper"
    bl_idname = "Shaper"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Shaper"
    def draw(self, context):
        layout = self.layout
        scene = context.scene 
        row = layout.row()
        row = layout.row()
        row = layout.row()
        row = layout.label("Low poly")
        layout.prop_search(scene, "LPObject", scene, "objects",text="")
        row = layout.label("High poly flat")
        layout.prop_search(scene, "HPFObject", scene, "objects",text="")
        row = layout.label("High poly")
        layout.prop_search(scene, "HPObject", scene, "objects",text="")
        row = layout.row()
        row.operator("beffio.shapebyuv")
        row = layout.row()  

def register():
    bpy.types.Scene.LPObject = bpy.props.PointerProperty(type=bpy.types.Object, name="")
    bpy.types.Scene.HPFObject = bpy.props.PointerProperty(type=bpy.types.Object,name="")
    bpy.types.Scene.HPObject = bpy.props.PointerProperty(type=bpy.types.Object, name="")
    bpy.utils.register_class(Shaper)
    

def unregister():
    bpy.utils.unregister_class(Shaper)

if __name__ == "__main__":
    register()        