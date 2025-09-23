import bpy
from bpy.props import (BoolProperty, FloatVectorProperty, EnumProperty, PointerProperty, IntProperty, StringProperty)
from bpy.types import PropertyGroup

class VCTProperties(PropertyGroup):
    pass

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