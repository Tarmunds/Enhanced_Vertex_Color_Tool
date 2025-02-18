bl_info = {
    "name": "Enhanced Vertex Color Tool",
    "blender": (4, 0, 0),
    "category": "Object",
    "version": (2, 5, 0),
    "author": "Tarmunds",
    "description": "Advanced vertex color tools: fill, gradients, randomization, baked AO in vertex color, bake texture in vertex color, and switch/clear channels.",
    "doc_url": "https://tarmunds.gumroad.com/l/EnhancedVertexColorTool",
    "tracker_url": "https://discord.gg/h39W5s5ZbQ",
    "location": "View3D > Tarmunds Addons > Export Unreal",
}


import bpy, random, bmesh, time, numpy as np
from bpy_extras.io_utils import ImportHelper
from . import VCT_Operator
from . import VCT_Pannel



def register_properties():
    bpy.types.Scene.show_fill_colors = bpy.props.BoolProperty(
        name="Show Fill Colors",
        default=False,
        description="Expand or collapse the Fill Colors section"
    )
    bpy.types.Scene.show_fill_alpha = bpy.props.BoolProperty(
        name="Show Fill Alpha",
        default=False,
        description="Expand or collapse the Fill Alpha section"
    )
    bpy.types.Scene.show_gradient_fill = bpy.props.BoolProperty(
        name="Show Gradient Fill",
        default=False,
        description="Expand or collapse the Gradient Fill section"
    )
    bpy.types.Scene.show_gradient_range = bpy.props.BoolProperty(
        name="Show Gradient Range",
        default=False,
        description="Expand or collapse the Gradient Range section"
    )
    bpy.types.Scene.show_randomize_colors = bpy.props.BoolProperty(
        name="Show Randomize Colors",
        default=False,
        description="Expand or collapse the Randomize Colors section"
    )
    bpy.types.Scene.show_merge_layers = bpy.props.BoolProperty(
        name="Show Merge Layers",
        default=False,
        description="Expand or collapse the Merge Layers section"
    )
    bpy.types.Scene.show_bake_ao = bpy.props.BoolProperty(
        name="Show Bake Ao",
        default=False,
        description="Expand or collapse the Bake Ao section"
    )
    bpy.types.Scene.show_bake_texture = bpy.props.BoolProperty(
        name="Show Bake Ao",
        default=False,
        description="Expand or collapse the Bake Texture section"
    )
    bpy.types.Scene.show_switch_channels = bpy.props.BoolProperty(
        name="Show Switch Channels",
        default=False,
        description="Expand or collapse the Switch Channels section"
    )
    bpy.types.Scene.show_clear_channels = bpy.props.BoolProperty(
        name="Show Clear Channels",
        default=False,
        description="Expand or collapse the Clear Channels section"
    )

def unregister_properties():
    del bpy.types.Scene.show_fill_colors
    del bpy.types.Scene.show_fill_alpha
    del bpy.types.Scene.show_gradient_fill
    del bpy.types.Scene.show_gradient_range
    del bpy.types.Scene.show_randomize_colors
    del bpy.types.Scene.show_merge_layers
    del bpy.types.Scene.show_bake_ao
    del bpy.types.Scene.show_bake_texture
    del bpy.types.Scene.show_switch_channels
    del bpy.types.Scene.show_clear_channels



classes = [
    VCT_Operator.VCT_VertexColorFillOperator,
    VCT_Operator.VCT_VertexColorFillWhiteOperator,
    VCT_Operator.VCT_VertexColorFillBlackOperator,
    VCT_Operator.VCT_VertexColorGradientFillOperator,
    VCT_Operator.VCT_VertexColorRandomizeOperator,
    VCT_Operator.VCT_FillVertexAlphaOperator,
    VCT_Operator.VCT_BakeAOToVertexColor,
    #VCT_Operator.VCT_BakeCurvatureToVertexColor,
    VCT_Operator.VCT_BAKE_OT_import_image,
    VCT_Operator.VCT_BAKE_OT_texture_to_vertex_colors,
    VCT_Operator.VCT_SwitchVertexColorsOperator,
    VCT_Operator.VCT_VertexColorClearChannelOperator,
    VCT_Operator.VCT_FlipFlopShading,
    VCT_Pannel.VCT_VertexColorFillPanel,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.vertex_fill_color = bpy.props.FloatVectorProperty(
        name="Vertex Fill Color",
        subtype='COLOR',
        size=3,
        min=0.0,
        max=1.0,
        default=(1.0, 0.0, 0.0)
    )

    bpy.types.Scene.gradient_direction = bpy.props.EnumProperty(
        name="Gradient Direction",
        items=[
            ('BOTTOM_TOP', "Bottom <> Top - Z axis", "Gradient along Z-axis"),
            ('LEFT_RIGHT', "Left <> Right - X axis", "Gradient along X-axis"),
            ('FRONT_BACK', "Front <> Back - Y axis", "Gradient along Y-axis")
        ],
        default='BOTTOM_TOP'
    )

    bpy.types.Scene.gradient_target_channel = bpy.props.EnumProperty(
        name="Gradient Target Channel",
        items=[
            ('RED', "Red", "Apply gradient to Red channel"),
            ('GREEN', "Green", "Apply gradient to Green channel"),
            ('BLUE', "Blue", "Apply gradient to Blue channel")
        ],
        default='RED'
    )

    bpy.types.Scene.gradient_inverse = bpy.props.BoolProperty(
        name="Inverse Gradient",
        description="Invert the gradient direction",
        default=False
    )

    bpy.types.Scene.gradient_global = bpy.props.BoolProperty(
        name="Global Gradient",
        description="Apply gradient across the entire selection",
        default=False
    )
    bpy.types.Scene.gradient_use_world_space = bpy.props.BoolProperty(
        name="Use World Space",
        description="Use world space coordinates instead of local space for the gradient",
        default=False
    )

    bpy.types.Scene.vertex_fill_alpha = bpy.props.FloatProperty(
        name="Vertex Alpha",
        description="Alpha value to fill the vertex color alpha channel",
        min=0.0,
        max=1.0,
        default=1.0
    )

    bpy.types.Scene.random_target_channel = bpy.props.EnumProperty(
        name="Random Target Channel",
        items=[
            ('RED', "Red", "Randomize Red channel"),
            ('GREEN', "Green", "Randomize Green channel"),
            ('BLUE', "Blue", "Randomize Blue channel")
        ],
        default='RED'
    )

    bpy.types.Scene.random_normalize = bpy.props.BoolProperty(
        name="Normalized Random",
        description="Distribute random values evenly across selected objects",
        default=False
    )
    bpy.types.Scene.bake_ao_vertex_color_channel = bpy.props.EnumProperty(
        name="Channel",
        description="Channel to store the AO bake result",
        items=[
            ("0", "Red", "Red channel"),
            ("1", "Green", "Green channel"),
            ("2", "Blue", "Blue channel"),
            ("3", "Alpha", "Alpha channel")
        ],
        default="0"
    )
    bpy.types.Scene.uv_index = bpy.props.IntProperty(
        name="UV Index",
        description="UV index to use for baking",
        default=0,
        min=0,
    )
    bpy.types.Scene.bake_texture_image = bpy.props.PointerProperty(
        name="Image",
        description="Select or import an image to bake from",
        type=bpy.types.Image,
    )
    bpy.types.Scene.color_channel = bpy.props.EnumProperty(
        name="Color Channel",
        description="Select the color channel to bake to",
        items=[
            ('R', "Red", "Bake to the red channel"),
            ('G', "Green", "Bake to the green channel"),
            ('B', "Blue", "Bake to the blue channel"),
            ('A', "Alpha", "Bake to the alpha channel"),
        ],
        default='R',
    )
    bpy.types.Scene.vc_source_channel = bpy.props.EnumProperty(
        name="Source Channel",
        description="Select the source channel",
        items=[
            ('R', "Red", "Red channel"),
            ('G', "Green", "Green channel"),
            ('B', "Blue", "Blue channel"),
            ('A', "Alpha", "Alpha channel"),
        ],
        default='R',
    )

    bpy.types.Scene.vc_target_channel = bpy.props.EnumProperty(
        name="Target Channel",
        description="Select the target channel",
        items=[
            ('R', "Red", "Red channel"),
            ('G', "Green", "Green channel"),
            ('B', "Blue", "Blue channel"),
            ('A', "Alpha", "Alpha channel"),
        ],
        default='G',
    )
    bpy.types.Scene.ao_vertex_channel = bpy.props.EnumProperty(
        name="Vertex Color Channel",
        description="Choose the channel to store AO",
        items=[
            ("R", "Red", "Store AO in the Red channel"),
            ("G", "Green", "Store AO in the Green channel"),
            ("B", "Blue", "Store AO in the Blue channel"),
            ("A", "Alpha", "Store AO in the Alpha channel"),
        ],
        default="R",
    )

    bpy.types.Scene.ao_uv_index = bpy.props.IntProperty(
        name="UV Index",
        description="Choose the UV map index to use for baking",
        default=0,
        min=0
    )

    bpy.types.Scene.bake_progress = bpy.props.FloatProperty(
        name="Bake Progress",
        description="Progress of AO bake",
        default=0.0,
        min=0.0,
        max=1.0
    )
    
    bpy.types.Scene.vertex_color_clear_channel = bpy.props.EnumProperty(
        name="Channel",
        description="Select the vertex color channel to clear",
        items=[
            ('R', "Red", "Red channel"),
            ('G', "Green", "Green channel"),
            ('B', "Blue", "Blue channel"),
            ('A', "Alpha", "Alpha channel"),
        ],
        default='R',
    )
    bpy.types.Scene.curvature_vertex_channel = bpy.props.EnumProperty(
        name="Curvature Channel",
        description="Choose the vertex color channel for curvature storage",
        items=[
            ("R", "Red", "Store curvature in the Red channel"),
            ("G", "Green", "Store curvature in the Green channel"),
            ("B", "Blue", "Store curvature in the Blue channel")
        ],
        default="R",
    )
    bpy.types.Scene.gradient_start = bpy.props.FloatProperty(
        name="Start Value",
        default=0.0,
        min=0.0,
        max=1.0,
    )
    bpy.types.Scene.gradient_end = bpy.props.FloatProperty(
        name="End Value",
        default=1.0,
        min=0.0,
        max=1.0,
    )
    register_properties()

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.vertex_fill_color
    del bpy.types.Scene.gradient_direction
    del bpy.types.Scene.gradient_target_channel
    del bpy.types.Scene.gradient_inverse
    del bpy.types.Scene.gradient_global
    del bpy.types.Scene.gradient_use_world_space
    del bpy.types.Scene.vertex_fill_alpha
    del bpy.types.Scene.random_target_channel
    del bpy.types.Scene.random_normalize
    del bpy.types.Scene.bake_ao_vertex_color_channel
    del bpy.types.Scene.uv_index
    del bpy.types.Scene.bake_texture_image
    del bpy.types.Scene.color_channel
    del bpy.types.Scene.vc_source_channel
    del bpy.types.Scene.vc_target_channel
    del bpy.types.Scene.ao_vertex_channel
    del bpy.types.Scene.ao_uv_index
    del bpy.types.Scene.bake_progress
    del bpy.types.Scene.vertex_color_clear_channel
    del bpy.types.Scene.gradient_start
    del bpy.types.Scene.gradient_end

    unregister_properties()

if __name__ == "__main__":
    register()
