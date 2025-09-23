import bpy
from .Functions import *

class VCT_SeeVcolor(bpy.types.Operator):
    bl_idname = "vct.see_vcolor"
    bl_label = "See Vertex Color"
    bl_description = "Toggle Vertex Color Display in Viewport"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        color_type = fetch_view_color_type(context)
        shading = fetch_view_shading(context)
        if color_type == 'VERTEX':
            color_name = 'Material'
            shading.color_type = 'MATERIAL'
        else:
            color_name = 'Vertex Color'
            shading.color_type = 'VERTEX'

        self.report({'INFO'}, f"Viewport Color Type set to {color_name}")
        return {'FINISHED'}

    
class VCT_ShadeFlat(bpy.types.Operator):
    bl_idname = "vct.shade_flat"
    bl_label = "Shade Flat"
    bl_description = "Set shading to Flat for all selected mesh objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        lighting_type = fetch_view_lighting(context)
        shading = fetch_view_shading(context)
        if lighting_type == 'FLAT':
            light_name = 'Default'
            shading.light = 'STUDIO'
        else:
            light_name = 'Flat'
            shading.light = 'FLAT'

        self.report({'INFO'}, f"Viewport Light Type set to {light_name}")
        return {'FINISHED'}
    
_classes = (
    VCT_SeeVcolor,
    VCT_ShadeFlat,
)

def register():
    for cls in _classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
