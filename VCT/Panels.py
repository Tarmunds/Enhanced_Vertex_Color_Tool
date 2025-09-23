import bpy
from .Functions import fetch_view_lighting, fetch_view_color_type

class VCT_Panel(bpy.types.Panel):
    bl_label = "Enhanced Vertex Color Tool"
    bl_idname = "VCT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tarmunds Addons'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        vct_props = scene.vct_properties 
        layout.label(text="Vertex Color Tool Panel")

        # Toggle buttons for lighting and color type
        row = layout.row()
        row.scale_y = 1.5
        if fetch_view_lighting(context) == 'FLAT':
            row.operator("vct.shade_flat", text="Switch to Studio Lighting", icon='SHADING_SOLID', depress=True)
        else:
            row.operator("vct.shade_flat", text="Switch to Flat Lighting", icon='SHADING_RENDERED', depress=False)
        row = layout.row()
        row.scale_y = 1.5
        if fetch_view_color_type(context) == 'VERTEX':
            row.operator("vct.see_vcolor", text="Switch to Material Color", icon='HIDE_OFF', depress=True)
        else:
            row.operator("vct.see_vcolor", text="Switch to Vertex Color", icon='HIDE_ON', depress=False)

    def draw_header_preset(self, context):
        layout = self.layout
        layout.label(icon='BRUSH_DATA')
        layout.label(text="")

_classes = (
    VCT_Panel,
    )

def register():
    for cls in _classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)