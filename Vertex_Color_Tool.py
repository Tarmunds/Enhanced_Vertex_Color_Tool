bl_info = {
    "name": "Enhanced Vertex Color Tool",
    "blender": (4, 0, 0),
    "category": "Object",
    "version": (2, 5, 0),
    "author": "Tarmunds",
    "description": "Advanced vertex color tools: fill, gradients, randomization, layer merging, baked AO in vertex color, bake texture in vertex color, and switch channels.",
    "doc_url": "https://tarmunds.gumroad.com/l/UnrealExporter",
    "tracker_url": "https://discord.gg/h39W5s5ZbQ",
    "location": "View3D > Tarmunds Addons > Export Unreal",
}


import bpy
import random
import bmesh
from bpy_extras.io_utils import ImportHelper

class VertexColorFillOperator(bpy.types.Operator):
    bl_idname = "object.vertex_color_fill"
    bl_label = "Fill Vertex Color"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        color = context.scene.vertex_fill_color
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                self.fill_vertex_color(obj, color)
        return {'FINISHED'}

    def fill_vertex_color(self, obj, color):
        if not obj.data.vertex_colors:
            obj.data.vertex_colors.new()

        vcol_layer = obj.data.vertex_colors.active
        r, g, b = color[:3]

        for poly in obj.data.polygons:
            for loop_idx in poly.loop_indices:
                vcol_layer.data[loop_idx].color = (r, g, b, 1.0)

class VertexColorFillWhiteOperator(bpy.types.Operator):
    bl_idname = "object.vertex_color_fill_white"
    bl_label = "Fill White"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        color = (1.0, 1.0, 1.0)
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                VertexColorFillOperator.fill_vertex_color(self, obj, color)
        return {'FINISHED'}

class VertexColorFillBlackOperator(bpy.types.Operator):
    bl_idname = "object.vertex_color_fill_black"
    bl_label = "Fill Black"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        color = (0.0, 0.0, 0.0)
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                VertexColorFillOperator.fill_vertex_color(self, obj, color)
        return {'FINISHED'}

class VertexColorGradientFillOperator(bpy.types.Operator):
    bl_idname = "object.vertex_color_gradient_fill"
    bl_label = "Apply Gradient to Vertex Color"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        direction = context.scene.gradient_direction
        target_channel = context.scene.gradient_target_channel
        inverse_gradient = context.scene.gradient_inverse
        global_gradient = context.scene.gradient_global

        if global_gradient:
            self.apply_global_gradient(context.selected_objects, direction, target_channel, inverse_gradient)
        else:
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    self.apply_gradient(obj, direction, target_channel, inverse_gradient)
        return {'FINISHED'}

    def apply_gradient(self, obj, direction, target_channel, inverse_gradient):
        if not obj.data.vertex_colors:
            obj.data.vertex_colors.new()

        vcol_layer = obj.data.vertex_colors.active

        min_val, max_val = self.get_bounds(obj, direction)
        if max_val == min_val:
            max_val = min_val + 1e-6  # Prevent division by zero
        for poly in obj.data.polygons:
            for loop_idx in poly.loop_indices:
                coord = self.get_coordinate(obj.data.loops[loop_idx].vertex_index, obj, direction)
                gradient_value = (coord - min_val) / (max_val - min_val)
                if inverse_gradient:
                    gradient_value = 1.0 - gradient_value
                r, g, b, a = vcol_layer.data[loop_idx].color
                if target_channel == 'RED':
                    vcol_layer.data[loop_idx].color = (gradient_value, g, b, a)
                elif target_channel == 'GREEN':
                    vcol_layer.data[loop_idx].color = (r, gradient_value, b, a)
                elif target_channel == 'BLUE':
                    vcol_layer.data[loop_idx].color = (r, g, gradient_value, a)

    def apply_global_gradient(self, objects, direction, target_channel, inverse_gradient):
        all_coords = []
        for obj in objects:
            if obj.type == 'MESH':
                # Convert local coordinates to global coordinates
                all_coords.extend([self.get_global_coordinate(v.index, obj, direction) for v in obj.data.vertices])

        if not all_coords:
            return

        min_val, max_val = min(all_coords), max(all_coords)
        if max_val == min_val:
            max_val = min_val + 1e-6  # Prevent division by zero

        for obj in objects:
            if obj.type == 'MESH':
                vcol_layer = obj.data.vertex_colors.active
                if not vcol_layer:
                    vcol_layer = obj.data.vertex_colors.new()

                for poly in obj.data.polygons:
                    for loop_idx in poly.loop_indices:
                        coord = self.get_global_coordinate(obj.data.loops[loop_idx].vertex_index, obj, direction)
                        gradient_value = (coord - min_val) / (max_val - min_val)
                        if inverse_gradient:
                            gradient_value = 1.0 - gradient_value
                        r, g, b, a = vcol_layer.data[loop_idx].color
                        if target_channel == 'RED':
                            vcol_layer.data[loop_idx].color = (gradient_value, g, b, a)
                        elif target_channel == 'GREEN':
                            vcol_layer.data[loop_idx].color = (r, gradient_value, b, a)
                        elif target_channel == 'BLUE':
                            vcol_layer.data[loop_idx].color = (r, g, gradient_value, a)

    def get_bounds(self, obj, direction):
        coords = [self.get_coordinate(v.index, obj, direction) for v in obj.data.vertices]
        return min(coords), max(coords)

    def get_coordinate(self, vertex_idx, obj, direction):
        coord = obj.data.vertices[vertex_idx].co
        if direction == 'BOTTOM_TOP':
            return coord.z
        elif direction == 'LEFT_RIGHT':
            return coord.x
        elif direction == 'FRONT_BACK':
            return coord.y

    def get_global_coordinate(self, vertex_idx, obj, direction):
        # Convert local coordinate to global coordinate
        coord = obj.matrix_world @ obj.data.vertices[vertex_idx].co
        if direction == 'BOTTOM_TOP':
            return coord.z
        elif direction == 'LEFT_RIGHT':
            return coord.x
        elif direction == 'FRONT_BACK':
            return coord.y

        
class VertexColorRandomizeOperator(bpy.types.Operator):
    bl_idname = "object.vertex_color_randomize"
    bl_label = "Randomize Vertex Colors"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target_channel = context.scene.random_target_channel
        normalize = context.scene.random_normalize
        objects = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if normalize and objects:
            step = 1.0 / max(1, len(objects) - 1)
            for i, obj in enumerate(sorted(objects, key=lambda o: o.name)):  # Sort for consistency
                normalized_value = i * step
                self.randomize_color(obj, target_channel, value=normalized_value)
        else:
            for obj in objects:
                self.randomize_color(obj, target_channel)

        return {'FINISHED'}

    def randomize_color(self, obj, target_channel, value=None):
        if not obj.data.vertex_colors:
            obj.data.vertex_colors.new()

        vcol_layer = obj.data.vertex_colors.active
        rand_value = value if value is not None else random.random()

        for poly in obj.data.polygons:
            for loop_idx in poly.loop_indices:
                r, g, b, a = vcol_layer.data[loop_idx].color
                if target_channel == 'RED':
                    vcol_layer.data[loop_idx].color = (rand_value, g, b, a)
                elif target_channel == 'GREEN':
                    vcol_layer.data[loop_idx].color = (r, rand_value, b, a)
                elif target_channel == 'BLUE':
                    vcol_layer.data[loop_idx].color = (r, g, rand_value, a)

class FillVertexAlphaOperator(bpy.types.Operator):
    bl_idname = "object.fill_vertex_alpha"
    bl_label = "Fill Vertex Alpha"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        alpha_value = context.scene.vertex_fill_alpha
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                self.fill_vertex_alpha(obj, alpha_value)
        return {'FINISHED'}

    def fill_vertex_alpha(self, obj, alpha_value):
        if not obj.data.vertex_colors:
            obj.data.vertex_colors.new()

        vcol_layer = obj.data.vertex_colors.active

        for poly in obj.data.polygons:
            for loop_idx in poly.loop_indices:
                r, g, b, _ = vcol_layer.data[loop_idx].color
                vcol_layer.data[loop_idx].color = (r, g, b, alpha_value)

class MergeVertexColorLayersOperator(bpy.types.Operator):
    bl_idname = "object.merge_vertex_color_layers"
    bl_label = "Merge Vertex Color Layers"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        source_layer_name = context.scene.source_vertex_color_layer
        target_channel = context.scene.ao_target_channel

        for obj in context.selected_objects:
            if obj.type == 'MESH':
                self.merge_vertex_color_layers(obj, source_layer_name, target_channel)

        return {'FINISHED'}

    def merge_vertex_color_layers(self, obj, source_layer_name, target_channel):
        if source_layer_name not in obj.data.vertex_colors:
            self.report({'ERROR'}, f"Source vertex color layer '{source_layer_name}' not found in object '{obj.name}'")
            return

        source_vcol_layer = obj.data.vertex_colors[source_layer_name]
        target_vcol_layer = obj.data.vertex_colors.active

        for poly in obj.data.polygons:
            for loop_idx in poly.loop_indices:
                source_value = source_vcol_layer.data[loop_idx].color[0]
                r, g, b, a = target_vcol_layer.data[loop_idx].color
                if target_channel == 'RED':
                    target_vcol_layer.data[loop_idx].color = (source_value, g, b, a)
                elif target_channel == 'GREEN':
                    target_vcol_layer.data[loop_idx].color = (r, source_value, b, a)
                elif target_channel == 'BLUE':
                    target_vcol_layer.data[loop_idx].color = (r, g, source_value, a)
                elif target_channel == 'ALPHA':
                    target_vcol_layer.data[loop_idx].color = (r, g, b, source_value)

import bpy

class BAKE_OT_ao_to_vertex_color(bpy.types.Operator):
    bl_idname = "object.bake_ao_to_vertex_color"
    bl_label = "Bake AO to Vertex Color"
    bl_description = "Bakes AO to the selected vertex color channel for all selected meshes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not selected_objects:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}

        # Set render engine to Cycles
        context.scene.render.engine = 'CYCLES'

        # Backup the original bake type
        original_bake_type = context.scene.cycles.bake_type
        context.scene.cycles.bake_type = 'AO'

        # Get the target channel index
        channel_index = int(context.scene.bake_ao_vertex_color_channel)

        for obj in selected_objects:
            # Ensure the object has a valid color attribute
            color_layer = obj.data.color_attributes.active
            if not color_layer or color_layer.domain != 'CORNER' or color_layer.data_type not in {'BYTE_COLOR', 'FLOAT_COLOR'}:
                self.report({'ERROR'}, f"Object {obj.name} lacks a valid face-corner Color Attributes layer. Skipping.")
                continue

            # Backup current color data
            original_colors = [list(data.color) for data in color_layer.data]

            # Prepare the object for baking
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj

            try:
                # Perform the AO bake
                bpy.ops.object.bake(type='AO')

                # Apply the baked results to the selected channel while restoring other channels
                for poly in obj.data.polygons:
                    for loop_index in poly.loop_indices:
                        baked_value = color_layer.data[loop_index].color[0]  # AO is baked into the first channel
                        new_color = original_colors[loop_index]
                        new_color[channel_index] = baked_value
                        color_layer.data[loop_index].color = tuple(new_color)

                self.report({'INFO'}, f"AO bake completed for {obj.name}")
            except RuntimeError as e:
                if "No active image found" in str(e):
                    self.report({'ERROR'}, f"Object {obj.name} - Turn the bake output target to Active Color Attribute")
                else:
                    self.report({'ERROR'}, f"Object {obj.name} - Bake failed: {str(e)}")
            finally:
                # Restore the original bake type
                context.scene.cycles.bake_type = original_bake_type

        return {'FINISHED'}



class BAKE_OT_import_image(bpy.types.Operator, ImportHelper):
    bl_idname = "object.import_bake_image"
    bl_label = "Import Image"
    bl_description = "Import an image to use for baking"
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob: bpy.props.StringProperty(
        default="*.png;*.jpg;*.jpeg;*.bmp;*.tga",
        options={'HIDDEN'},
        maxlen=255,
    )

    def execute(self, context):
        try:
            image = bpy.data.images.load(self.filepath)
            context.scene.bake_texture_image = image
            self.report({'INFO'}, f"Loaded image: {image.name}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load image: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}





class BAKE_OT_texture_to_vertex_colors(bpy.types.Operator):
    bl_idname = "object.bake_texture_to_vertex_colors"
    bl_label = "Bake Texture to Vertex Colors"
    bl_description = "Bake texture color into vertex colors for all selected meshes using the selected UV index, image, and channel"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        scene = context.scene

        if not selected_objects:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}

        if not scene.bake_texture_image:
            self.report({'ERROR'}, "No image selected for baking")
            return {'CANCELLED'}

        image = scene.bake_texture_image
        image_pixels = list(image.pixels)
        image_width = image.size[0]
        image_height = image.size[1]

        for obj in selected_objects:
            if not obj.data.uv_layers:
                self.report({'WARNING'}, f"Object {obj.name} has no UV layers, skipping")
                continue

            if scene.uv_index >= len(obj.data.uv_layers):
                self.report({'WARNING'}, f"UV index {scene.uv_index} is out of range for object {obj.name}, skipping")
                continue

            uv_layer = obj.data.uv_layers[scene.uv_index]

            # Prepare vertex colors
            color_layer = obj.data.vertex_colors.get("Col")
            if not color_layer:
                color_layer = obj.data.vertex_colors.new(name="Col")

            bm = bmesh.new()
            bm.from_mesh(obj.data)
            uv_layer_bm = bm.loops.layers.uv[uv_layer.name]
            color_layer_bm = bm.loops.layers.color["Col"]

            # Save current vertex color data
            original_colors = {}
            for face in bm.faces:
                for loop in face.loops:
                    original_colors[loop.index] = loop[color_layer_bm]

            # Sample texture color and bake to vertex colors
            for face in bm.faces:
                for loop in face.loops:
                    uv = loop[uv_layer_bm].uv
                    x = int(uv.x * (image_width - 1))
                    y = int(uv.y * (image_height - 1))

                    # Get color from image
                    pixel_index = (y * image_width + x) * 4
                    r, g, b, a = image_pixels[pixel_index:pixel_index + 4]

                    # Assign vertex color to selected channel
                    selected_channel = scene.color_channel
                    if selected_channel == 'R':
                        loop[color_layer_bm] = (r, original_colors[loop.index][1], original_colors[loop.index][2], original_colors[loop.index][3])
                    elif selected_channel == 'G':
                        loop[color_layer_bm] = (original_colors[loop.index][0], g, original_colors[loop.index][2], original_colors[loop.index][3])
                    elif selected_channel == 'B':
                        loop[color_layer_bm] = (original_colors[loop.index][0], original_colors[loop.index][1], b, original_colors[loop.index][3])
                    elif selected_channel == 'A':
                        loop[color_layer_bm] = (original_colors[loop.index][0], original_colors[loop.index][1], original_colors[loop.index][2], a)

            bm.to_mesh(obj.data)
            bm.free()
            obj.data.update()

        self.report({'INFO'}, "Baking completed for all selected meshes")
        return {'FINISHED'}


class SwapColorChannelsOperator(bpy.types.Operator):
    """Swap two color channels in the active color attribute for all selected meshes"""
    bl_idname = "mesh.swap_color_channels"
    bl_label = "Swap Color Channels"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.selected_objects and any(
            obj.type == 'MESH' and obj.data.color_attributes.active
            for obj in context.selected_objects
        )

    def execute(self, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']

        props = context.scene.color_channel_swapper_props

        # Convert the selected channels to integers
        source_channel_switch = int(props.source_channel_switch)
        target_channel_switch = int(props.target_channel_switch)

        if source_channel_switch == target_channel_switch:
            self.report({'WARNING'}, "Source and target channels must be different")
            return {'CANCELLED'}

        swapped_objects = []
        skipped_objects = []

        for obj in selected_objects:
            mesh = obj.data
            color_layer = mesh.color_attributes.active

            if not color_layer or color_layer.data is None:
                skipped_objects.append(obj.name)
                continue

            # Swap the data
            for color in color_layer.data:
                color_data = list(color.color)
                color_data[source_channel_switch], color_data[target_channel_switch] = (
                    color_data[target_channel_switch], 
                    color_data[source_channel_switch]
                )
                color.color = color_data

            swapped_objects.append(obj.name)

        # Report results
        if swapped_objects:
            self.report({'INFO'}, f"Swapped channels for: {', '.join(swapped_objects)}")
        if skipped_objects:
            self.report({'WARNING'}, f"Skipped objects with no valid color attributes: {', '.join(skipped_objects)}")

        return {'FINISHED'}


class ColorChannelSwapperProperties(bpy.types.PropertyGroup):
    """Properties for the Color Channel Swapper"""
    source_channel_switch: bpy.props.EnumProperty(
        name="Source Channel",
        description="Select the source channel to swap",
        items=[
            ('0', 'Red', 'Red channel'),
            ('1', 'Green', 'Green channel'),
            ('2', 'Blue', 'Blue channel'),
            ('3', 'Alpha', 'Alpha channel'),
        ],
        default='0'
    )
    target_channel_switch: bpy.props.EnumProperty(
        name="Target Channel",
        description="Select the target channel to swap",
        items=[
            ('0', 'Red', 'Red channel'),
            ('1', 'Green', 'Green channel'),
            ('2', 'Blue', 'Blue channel'),
            ('3', 'Alpha', 'Alpha channel'),
        ],
        default='1'
    )

class VertexColorFillPanel(bpy.types.Panel):
    bl_label = "Enhanced Vertex Color Tool"
    bl_idname = "OBJECT_PT_vertex_color_tool"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tarmunds Addons'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Fill Colors Section
        box = layout.box()
        row = box.row()
        row.prop(scene, "show_fill_colors", text="", icon="BRUSH_DATA", emboss=False)
        row.label(text="Fill Colors")
        row.prop(scene, "show_fill_colors", text="", icon="TRIA_DOWN" if scene.show_fill_colors else "TRIA_RIGHT", emboss=False, icon_only=True, invert_checkbox=True)
        if scene.show_fill_colors:
            # Vertex Fill Color
            box.prop(context.scene, "vertex_fill_color", text="Vertex Fill Color")

            # Apply Fill
            box.operator("object.vertex_color_fill", text="Apply Fill")

            # Fill White and Fill Black in the same row
            row = box.row(align=True)
            row.operator("object.vertex_color_fill_white", text="Fill White")
            row.operator("object.vertex_color_fill_black", text="Fill Black")

        # Fill Alpha Section
        box = layout.box()
        row = box.row()
        row.prop(scene, "show_fill_alpha", text="", icon="MATFLUID", emboss=False)
        row.label(text="Fill Alpha Channel")
        row.prop(scene, "show_fill_alpha", text="", icon="TRIA_DOWN" if scene.show_fill_alpha else "TRIA_RIGHT", emboss=False, icon_only=True, invert_checkbox=True)
        if scene.show_fill_alpha:
            box.prop(context.scene, "vertex_fill_alpha", text="Alpha Value")
            box.operator("object.fill_vertex_alpha", text="Apply Alpha Fill")

        # Gradient Fill Section
        box = layout.box()
        row = box.row()
        row.prop(scene, "show_gradient_fill", text="", icon="TRANSFORM_ORIGINS", emboss=False)
        row.label(text="Gradient Fill")
        row.prop(scene, "show_gradient_fill", text="", icon="TRIA_DOWN" if scene.show_gradient_fill else "TRIA_RIGHT", emboss=False, icon_only=True, invert_checkbox=True)
        if scene.show_gradient_fill:
            box.prop(context.scene, "gradient_direction", text="Direction")
            box.prop(context.scene, "gradient_target_channel", text="Target Channel")
            box.prop(context.scene, "gradient_inverse", text="Inverse Gradient")
            box.prop(context.scene, "gradient_global", text="Global Gradient")
            box.operator("object.vertex_color_gradient_fill", text="Apply Gradient")

        # Randomize Colors Section
        box = layout.box()
        row = box.row()
        row.prop(scene, "show_randomize_colors", text="", icon="PARTICLES", emboss=False)
        row.label(text="Randomize Colors")
        row.prop(scene, "show_randomize_colors", text="", icon="TRIA_DOWN" if scene.show_randomize_colors else "TRIA_RIGHT", emboss=False, icon_only=True, invert_checkbox=True)
        if scene.show_randomize_colors:
            box.prop(context.scene, "random_target_channel", text="Target Channel")
            box.prop(context.scene, "random_normalize", text="Normalized Random")
            box.operator("object.vertex_color_randomize", text="Apply Randomization")

        # Merge Layers Section
        box = layout.box()
        row = box.row()
        row.prop(scene, "show_merge_layers", text="", icon="IMPORT", emboss=False)
        row.label(text="Merge Vertex Color Layers")
        row.prop(scene, "show_merge_layers", text="", icon="TRIA_DOWN" if scene.show_merge_layers else "TRIA_RIGHT", emboss=False, icon_only=True, invert_checkbox=True)
        if scene.show_merge_layers:
            box.prop(context.scene, "source_vertex_color_layer", text="Source Layer")
            box.prop(context.scene, "ao_target_channel", text="Target Channel")
            box.operator("object.merge_vertex_color_layers", text="Merge Layers")

        # Baked AO Section
        box = layout.box()
        row = box.row()
        row.prop(scene, "show_bake_ao", text="", icon="SHADING_RENDERED", emboss=False)
        row.label(text="Bake AO into channel")
        row.prop(scene, "show_bake_ao", text="", icon="TRIA_DOWN" if scene.show_bake_ao else "TRIA_RIGHT", emboss=False, icon_only=True, invert_checkbox=True)
        if scene.show_bake_ao:
            box.prop(context.scene, "bake_ao_vertex_color_channel", text="Channel")
            box.operator("object.bake_ao_to_vertex_color", text="Bake AO")

        # Baked Texture Section
        box = layout.box()
        row = box.row()
        row.prop(scene, "show_bake_texture", text="", icon="NODE_TEXTURE", emboss=False)
        row.label(text="Bake Texture into channel")
        row.prop(scene, "show_bake_texture", text="", icon="TRIA_DOWN" if scene.show_bake_texture else "TRIA_RIGHT", emboss=False, icon_only=True, invert_checkbox=True)
        if scene.show_bake_texture:
            # UV Index
            box.prop(scene, "uv_index", text="UV Index")

            # Image Selection and Import
            row = box.row(align=True)
            row.prop(scene, "bake_texture_image", text="Image")
            row.operator("object.import_bake_image", text="", icon="FILE_IMAGE")

            # Channel Selection and Bake Button
            box.prop(scene, "color_channel", text="Channel")
            box.operator("object.bake_texture_to_vertex_colors", text="Bake")
        

        # Switch Channels
        box = layout.box()
        row = box.row()
        row.prop(scene, "show_switch_channels", text="", icon="ARROW_LEFTRIGHT", emboss=False)
        row.label(text="Switch Channels Data")
        row.prop(scene, "show_switch_channels", text="", icon="TRIA_DOWN" if scene.show_switch_channels else "TRIA_RIGHT", emboss=False, icon_only=True, invert_checkbox=True)
        if scene.show_switch_channels:
            # Retrieve the properties from context.scene
            props = scene.color_channel_swapper_props  # Ensure this line is added
            box.prop(props, "source_channel_switch")
            box.prop(props, "target_channel_switch")
            box.operator("mesh.swap_color_channels", text="Swap Channels")

        

def register_properties():
    bpy.types.Scene.show_fill_colors = bpy.props.BoolProperty(
        name="Show Fill Colors",
        default=True,
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

def unregister_properties():
    del bpy.types.Scene.show_fill_colors
    del bpy.types.Scene.show_fill_alpha
    del bpy.types.Scene.show_gradient_fill
    del bpy.types.Scene.show_randomize_colors
    del bpy.types.Scene.show_merge_layers
    del bpy.types.Scene.show_bake_ao
    del bpy.types.Scene.show_bake_texture
    del bpy.types.Scene.show_switch_channels



classes = [
    VertexColorFillOperator,
    VertexColorFillWhiteOperator,
    VertexColorFillBlackOperator,
    VertexColorGradientFillOperator,
    VertexColorRandomizeOperator,
    FillVertexAlphaOperator,
    MergeVertexColorLayersOperator,
    BAKE_OT_ao_to_vertex_color,
    BAKE_OT_import_image,
    BAKE_OT_texture_to_vertex_colors,
    SwapColorChannelsOperator,
    ColorChannelSwapperProperties,
    VertexColorFillPanel
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
        default=(0.8, 0.8, 0.8)
    )

    bpy.types.Scene.gradient_direction = bpy.props.EnumProperty(
        name="Gradient Direction",
        items=[
            ('BOTTOM_TOP', "Bottom-Top", "Gradient along Z-axis"),
            ('LEFT_RIGHT', "Left-Right", "Gradient along X-axis"),
            ('FRONT_BACK', "Front-Back", "Gradient along Y-axis")
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

    bpy.types.Scene.source_vertex_color_layer = bpy.props.StringProperty(
        name="Source Vertex Color Layer",
        description="Name of the source vertex color layer to merge from"
    )

    bpy.types.Scene.ao_target_channel = bpy.props.EnumProperty(
        name="AO Target Channel",
        description="Choose which channel to merge to",
        items=[
            ('RED', "Red", "Merge to the red channel"),
            ('GREEN', "Green", "Merge to the green channel"),
            ('BLUE', "Blue", "Merge to the blue channel"),
            ('ALPHA', "Alpha", "Merge to the alpha channel")
        ],
        default='RED'
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
    bpy.types.Scene.color_channel_swapper_props = bpy.props.PointerProperty(type=ColorChannelSwapperProperties)
    register_properties()

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.vertex_fill_color
    del bpy.types.Scene.gradient_direction
    del bpy.types.Scene.gradient_target_channel
    del bpy.types.Scene.gradient_inverse
    del bpy.types.Scene.gradient_global
    del bpy.types.Scene.vertex_fill_alpha
    del bpy.types.Scene.random_target_channel
    del bpy.types.Scene.random_normalize
    del bpy.types.Scene.source_vertex_color_layer
    del bpy.types.Scene.ao_target_channel
    del bpy.types.Scene.bake_ao_vertex_color_channel
    del bpy.types.Scene.uv_index
    del bpy.types.Scene.bake_texture_image
    del bpy.types.Scene.color_channel
    del bpy.types.Scene.color_channel_swapper_props

    unregister_properties()

if __name__ == "__main__":
    register()
