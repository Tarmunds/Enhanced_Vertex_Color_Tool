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
    gradient_only_selected: BoolProperty(
        name="Only Affect Selected",
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