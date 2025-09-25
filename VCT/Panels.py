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
        row = layout.row()
        row.scale_y = 1.5
        if fetch_view_lighting(context) == 'FLAT':
            row.operator("vct.shade_flat", text="Switch to Studio Lighting", icon='SHADING_SOLID', depress=True)
        else:
            row.operator("vct.shade_flat", text="Switch to Flat Lighting", icon='SHADING_RENDERED', depress=False)
        layout.separator()
        # Toggle buttons for lighting and color type

        row = layout.row()
        row.scale_y = 1.5
        if fetch_view_color_type(context) == 'VERTEX':
            row.operator("vct.see_vcolor", text="Switch to Material Color", icon='HIDE_OFF', depress=True)
        else:
            row.operator("vct.see_vcolor", text="Switch to Vertex Color", icon='HIDE_ON', depress=False)

        layout.separator()

        #standard pannel when not inspecting
        if not context.scene.vct_properties.inspect_enable:

            row = layout.row()
            row.scale_y = 1.5
            row.operator("vct.fill_color", text="Fill Vertex Color", icon='BRUSH_DATA')
            layout.prop(vct_props, "fill_color", text="Fill Color")
            layout.prop(vct_props, "affect_only_selected", text="Affect Only Selected")
            row = layout.row()
            row.scale_y = 1.5
            row.operator("vct.fill_black", text="Fill Black", icon='X')
            row.operator("vct.fill_white", text="Fill White", icon='CHECKMARK')
            row = layout.row()
            row.scale_y = 1.5
            row.operator("vct.gradient_fill", text="Gradient Fill", icon='BRUSH_DATA')
            layout.prop(vct_props, "gradient_channel", text="Gradient Channel", expand=True)
            row = layout.row(align=False)
            row.prop(vct_props, "gradient_direction", text="Gradient Direction", expand=True)
            row.prop(vct_props, "gradient_WS_direction", text="World Space Direction", toggle=True)
            row = layout.row()
            row.scale_y = 1.5
            row.operator("vct.random_fill", text="Random Fill", icon='BRUSH_DATA')
            layout.prop(vct_props, "random_channel", text="Random Channel", expand=True)
            layout.prop(vct_props, "random_normalize", text="Normalize Random Values", toggle=True)
            row = layout.row()
            row.separator()
            row.scale_y = 1.5
            row.operator("vct.inspect_color", text="Inspect Vertex Color", icon='EYEDROPPER')
            layout.prop(vct_props, "inspect_channel", text="Inspect Channel", expand=True)

        #special pannel when inspecting    
        else:
            current_channel = {'R': 'Red', 'G': 'Green', 'B': 'Blue', 'A': 'Alpha'}[vct_props.inspect_channel]
            layout.label(text=f"Inspecting {current_channel} Channel", icon='INFO')
            row = layout.row()
            row.scale_y = 1.5
            row.operator("vct.inspect_color", text="Accept Change", icon='CHECKMARK')
            row.operator("vct.discard_inspect_changes", text="Close Inspector", icon='X')
            layout.prop(vct_props, "affect_only_selected", text="Affect Only Selected")
            layout.operator("vct.fill_value", text="Fill Value", icon='BRUSH_DATA')
            layout.prop(vct_props, "fill_value", text="Fill Value")


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