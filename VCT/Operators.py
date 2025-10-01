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
    
class VCT_FillColor(bpy.types.Operator):
    bl_idname = "vct.fill_color"
    bl_label = "Fill Vertex Color"
    bl_description = "Fill selected mesh objects with the active vertex color"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return fill_vertex_color(context)

    
class VCT_FillBlack(bpy.types.Operator):
    bl_idname = "vct.fill_black"
    bl_label = "Fill Black"
    bl_description = "Fill selected mesh objects with black vertex color"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return fill_vertex_color(context, overide_color=(0.0, 0.0, 0.0, 1.0))

class VCT_FillWhite(bpy.types.Operator):
    bl_idname = "vct.fill_white"
    bl_label = "Fill White"
    bl_description = "Fill selected mesh objects with white vertex color"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return fill_vertex_color(context, overide_color=(1.0, 1.0, 1.0, 1.0))

class VCT_Fill1Channel(bpy.types.Operator):
    bl_idname = "vct.fill_1channel"
    bl_label = "Fill 1 Channel"
    bl_description = "Fill selected mesh objects with the active 1 channel color"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return fill_channel(context)

class VCT_GradientFill(bpy.types.Operator):
    bl_idname = "vct.gradient_fill"
    bl_label = "Gradient Fill"
    bl_description = "Fill selected mesh objects with a gradient based on the chosen channel"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return fill_gradient(context)

class VCT_RandomFill(bpy.types.Operator):
    bl_idname = "vct.random_fill"
    bl_label = "Random Fill"
    bl_description = "Fill selected mesh objects with random vertex color"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return fill_random(context)

class VCT_ChannelInspect(bpy.types.Operator):
    bl_idname = "vct.inspect_color"
    bl_label = "Inspect Vertex Color"
    bl_description = "Inspect the vertex color of selected mesh objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return inspect_color_channel(context)

class VCT_DiscardInspectChanges(bpy.types.Operator):
    bl_idname = "vct.discard_inspect_changes"
    bl_label = "Discard Inspect Changes"
    bl_description = "Discard changes made during inspect mode and revert to original vertex colors"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        remove_inspector(context, keep_data=False)
        return {'FINISHED'}

class VCT_InspectFillValue(bpy.types.Operator):
    bl_idname = "vct.inspect_fill_value"
    bl_label = "Fill Value"
    bl_description = "Fill selected mesh objects with a specific value on the inspect channel"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        value = (context.scene.vct_properties.fill_value,)*4
        return fill_vertex_color(context, overide_color=value)

class VCT_ClearChannel(bpy.types.Operator):
    bl_idname = "vct.clear_channel"
    bl_label = "Clear Channel"
    bl_description = "Clear the selected channel to zero in the vertex colors of selected mesh objects"
    bl_options = {'REGISTER', 'UNDO'}

    value: bpy.props.FloatProperty(name="Value", default=0.0)

    def execute(self, context):
        return clear_channel(context, value=self.value)

class VCT_SwitchChannel(bpy.types.Operator):
    bl_idname = "vct.switch_channel"
    bl_label = "Switch Channel"
    bl_description = "Switch the source channel to the target channel in the vertex colors of selected mesh objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return switch_channel(context)

class VCT_AOToVertexColor(bpy.types.Operator):
    bl_idname = "vct.ao_to_vertex_color"
    bl_label = "Bake AO to Vertex Color"
    bl_description = "Bake Ambient Occlusion to the selected vertex color channel of selected mesh objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def execute(self, context):
        return bake_ao_to_vertex_color(context)
    
class VCT_InvertChannel(bpy.types.Operator):
    bl_idname = "vct.invert_channel"
    bl_label = "Invert Channel"
    bl_description = "Invert the values of the selected channel in the vertex colors of selected mesh objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return invert_vertex_colors(context)

_classes = (
    VCT_SeeVcolor,
    VCT_ShadeFlat,
    VCT_FillColor,
    VCT_FillBlack,
    VCT_FillWhite,
    VCT_GradientFill,
    VCT_RandomFill,
    VCT_ChannelInspect,
    VCT_DiscardInspectChanges,
    VCT_InspectFillValue,
    VCT_ClearChannel,
    VCT_SwitchChannel,
    VCT_Fill1Channel,
    VCT_AOToVertexColor,
    VCT_InvertChannel,
)

def register():
    for cls in _classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
