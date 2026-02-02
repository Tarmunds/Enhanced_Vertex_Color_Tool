import bpy
from bpy.props import (BoolProperty, FloatVectorProperty, EnumProperty, PointerProperty, IntProperty, StringProperty, FloatProperty)
from bpy.types import PropertyGroup

Echannel_source = [
            ('R', "Red", "Red Channel"),
            ('G', "Green", "Green Channel"),
            ('B', "Blue", "Blue Channel"),
            ('A', "Alpha", "Alpha Channel"),
        ]
Echannel_axis = [
            ('X', "X-Axis", "X-Axis"),
            ('Y', "Y-Axis", "Y-Axis"),
            ('Z', "Z-Axis", "Z-Axis"),
        ]
Echannel_resolution = [
            ('256', "Low (256x256)", "Low Resolution 256x256"),
            ('512', "Medium (512x512)", "Medium Resolution 512x512"),
            ('1024', "High (1024x1024)", "High Resolution 1024x1024"),
            ('2048', "Ultra (2048x2048)", "Ultra Resolution 2048x2048"),
            ('4096', "Extreme (4096x4096)", "Extreme Resolution 4096x4096"),
        ]

class VCTProperties(PropertyGroup):
    fill_color: FloatVectorProperty(
        name="Fill Color",
        subtype='COLOR',
        size=4,
        default=(1.0, 1.0, 1.0, 1.0),
        min=0.0, max=1.0
    )
    fill_value: FloatProperty(
        name="Fill Value",
        default=1.0,
        min=0.0,
        max=1.0
    )
    fill_1channel_value: FloatProperty(
        name="Fill Value",
        default=1.0,
        min=0.0,
        max=1.0
    )
    fill_1channel: EnumProperty(
        name="Fill Channel",
        items=Echannel_source,
        default='R'
    )
    affect_only_selected: BoolProperty(
        name="Affect Only Selected",
        default=True
    )
    gradient_channel: EnumProperty(
        name="Gradient Channel",
        items=Echannel_source,
        default='R'
    )
    gradient_direction: EnumProperty(
        name="Gradient Direction",
        items=Echannel_axis,
        default='Z'
    )
    gradient_WS_direction: BoolProperty(
        name="World Space Direction",
        default=False
    )
    gradient_global: BoolProperty(
        name="Global Direction",
        default=False
    )
    gradient_direction_inherit_from_active: BoolProperty(
        name="Inherit From Active",
        default=False
    )
    gradient_invert: BoolProperty(
        name="Invert Gradient",
        default=False
    )
    trace_gradient_active: bpy.props.BoolVectorProperty(
        name="Trace Gradient Active",
        size=2,
        default=(False, False)
    )
    Bcolor_gradient: BoolProperty(
        name="Color Gradient",
        default=False
    )
    gradient_color_start: FloatVectorProperty(
        name="Gradient Color Start",
        subtype='COLOR',
        size=4,
        default=(1.0, 0.0, 0.0, 1.0),
        min=0.0, max=1.0
    )
    gradient_color_end: FloatVectorProperty(
        name="Gradient Color End",
        subtype='COLOR',
        size=4,
        default=(0.0, 0.0, 1.0, 1.0),
        min=0.0, max=1.0
    )
    Bgradient_advanced_options: BoolProperty(
        name="Gradient Advanced Options",
        default=False
    )
    random_channel: EnumProperty(
        name="Random Channel",
        items=Echannel_source,
        default='R'
    )
    random_normalize: BoolProperty(
        name="Normalize Random Values",
        default=False
    )
    random_per_connected: BoolProperty(
        name="Random Per Connected Component",
        default=False
    )
    random_per_uv_island: BoolProperty(
        name="Random Per UV Island",
        default=False
    )
    inspect_enable: BoolProperty(
        name="Inspect Mode",
        default=False
    )
    inspect_channel: EnumProperty(
        name="Inspect Channel",
        items=Echannel_source,
        default='R'
    )
    clear_channel: EnumProperty(
        name="Clear Channel",
        items=Echannel_source,
        default='R'
    )
    switch_source_channel: EnumProperty(
        name="Switch Source Channel",
        items=Echannel_source,
        default='R'
    )
    switch_target_channel: EnumProperty(
        name="Switch Target Channel",
        items=Echannel_source,
        default='G'
    )
    ao_vertex_channel: EnumProperty(
        name="AO Vertex Color Channel",
        items=Echannel_source,
        default='R'
    )
    ao_uv_index: IntProperty(
        name="UV Map Index",
        default=0
    )
    ao_texture_size: EnumProperty(
        name="AO Texture Size",
        items=Echannel_resolution,
        default='1024'
    )
    ao_percent: FloatProperty(
        name="AO Process %",
        default=1.0,
        min=0.0,
        max=100.0,
        subtype='PERCENTAGE',
        precision=3,
    )
    ao_show_percent: BoolProperty(
        name="Show AO Progress %",
        default=False
    )
    Bshow_fill_color: BoolProperty(
        name="Show Fill Color",
        default=False
    )
    Bshow_gradient: BoolProperty(
        name="Show Gradient Options",
        default=False
    )
    Bshow_random: BoolProperty(
        name="Show Random Options",
        default=False
    )
    Bshow_managing: BoolProperty(
        name="Show Managing Options",
        default=False
    )
    Bshow_switch: BoolProperty(
        name="Show Switch Options",
        default=False
    )
    Bshow_ao: BoolProperty(
        name="Show Ambient Occlusion Options",
        default=False
    )
    Bedit_face_mode: BoolProperty(
        name="Edit Mode: Use Face Selection",
        description="When enabled, affects only selected faces in Edit Mode (prevents painting across shared vertices / bleeding).",
        default=False
    )
    Bsrgb: BoolProperty(
        name="sRGB Color Space",
        description="Use sRGB color space for vertex colors (recommended for most cases). Disable for linear workflows.",
        default=False
    )
    Bshow_advanced_options: BoolProperty(
        name="Show Advanced Options",
        default=False
    )


_classes = (
    VCTProperties,
    )

def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.vct_properties = PointerProperty(type=VCTProperties)


def unregister():
    del bpy.types.Scene.vct_properties
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)