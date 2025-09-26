import bpy
from .Functions import fetch_view_lighting, fetch_view_color_type

def go_to_row(layout, *, scale_y=1.2, align=False):
    row = layout.row(align=align)
    row.scale_y = scale_y
    return row

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

            row = go_to_row(layout)
            row.prop(vct_props, "affect_only_selected", text="Affect Only Selection - Edit Mode Only", toggle=True, icon='RESTRICT_SELECT_OFF' if vct_props.affect_only_selected else 'RESTRICT_SELECT_ON')
            
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
            row = layout.row(align=False)
            row.prop(vct_props, "random_normalize", text="Normalize Random Values", toggle=True)
            row.prop(vct_props, "random_per_connected", text="Per Connected", toggle=True)
            row.prop(vct_props, "random_per_uv_island", text="Per UV Island", toggle=True)
            layout.separator()
            row = layout.row()
            row.scale_y = 1.5
            row.operator("vct.inspect_color", text="Inspect Vertex Color", icon='EYEDROPPER')
            layout.prop(vct_props, "inspect_channel", text="Inspect Channel", expand=True)
            row = go_to_row(layout)
            row.operator("vct.clear_channel", text="Clear to 0", icon='X').value = 0.0
            row.operator("vct.clear_channel", text="Clear to 1", icon='X').value = 1.0
            layout.prop(vct_props, "clear_channel", text="Clear Channel", expand=True)
            layout.separator()

            row = go_to_row(layout)
            row.operator("vct.switch_channel", text="Switch Channels", icon='ARROW_LEFTRIGHT')
            layout.label(text="(Swaps the source and target channels for Gradient and Random fills)")
            row = go_to_row(layout, scale_y=1.0)
            row.prop(vct_props, "switch_source_channel", text="Source Channel", expand=True)
            layout.label(text="(Swaps the source and target channels for Gradient and Random fills)")
            row = go_to_row(layout, scale_y=1.0)
            row.prop(vct_props, "switch_target_channel", text="Target Channel", expand=True)

        #special pannel when inspecting    
        else:
            current_channel = {'R': 'Red', 'G': 'Green', 'B': 'Blue', 'A': 'Alpha'}[vct_props.inspect_channel]
            layout.label(text=f"Inspecting {current_channel} Channel", icon='INFO')
            row = go_to_row(layout)
            row.operator("vct.inspect_color", text="Accept Change", icon='CHECKMARK')
            row.operator("vct.discard_inspect_changes", text="Close Inspector", icon='X')

            row = go_to_row(layout)
            row.prop(vct_props, "affect_only_selected", text="Affect Only Selection - Edit Mode Only", toggle=True, icon='RESTRICT_SELECT_OFF' if vct_props.affect_only_selected else 'RESTRICT_SELECT_ON')

            row = go_to_row(layout, align=True)
            row.operator("vct.inspect_fill_value", text="Fill Value", icon='BRUSH_DATA')
            row.prop(vct_props, "fill_value", text="Fill Value")

            row = go_to_row(layout)
            row.operator("vct.random_fill", text="Random Fill", icon='BRUSH_DATA')
            row = go_to_row(layout, scale_y=1.0)
            row.prop(vct_props, "random_normalize", text="Normalize Random Values", toggle=True)
            row.prop(vct_props, "random_per_connected", text="Per Connected", toggle=True)
            row.prop(vct_props, "random_per_uv_island", text="Per UV Island", toggle=True)

            row = go_to_row(layout)
            row.separator()

            row = go_to_row(layout)
            row.operator("vct.gradient_fill", text="Gradient Fill", icon='BRUSH_DATA')
            row = go_to_row(layout, scale_y=1.0)
            row.prop(vct_props, "gradient_direction", text="Gradient Direction", expand=True)
            row.prop(vct_props, "gradient_WS_direction", text="World Space Direction", toggle=True)

            row.operator("vct.clear_channel", text="Clear to 0", icon='X').value = 0.0
            row.operator("vct.clear_channel", text="Clear to 1", icon='X').value = 1.0
            layout.prop(vct_props, "clear_channel", text="Clear Channel", expand=True)


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