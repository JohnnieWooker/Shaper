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
    "version" : (1, 0, 1),
    "blender" : (2, 80, 0),
    "location" : "View 3D > Object Mode > Tool Shelf",
    "description" :
    "Transfer attributes. 1. UV map from another mesh with sharing topology. 2. Shape from another mesh through UV map layout ",
    "warning" : "",
    "wiki_url" : "",
    "tracker_url" : "",
    "category" : "Object",
    }

#To do: give ability to pause calculation and return at same point
#To do: better sorting algorithm (faster calculation)

def smoothen(obj,target):
    vg = obj.vertex_groups.new(name="Shaper_Smoothed")
    verts=[]
    bm=bmesh.new()
    bm.from_mesh(obj.data)    
    for v in bm.verts:
        if not v.is_boundary:
            verts.append(v.index)
    vg.add(verts, 1.0, 'ADD')
    for x in range(0,smooth_iterations):
        modifier_smooth = obj.modifiers.new(name="Shaper_Smooth", type='SMOOTH')
        modifier_smooth.factor=0.5
        modifier_smooth.iterations=1
        modifier_smooth.vertex_group="Shaper_Smoothed"
        modifier_shrinkwrap=obj.modifiers.new(name="Shaper_Shrinkwrap", type='SHRINKWRAP')
        modifier_shrinkwrap.target=target
        bpy.ops.object.modifier_apply (modifier='Shaper_Smooth')
        bpy.ops.object.modifier_apply (modifier='Shaper_Shrinkwrap')
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier='Shaper_Smooth')
        bpy.ops.object.modifier_apply(modifier='Shaper_Shrinkwrap')
        bpy.context.view_layer.objects.active = target

def shapetouv():
    selection = bpy.context.selected_objects
    obj_active=bpy.context.view_layer.objects.active
    obj_selected_index=0
    if len(selection)==2:
        for s in selection:
            if not s.name==obj_active.name:
                break
            obj_selected_index=obj_selected_index+1
        obj_selected=selection[obj_selected_index]
        if(len(obj_active.data.uv_layers)==0):
            obj_active.data.uv_layers.new()
        DT_mod = obj_active.modifiers.new(type="DATA_TRANSFER", name="DataTransfer")
        DT_mod.object=obj_selected
        DT_mod.use_loop_data=True
        DT_mod.data_types_loops={'UV'}
        DT_mod.layers_uv_select_dst='INDEX'
        bpy.ops.object.modifier_apply (modifier='DataTransfer') 
        print("passing uv from ",obj_selected.name," to ",obj_active.name)

def modal():
    if self.running == False:
        self.end_run()
        self.cancel(context)
        return {'FINISHED'}

bpy.types.Scene.shaping_progress = bpy.props.StringProperty(
        name="shaping_progress", description="Shaping Progress") 
bpy.types.Scene.polycounter = bpy.props.IntProperty(
        name="polycounter", description="Poly Counter")
bpy.types.Scene.calcstopper=bpy.props.BoolProperty(
        name="calcstopper", description="Calculate Stopper Flag")
bpy.types.Scene.calcpauser=bpy.props.BoolProperty(
        name="calcpauser", description="Calculate Pauser Flag")
bpy.types.Scene.shaper_warning = bpy.props.StringProperty(
        name="shaper_warning", description="Warning message")
bpy.types.Scene.selected_name = bpy.props.StringProperty(
        name="selected_name", description="Selected mesh name")        
bpy.types.Scene.active_name = bpy.props.StringProperty(
        name="active_name", description="Active mesh name")
bpy.types.Scene.removedbls = bpy.props.BoolProperty(
    name="Merge",
    description="Remove doubles after wrapping",
    default = True)
bpy.types.Scene.smooth = bpy.props.BoolProperty(
    name="Smooth",
    description="smooth results",
    default = True)
bpy.types.Scene.goflag = bpy.props.BoolProperty(
    name="goflag",
    description="goflag",
    default = False)
class globallist(bpy.types.PropertyGroup):
    value = bpy.props.IntProperty()
bpy.utils.register_class(globallist)

bpy.types.Scene.useduvlist = bpy.props.CollectionProperty(type=globallist)                           

def calculate(SobD, AobD,start_index):
    Source_indices=[]
    Target_indices=[]
    breaker=False

    Sobdfaces=SobD.polygons
    AobDfaces=AobD.polygons
    counter=0
    polys=len(Sobdfaces)        
    border=start_index+offset        
    if border>len(Sobdfaces):
        border=len(Sobdfaces)            
    for x in range(start_index,border):
        Spoly=Sobdfaces[x]
        counter=counter+1                    
        percent=(start_index+counter)/polys*100  
        #print(percent)
        breaker=False
        bpy.context.scene.shaping_progress=str(percent)          
        for Sloop in Spoly.loop_indices:
            Suv=SobD.uv_layers[0].data[Sloop].uv
            """
            breaker=False
            for coord in bpy.context.scene.useduvlist:
                if SobD.loops[Sloop].vertex_index==coord.value:
                    breaker=True
                    break                
            temp = bpy.context.scene.useduvlist.add()
            temp.value = SobD.loops[Sloop].vertex_index
            """ 
            #print('Vertex[', SobD.loops[Sloop].vertex_index, '].uv = ', Suv)
            smallest=10000
            Ssmallest_index=0
            Tsmallest_index=0
            for Tpoly in AobDfaces: 
                for Tloop in Tpoly.loop_indices:   
                    Tuv=AobD.uv_layers[0].data[Tloop].uv
                    #print(numpy.dot(Suv,Tuv))                        
                    #print(Tuv,' ',(Suv-Tuv).length,' ', smallest)
                    if (Suv-Tuv).length<smallest:
                        smallest=(Suv-Tuv).length
                        #print(smallest)
                        Ssmallest_index=SobD.loops[Sloop].vertex_index
                        Tsmallest_index=AobD.loops[Tloop].vertex_index
            #print(Ssmallest_index,' ',Tsmallest_index,' ',smallest)  
            Source_indices.append(Ssmallest_index) 
            Target_indices.append(Tsmallest_index)             
    for x in range(len(Source_indices)):
        SobD.vertices[Source_indices[x]].co=AobD.vertices[Target_indices[x]].co
    bpy.context.scene.polycounter=bpy.context.scene.polycounter+1


def uvtoshape():
    if bpy.context.scene.polycounter==0:
        #firstpass
        bpy.context.scene.useduvlist.clear()
        if len(bpy.context.selected_objects)==2:

            obj_selected_index=0  
            for s in bpy.context.selected_objects: 
                if not s.name==bpy.context.view_layer.objects.active.name:
                    break
                obj_selected_index=obj_selected_index+1           
            bpy.context.scene.selected_name=bpy.context.selected_objects[obj_selected_index].name
            bpy.context.scene.active_name=bpy.context.view_layer.objects.active.name
            if bpy.context.selected_objects[obj_selected_index].data.uv_layers.active and bpy.context.view_layer.objects.active.data.uv_layers.active:
                bpy.context.scene.goflag=True
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            else:
                print("No UV layout found for one of selected objects") 
                bpy.context.scene.calcpauser=True
                bpy.context.scene.shaper_warning="No UV layout found for one of selected objects"       
        else:
            print("Number of selected objects is different than 2")
            bpy.context.scene.shaper_warning="Number of selected objects is different than 2" 
            bpy.context.scene.calcpauser=True                 

    obj_active=bpy.data.objects[bpy.context.scene.active_name]
    obj_selected=bpy.data.objects[bpy.context.scene.selected_name]
    
    if obj_selected.type=='MESH' and obj_active.type=='MESH' and bpy.context.scene.goflag and bpy.context.view_layer.objects.active.mode=='OBJECT':
        start_index=bpy.context.scene.polycounter*offset
        if start_index>len(obj_selected.data.polygons):
            bpy.context.scene.calcstopper=True
            if bpy.context.scene.removedbls:
                bm = bmesh.new()
                bm.from_mesh(obj_selected.data)
                bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=distance)
                bm.to_mesh(obj_selected.data)
                obj_selected.data.update()
                bm.clear()
            if bpy.context.scene.smooth:
                smoothen(obj_selected,obj_active)
                
                                    
        calculate(obj_selected.data,obj_active.data,start_index) 

class uvtoshapeoperator(bpy.types.Operator):    
    bl_idname="beffio.uvtoshape"
    bl_label="UV -> Shape "
    def modal(self, context, event):    
        if bpy.context.scene.calcstopper==True:
            bpy.context.scene.shaping_progress=""
            self.cancel(context)
            return{'FINISHED'}
            
        if bpy.context.scene.calcpauser==True:
            bpy.context.scene.shaping_progress=""
            self.report({'WARNING'},bpy.context.scene.shaper_warning)
            self.cancel(context)
            return{'CANCELLED'}
        if event.type =='ESC':
            self.cancel(context)
            return{'CANCELLED'}
        if event.type == 'TIMER':
            uvtoshape()
            for area in bpy.context.screen.areas:
                area.tag_redraw()
                
        return {'PASS_THROUGH'}
    def execute(self,context):
        bpy.context.scene.polycounter=0
        bpy.context.scene.calcstopper=False
        bpy.context.scene.calcpauser=False
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)            
        return {'RUNNING_MODAL'}
    
    def cancel(self,context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
    
class shapetouvoperator(bpy.types.Operator):
    bl_idname="beffio.shapetouv"
    bl_label="Shape -> UV"
    def execute(self,context):
        shapetouv()
        return{'FINISHED'}

class Shaper(bpy.types.Panel):
    bl_label = "Shaper"
    bl_idname = "Shaper"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Shaper"
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row = layout.row()
        row = layout.row()
        row = layout.row()
        row.operator("beffio.shapetouv")
        row = layout.row()
        if bpy.context.scene.shaping_progress=="":
            row.operator(uvtoshapeoperator.bl_idname,text="UV -> Shape")
        else:      
            row.operator(uvtoshapeoperator.bl_idname,text="UV -> Shape "+bpy.context.scene.shaping_progress[0:3]+"%")
        row = layout.row()    
        row.prop(context.scene, "removedbls")
        row = layout.row()
        row.prop(context.scene, "smooth")            
classes =(
uvtoshapeoperator,
shapetouvoperator,
Shaper    
)

register, unregister = bpy.utils.register_classes_factory(classes) 

if __name__ == "__main__":
    register()        