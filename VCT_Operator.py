import bpy, random, bmesh, time, numpy as np
from bpy_extras.io_utils import ImportHelper
from bpy.props import EnumProperty, PointerProperty, BoolProperty
from bpy.types import Operator, PropertyGroup
from mathutils import Vector
from bpy.types import Operator, Panel


def ensure_object_mode(self, context):
    if context.object and context.object.mode != 'OBJECT':
        self.report({'ERROR'}, "Only usable in Object Mode.")
        return False
    return True

class VCT_VertexColorFillOperator(bpy.types.Operator):
    bl_idname = "object.vertex_color_fill"
    bl_label = "Fill Vertex Color"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if not ensure_object_mode(self, context):
            return {'CANCELLED'}
        
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

class VCT_VertexColorFillWhiteOperator(bpy.types.Operator):
    bl_idname = "object.vertex_color_fill_white"
    bl_label = "Fill White"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if not ensure_object_mode(self, context):
            return {'CANCELLED'}

        color = (1.0, 1.0, 1.0)
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                VCT_VertexColorFillOperator.fill_vertex_color(self, obj, color)
        return {'FINISHED'}

class VCT_VertexColorFillBlackOperator(bpy.types.Operator):
    bl_idname = "object.vertex_color_fill_black"
    bl_label = "Fill Black"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if not ensure_object_mode(self, context):
            return {'CANCELLED'}

        color = (0.0, 0.0, 0.0)
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                VCT_VertexColorFillOperator.fill_vertex_color(self, obj, color)
        return {'FINISHED'}

class VCT_VertexColorGradientFillOperator(bpy.types.Operator):
    bl_idname = "object.vertex_color_gradient_fill"
    bl_label = "Apply Gradient to Vertex Color"
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):
        direction = context.scene.gradient_direction
        target_channel = context.scene.gradient_target_channel
        inverse_gradient = context.scene.gradient_inverse
        global_gradient = context.scene.gradient_global
        use_world_space = context.scene.gradient_use_world_space

        if not ensure_object_mode(self, context):
            return {'CANCELLED'}

        if global_gradient:
            self.apply_global_gradient(context.selected_objects, direction, target_channel, inverse_gradient, context)
        else:
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    self.apply_gradient(obj, direction, target_channel, inverse_gradient, use_world_space, context)
        return {'FINISHED'}

    def apply_gradient(self, obj, direction, target_channel, inverse_gradient, use_world_space, context):
        if not obj.data.vertex_colors:
            obj.data.vertex_colors.new()

        vcol_layer = obj.data.vertex_colors.active

        min_val, max_val = self.get_bounds(obj, direction, use_world_space)
        if max_val == min_val:
            max_val = min_val + 1e-6  # Prevent division by zero
        for poly in obj.data.polygons:
            for loop_idx in poly.loop_indices:
                coord = self.get_coordinate(obj.data.loops[loop_idx].vertex_index, obj, direction, use_world_space)
                gradient_value = (coord - min_val) / (max_val - min_val)
                gradient_value = context.scene.gradient_start + gradient_value * (context.scene.gradient_end - context.scene.gradient_start)
                if inverse_gradient:
                    gradient_value = 1.0 - gradient_value
                r, g, b, a = vcol_layer.data[loop_idx].color
                if target_channel == 'RED':
                    vcol_layer.data[loop_idx].color = (gradient_value, g, b, a)
                elif target_channel == 'GREEN':
                    vcol_layer.data[loop_idx].color = (r, gradient_value, b, a)
                elif target_channel == 'BLUE':
                    vcol_layer.data[loop_idx].color = (r, g, gradient_value, a)

    def apply_global_gradient(self, objects, direction, target_channel, inverse_gradient, context):
        all_coords = []
        for obj in objects:
            if obj.type == 'MESH':
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
                        gradient_value = context.scene.gradient_start + gradient_value * (context.scene.gradient_end - context.scene.gradient_start)
                        if inverse_gradient:
                            gradient_value = 1.0 - gradient_value
                        r, g, b, a = vcol_layer.data[loop_idx].color
                        if target_channel == 'RED':
                            vcol_layer.data[loop_idx].color = (gradient_value, g, b, a)
                        elif target_channel == 'GREEN':
                            vcol_layer.data[loop_idx].color = (r, gradient_value, b, a)
                        elif target_channel == 'BLUE':
                            vcol_layer.data[loop_idx].color = (r, g, gradient_value, a)

    def get_bounds(self, obj, direction, use_world_space):
        coords = [self.get_coordinate(v.index, obj, direction, use_world_space) for v in obj.data.vertices]
        return min(coords), max(coords)

    def get_coordinate(self, vertex_idx, obj, direction, use_world_space):
        if use_world_space:
            coord = obj.matrix_world @ obj.data.vertices[vertex_idx].co
        else:
            coord = obj.data.vertices[vertex_idx].co

        if direction == 'BOTTOM_TOP':
            return coord.z
        elif direction == 'LEFT_RIGHT':
            return coord.x
        elif direction == 'FRONT_BACK':
            return coord.y

    def get_global_coordinate(self, vertex_idx, obj, direction):
        coord = obj.matrix_world @ obj.data.vertices[vertex_idx].co
        if direction == 'BOTTOM_TOP':
            return coord.z
        elif direction == 'LEFT_RIGHT':
            return coord.x
        elif direction == 'FRONT_BACK':
            return coord.y

class VCT_VertexColorRandomizeOperator(bpy.types.Operator):
    bl_idname = "object.vertex_color_randomize"
    bl_label = "Randomize Vertex Colors"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target_channel = context.scene.random_target_channel
        normalize = context.scene.random_normalize
        objects = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not ensure_object_mode(self, context):
            return {'CANCELLED'}

        if normalize and objects:
            step = 1.0 / max(1, len(objects) - 1)
            normalized_values = [i * step for i in range(len(objects))]
            random.shuffle(normalized_values)  # Shuffle the order of normalized values

            for obj, normalized_value in zip(objects, normalized_values):
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

class VCT_FillVertexAlphaOperator(bpy.types.Operator):
    bl_idname = "object.fill_vertex_alpha"
    bl_label = "Fill Vertex Alpha"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if not ensure_object_mode(self, context):
            return {'CANCELLED'}

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

class VCT_BakeAOToVertexColor(bpy.types.Operator):
    """Bake AO to Vertex Color"""
    bl_idname = "object.bake_ao_to_vertex_color"
    bl_label = "Bake AO"
    bl_options = {'REGISTER', 'UNDO'}

    _timer = None
    _current_index = 0
    _selected_objects = []

    def modal(self, context, event):
        scene = context.scene

        if event.type == 'TIMER':
            if self._current_index >= len(self._selected_objects):
                scene.bake_progress = 1.0
                context.window_manager.event_timer_remove(self._timer)
                self.report({'INFO'}, "AO Bake Complete")
                return {'FINISHED'}

            obj = self._selected_objects[self._current_index]
            self.bake_ao_for_object(context, obj)
            self._current_index += 1

            # Update progress
            scene.bake_progress = self._current_index / len(self._selected_objects)
            context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not ensure_object_mode(self, context):
            return {'CANCELLED'}

        self._selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not self._selected_objects:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}

        # Initialize progress
        context.scene.bake_progress = 0.0
        self._current_index = 0

        # Start modal timer
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def bake_ao_for_object(self, context, obj):
        scene = context.scene
        uv_index = scene.ao_uv_index

        if uv_index >= len(obj.data.uv_layers):
            self.report({'WARNING'}, f"Skipping {obj.name}: UV index {uv_index} does not exist")
            return

        # Ensure Cycles is the active engine
        bpy.context.scene.render.engine = 'CYCLES'

        # Create a temporary image for baking
        temp_image = bpy.data.images.new("AO_Temp", width=1024, height=1024, alpha=False)

        # Create a temporary material
        temp_material = bpy.data.materials.new(name="AO_Temp_Material")
        temp_material.use_nodes = True
        node_tree = temp_material.node_tree
        tex_image_node = node_tree.nodes.new("ShaderNodeTexImage")
        tex_image_node.image = temp_image
        obj.active_material = temp_material

        # Set UV layer
        obj.data.uv_layers.active_index = uv_index

        # Assign the image node as active for baking
        node_tree.nodes.active = tex_image_node

        # Set up bake settings
        scene.cycles.bake_type = 'AO'
        scene.render.bake.use_pass_direct = False
        scene.render.bake.use_pass_indirect = False
        scene.render.bake.use_pass_color = True

        try:
            # Bake the AO
            bpy.ops.object.bake(type='AO')
        except RuntimeError as e:
            self.report({'WARNING'}, f"Baking failed for {obj.name}: {e}")
            bpy.data.images.remove(temp_image)
            bpy.data.materials.remove(temp_material)
            return

        # Transfer AO data to vertex color
        if not obj.data.vertex_colors:
            obj.data.vertex_colors.new()

        vertex_color = obj.data.vertex_colors.active
        selected_channel = scene.ao_vertex_channel
        channel_index = {"R": 0, "G": 1, "B": 2, "A": 3}[selected_channel]

        width, height = temp_image.size
        pixels = list(temp_image.pixels)

        for poly in obj.data.polygons:
            for loop_index in poly.loop_indices:
                loop = obj.data.loops[loop_index]
                uv = obj.data.uv_layers[uv_index].data[loop_index].uv

                # Check if UV is outside the valid [0,1] range
                if not (0.0 <= uv.x <= 1.0 and 0.0 <= uv.y <= 1.0):
                    self.report({'WARNING'}, f"UV island out of the UV shell in object '{obj.name}', skipping vertex color assignment.")
                    continue

                # Clamp UV coordinates to ensure they stay in valid range
                x = min(max(int(uv.x * width), 0), width - 1)
                y = min(max(int(uv.y * height), 0), height - 1)

                pixel_index = (y * width + x) * 4

                # Ensure pixel_index is within the valid range
                if 0 <= pixel_index < len(pixels):
                    color = vertex_color.data[loop_index].color
                    color[channel_index] = pixels[pixel_index]
                    vertex_color.data[loop_index].color = color

        # Cleanup
        bpy.data.images.remove(temp_image)
        bpy.data.materials.remove(temp_material)

'''
class VCT_BakeCurvatureToVertexColor(bpy.types.Operator):
    """Bake Curvature to Active Vertex Color Layer"""
    bl_idname = "object.bake_curvature_to_vertex_color"
    bl_label = "Bake Curvature"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target_channel = context.scene.curvature_vertex_channel  # 'R', 'G', or 'B'
        default_value = 0.5
        objects = [obj for obj in context.selected_objects if obj.type == 'MESH']

        for obj in objects:
            if obj.data.vertex_colors:
                self.bake_curvature(obj, target_channel, default_value)
            else:
                self.report({'WARNING'}, f"{obj.name} has no vertex color layer.")

        self.report({'INFO'}, "Curvature baking complete.")
        return {'FINISHED'}

    def bake_curvature(self, obj, target_channel, default_value):
        vcol_layer = obj.data.vertex_colors.active  # Use active layer only
        if not vcol_layer:
            self.report({'WARNING'}, f"{obj.name} has no active vertex color layer.")
            return

        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.verts.ensure_lookup_table()

        # Create a dictionary to store curvature values per vertex
        curvatures = {}

        for v in bm.verts:
            if len(v.link_edges) < 2:  # Ignore isolated verts/edges
                curvatures[v.index] = default_value
                continue

            # Calculate the Laplacian (difference between vertex and average of neighbors)
            neighbor_coords = [e.other_vert(v).co for e in v.link_edges]
            avg_neighbor_co = np.mean([np.array(co) for co in neighbor_coords], axis=0)
            laplacian = np.array(v.co) - avg_neighbor_co
            curvature = np.linalg.norm(laplacian)

            # Normalize curvature to [0, 1]
            curvature = np.clip(curvature, 0, 1)
            curvatures[v.index] = curvature

        # Apply curvature to vertex colors (directly to the mesh data, not the BMesh)
        color_data = vcol_layer.data
        loop_index = 0  # Track loop index manually

        for poly in obj.data.polygons:
            for loop_idx in poly.loop_indices:
                loop_vert_index = obj.data.loops[loop_idx].vertex_index
                r, g, b, a = color_data[loop_idx].color
                value = curvatures.get(loop_vert_index, default_value)

                # Assign to the selected channel
                if target_channel == 'R':
                    color_data[loop_idx].color = (value, g, b, a)
                elif target_channel == 'G':
                    color_data[loop_idx].color = (r, value, b, a)
                elif target_channel == 'B':
                    color_data[loop_idx].color = (r, g, value, a)

                loop_index += 1

        bm.free()
        obj.data.update()
'''

        
class VCT_BAKE_OT_import_image(bpy.types.Operator, ImportHelper):
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
        if not ensure_object_mode(self, context):
            return {'CANCELLED'}        
        
        try:
            image = bpy.data.images.load(self.filepath)
            context.scene.bake_texture_image = image
            self.report({'INFO'}, f"Loaded image: {image.name}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load image: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}

class VCT_BAKE_OT_texture_to_vertex_colors(bpy.types.Operator):
    bl_idname = "object.bake_texture_to_vertex_colors"
    bl_label = "Bake Texture to Vertex Colors"
    bl_description = "Bake texture color into vertex colors for all selected meshes using the selected UV index, image, and channel"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        scene = context.scene
        if not ensure_object_mode(self, context):
            return {'CANCELLED'}
        
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

class VCT_SwitchVertexColorsOperator(bpy.types.Operator):
    """Operator to switch vertex color channel values"""
    bl_idname = "object.switch_vertex_colors"
    bl_label = "Switch Vertex Colors"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Get the source and target channels from the scene properties
        source_channel = context.scene.vc_source_channel
        target_channel = context.scene.vc_target_channel

        if not ensure_object_mode(self, context):
            return {'CANCELLED'}

        if source_channel == target_channel:
            self.report({'ERROR'}, "Source and target channels are the same")
            return {'CANCELLED'}

        # Map channel names to indices
        channel_map = {'R': 0, 'G': 1, 'B': 2, 'A': 3}
        source_idx = channel_map[source_channel]
        target_idx = channel_map[target_channel]

        # Iterate over selected objects
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue  # Skip non-mesh objects

            if not obj.data.vertex_colors:
                self.report({'WARNING'}, f"Mesh {obj.name} has no vertex colors")
                continue

            color_layer = obj.data.vertex_colors.active

            # Switch vertex color channels for the active color layer
            for loop_color in color_layer.data:
                loop_color.color[source_idx], loop_color.color[target_idx] = (
                    loop_color.color[target_idx],
                    loop_color.color[source_idx],
                )

            self.report({'INFO'}, f"Switched {source_channel} and {target_channel} channels for {obj.name}")

        return {'FINISHED'}

class VCT_FlipFlopShading(bpy.types.Operator):
    """Flip-Flop the Shading Color Type between Material and Vertex"""
    bl_idname = "view3d.flip_flop_shading"
    bl_label = "Flip-Flop Shading"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        shading = space.shading
                        if shading.color_type == 'VERTEX':
                            shading.color_type = 'MATERIAL'
                            shading_name = 'Original Material'
                        else:
                            shading.color_type = 'VERTEX'
                            shading_name = 'Vertex Color'

                        self.report({'INFO'}, f"Shading Type set to {shading_name}")
        return {'FINISHED'}

class VCT_VertexColorClearChannelOperator(bpy.types.Operator):
    bl_idname = "vertex_color.clear_channel"
    bl_label = "Clear Vertex Color Channel"
    bl_description = "Clears the selected vertex color channel for all selected meshes by setting it to the specified value"
    bl_options = {'REGISTER', 'UNDO'}

    value: bpy.props.FloatProperty()

    def execute(self, context):
        if not ensure_object_mode(self, context):
            return {'CANCELLED'}

        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']

        if not selected_objects:
            self.report({'ERROR'}, "No selected meshes found.")
            return {'CANCELLED'}

        channel = context.scene.vertex_color_clear_channel
        affected_objects = 0

        for obj in selected_objects:
            if obj.data.vertex_colors.active is None:
                self.report({'WARNING'}, f"Object '{obj.name}' has no active vertex color layer.")
                continue

            color_layer = obj.data.vertex_colors.active.data

            for loop_color in color_layer:
                if channel == 'R':
                    loop_color.color[0] = self.value
                elif channel == 'G':
                    loop_color.color[1] = self.value
                elif channel == 'B':
                    loop_color.color[2] = self.value
                elif channel == 'A':
                    loop_color.color[3] = self.value

            affected_objects += 1

        self.report({'INFO'}, f"Cleared {channel} channel to {self.value} for {affected_objects} object(s).")
        return {'FINISHED'}



class VCT_GradientSettings(bpy.types.PropertyGroup):
    center_mode: EnumProperty(
        name="Gradient Origin",
        items=[
            ('CURSOR', "3D Cursor", ""),
            ('ACTIVE', "Active Object", ""),
            ('REFERENCE', "Reference Object", ""),
        ],
        default='CURSOR'
    )
    reference_object: PointerProperty(
        name="Reference Object",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == 'MESH'
    )
    include_center: BoolProperty(
        name="Include Center in Radius",
        description="Ensure the center is considered in the bounding radius",
        default=True
    )
    show_preview: BoolProperty(
        name="Show Visualizer",
        description="Draw a 2D preview of the gradient center and radius",
        default=False
    )

class VCT_OT_ApplyGradient(Operator):
    bl_idname = "object.vct_apply_gradient"
    bl_label = "Apply Radial Gradient"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        apply_radial_gradient(context)
        self.report({'INFO'}, "Gradient applied to vertex colors.")
        return {'FINISHED'}

# === GRADIENT APPLICATION ===

def get_gradient_center(context):
    settings = context.scene.vct_settings
    if settings.center_mode == 'CURSOR':
        return context.scene.cursor.location
    elif settings.center_mode == 'ACTIVE':
        return context.active_object.matrix_world.translation if context.active_object else Vector()
    elif settings.center_mode == 'REFERENCE':
        return settings.reference_object.matrix_world.translation if settings.reference_object else Vector()
    return Vector()


def apply_radial_gradient(context):
    settings = context.scene.vct_settings
    center = get_gradient_center(context)
    include_center = settings.include_center

    mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
    if not mesh_objects:
        return

    all_dists = [
        (obj.matrix_world @ v.co - center).length
        for obj in mesh_objects for v in obj.data.vertices
    ]
    if include_center:
        all_dists.append(0.0)

    max_radius = max(all_dists) if all_dists else 1e-6

    # Get user options
    channel = context.scene.radial_target_channel
    invert = context.scene.radial_inverse

    for obj in mesh_objects:
        mesh = obj.data
        if not mesh.vertex_colors:
            mesh.vertex_colors.new(name="Col")
        vcol_layer = mesh.vertex_colors.active

        for poly in mesh.polygons:
            for loop_idx in poly.loop_indices:
                v = mesh.vertices[mesh.loops[loop_idx].vertex_index]
                world_pos = obj.matrix_world @ v.co
                dist = (world_pos - center).length
                gradient = 1.0 - min(dist / max_radius, 1.0)
                if invert:
                    gradient = 1.0 - gradient

                r, g, b, a = vcol_layer.data[loop_idx].color
                if channel == 'RED':
                    vcol_layer.data[loop_idx].color = (gradient, g, b, a)
                elif channel == 'GREEN':
                    vcol_layer.data[loop_idx].color = (r, gradient, b, a)
                elif channel == 'BLUE':
                    vcol_layer.data[loop_idx].color = (r, g, gradient, a)

        mesh.update()