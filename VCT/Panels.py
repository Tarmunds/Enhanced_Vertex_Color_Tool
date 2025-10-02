import bpy
from .Functions import fetch_view_lighting, fetch_view_color_type

def go_to_row(layout, *, scale_y=1.2, align=False):
    row = layout.row(align=align)
    row.scale_y = scale_y
    return row

def go_to_box_row(layout, scale_y=1.2, align=False):
    box = layout.box()
    row = box.row(align=align)
    row.scale_y = scale_y
    return row, box

def dropdown_menu(layout, data, prop_name: str, text: str, section_icon=None):
    expanded = getattr(data, prop_name)
    row, box = go_to_box_row(layout)
    row.prop(data, prop_name,
             text=text,
             icon='TRIA_DOWN' if expanded else 'TRIA_RIGHT',
             emboss=False,
             toggle=True)
    if section_icon:
        r = row.row(align=True)
        r.enabled = True if expanded else False
        r.label(icon=section_icon)
    return box if expanded else None

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


        # Shading and Color Type toggles
        row = layout.row()
        row.scale_y = 1.5
        if fetch_view_color_type(context) == 'VERTEX':
            row.operator("vct.see_vcolor", text="See Vertex Color", icon='HIDE_OFF', depress=True)
        else:
            row.operator("vct.see_vcolor", text="See Vertex Color", icon='HIDE_ON', depress=False)

        if fetch_view_lighting(context) == 'FLAT':
            row.operator("vct.shade_flat", text="Flat Lighting", icon='SHADING_SOLID', depress=True)
        else:
            row.operator("vct.shade_flat", text="Studio Lighting", icon='SHADING_RENDERED', depress=False)

        # Affect Only Selection toggle
        row = go_to_row(layout)
        row.prop(vct_props, "affect_only_selected", text="Affect Only Selection - Edit Mode Only", toggle=True, icon='RESTRICT_SELECT_OFF' if vct_props.affect_only_selected else 'RESTRICT_SELECT_ON')

        layout.separator()

        # Inspect Color Section
        if not context.scene.vct_properties.inspect_enable:
            row = go_to_row(layout)
            box = row.box()
            box.operator("vct.inspect_color", text="Inspect Vertex Color", icon='EYEDROPPER')
            box = go_to_row(box, scale_y=1.0)
            box.prop(vct_props, "inspect_channel", text="Inspect Channel", expand=True)
        else:
            box = layout.box()
            row = go_to_row(box, scale_y=1.5)
            row.operator("vct.inspect_color", text="Accept Change", icon='CHECKMARK')
            row.operator("vct.discard_inspect_changes", text="Close Inspector", icon='X')
            row = go_to_row(box, scale_y=1.0)
            current_channel = {'R': 'Red', 'G': 'Green', 'B': 'Blue', 'A': 'Alpha'}[vct_props.inspect_channel]
            row.label(text=f"Inspecting {current_channel} Channel", icon='EYEDROPPER')

        #standard pannel when not inspecting
        if not context.scene.vct_properties.inspect_enable:

            box = dropdown_menu(layout, vct_props, "Bshow_fill_color", "Fill Color", section_icon='BRUSH_DATA')
            if box:
                row = go_to_row(box, scale_y=1.5)
                row.operator("vct.fill_color", text="Fill Vertex Color", icon='BRUSH_DATA')
                row.prop(vct_props, "fill_color", text="")
                row = go_to_row(box, scale_y=1.0)
                row.operator("vct.fill_black", text="Fill Black", icon='KEY_EMPTY1')
                row.operator("vct.fill_white", text="Fill White", icon='RADIOBUT_ON')
                row = go_to_row(box, align=True)
                row.label(text="Or Fill 1 Channel:")
                row = go_to_row(box, align=True)
                current_channel = {'R': 'Red', 'G': 'Green', 'B': 'Blue', 'A': 'Alpha'}[vct_props.fill_1channel]
                row.operator("vct.fill_1channel", text=f"Fill {current_channel} Channel", icon='PRESET')
                row.prop(vct_props, "fill_1channel_value", text="Fill Value")
                row = go_to_row(box, scale_y=1.0)
                row.prop(vct_props, "fill_1channel", text="Fill Channel", expand=True)

            box = dropdown_menu(layout, vct_props, "Bshow_gradient", "Gradient Fill", section_icon='TRANSFORM_ORIGINS')
            if box:
                row = go_to_row(box)
                row.operator("vct.gradient_fill", text="Gradient Fill", icon='BRUSH_DATA')
                row = go_to_row(box, align=True)
                row.operator("vct.trace_gradient", text="Trace Linear Gradient", icon='CURVE_PATH').Bcircle = False
                row.operator("vct.trace_gradient", text="Trace Radial Gradient", icon='CURVE_NCIRCLE').Bcircle = True
                row = go_to_row(box)
                row.prop(vct_props, "gradient_channel", text="Gradient Channel", expand=True)
                row = go_to_row(box, scale_y=1.0)
                row.prop(vct_props, "gradient_direction", text="Gradient Direction", expand=True)
                row = go_to_row(box, scale_y=1.0)
                row.prop(vct_props, "gradient_global", text="Global Gradient", toggle=True)
                row.prop(vct_props, "gradient_WS_direction", text="World Space Direction", toggle=True)
                row = go_to_row(box, scale_y=1.0)
                sub = row.row()
                sub.enabled =  not vct_props.gradient_WS_direction
                sub.prop(vct_props, "gradient_direction_inherit_from_active", text="Inherit From Active", toggle=True)
                row.prop(vct_props, "gradient_invert", text="Invert Gradient", toggle=True)


            box = dropdown_menu(layout, vct_props, "Bshow_random", "Random Fill", section_icon='POINTCLOUD_POINT')
            if box:
                row = go_to_row(box)
                row.operator("vct.random_fill", text="Random Fill", icon='BRUSH_DATA')
                row = go_to_row(box)
                row.prop(vct_props, "random_channel", text="Random Channel", expand=True)
                row = go_to_row(box, scale_y=1.0)
                row.prop(vct_props, "random_normalize", text="Normalize Random Values", toggle=True)
                row.prop(vct_props, "random_per_connected", text="Per Connected", toggle=True)
                row.prop(vct_props, "random_per_uv_island", text="Per UV Island", toggle=True)
            
            box = dropdown_menu(layout, vct_props, "Bshow_managing", "Managing Channel", section_icon='SETTINGS')
            if box:
                row = go_to_row(box, scale_y=1.0)
                row.prop(vct_props, "clear_channel", text="Clear Channel", expand=True)
                row = go_to_row(box)
                row.operator("vct.clear_channel", text="Clear to 0", icon='KEY_BACKSPACE').value = 0.0
                row.operator("vct.clear_channel", text="Clear to 1", icon='KEY_BACKSPACE_FILLED').value = 1.0
                row = go_to_row(box)
                row.operator("vct.invert_channel", text="Invert Channel", icon='NODE_COMPOSITING')
        

            box = dropdown_menu(layout, vct_props, "Bshow_switch", "Switch Channels", section_icon='ARROW_LEFTRIGHT')
            if box:
                row = go_to_row(box)
                row.operator("vct.switch_channel", text="Switch Channels", icon='ARROW_LEFTRIGHT')
                row = go_to_row(box, scale_y=1.0)
                row.prop(vct_props, "switch_source_channel", text="Source Channel", expand=True)
                row = go_to_row(box, scale_y=1.0)
                row.prop(vct_props, "switch_target_channel", text="Target Channel", expand=True)
            
            box = dropdown_menu(layout, vct_props, "Bshow_ao", "Ambient Occlusion to Vertex Color", section_icon='LIGHT_SUN')
            if box:
                row = go_to_row(box)
                row.operator("vct.ao_to_vertex_color", text="Bake AO to Vertex Color", icon='LIGHT_SUN')
                row = go_to_row(box, scale_y=1.0)
                row.prop(vct_props, "ao_vertex_channel", text="AO Channel", expand=True)
                row = go_to_row(box, scale_y=1.0)
                row.prop(vct_props, "ao_uv_index", text="UV Map")
                row = go_to_row(box, scale_y=1.0)
                row.prop(vct_props, "ao_texture_size", text="Texture Size")
                if vct_props.ao_show_percent:
                    row = go_to_row(box, scale_y=1.0)
                    row.prop(vct_props, "ao_percent", text="Progress")

        #special pannel when inspecting    
        else:
            layout.separator()
            # Inspect Fill Value and Clear Channel buttons
            row = go_to_row(layout, align=True)
            row.operator("vct.inspect_fill_value", text="Fill Value", icon='BRUSH_DATA')
            row.prop(vct_props, "fill_value", text="Fill Value")
            row = go_to_row(layout)
            row.operator("vct.clear_channel", text="Clear to 0", icon='KEY_BACKSPACE').value = 0.0
            row.operator("vct.clear_channel", text="Clear to 1", icon='KEY_BACKSPACE_FILLED').value = 1.0
            

            layout.separator()
            # Random Fill and Gradient Fill buttons and options
            row = go_to_row(layout)
            row.operator("vct.random_fill", text="Random Fill", icon='BRUSH_DATA')
            row = go_to_row(layout, scale_y=1.0)
            row.prop(vct_props, "random_normalize", text="Normalize Random Values", toggle=True)
            row.prop(vct_props, "random_per_connected", text="Per Connected", toggle=True)
            row.prop(vct_props, "random_per_uv_island", text="Per UV Island", toggle=True)

            layout.separator()
            # Gradient Fill buttons and options
            row = go_to_row(layout)
            row.operator("vct.gradient_fill", text="Gradient Fill", icon='BRUSH_DATA')
            row = go_to_row(layout, scale_y=1.0)
            row.prop(vct_props, "gradient_direction", text="Gradient Direction", expand=True)
            row.prop(vct_props, "gradient_WS_direction", text="World Space Direction", toggle=True)
            



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