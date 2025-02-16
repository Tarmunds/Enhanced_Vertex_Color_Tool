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


import bpy, random, bmesh, time
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
        use_world_space = context.scene.gradient_use_world_space

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

class BakeAOToVertexColor(bpy.types.Operator):
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
                x = int(uv.x * width)
                y = int(uv.y * height)
                pixel_index = (y * width + x) * 4

                color = vertex_color.data[loop_index].color
                color[channel_index] = pixels[pixel_index]
                vertex_color.data[loop_index].color = color

        # Cleanup
        bpy.data.images.remove(temp_image)
        bpy.data.materials.remove(temp_material)

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

class SwitchVertexColorsOperator(bpy.types.Operator):
    """Operator to switch vertex color channel values"""
    bl_idname = "object.switch_vertex_colors"
    bl_label = "Switch Vertex Colors"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Get the source and target channels from the scene properties
        source_channel = context.scene.vc_source_channel
        target_channel = context.scene.vc_target_channel

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

class FlipFlopShading(bpy.types.Operator):
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

class VertexColorClearChannelOperator(bpy.types.Operator):
    bl_idname = "vertex_color.clear_channel"
    bl_label = "Clear Vertex Color Channel"
    bl_description = "Clears the selected vertex color channel for all selected meshes by setting it to the specified value"
    bl_options = {'REGISTER', 'UNDO'}

    value: bpy.props.FloatProperty()

    def execute(self, context):
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

class VertexColorFillPanel(bpy.types.Panel):
    bl_label = "Enhanced Vertex Color Tool"
    bl_idname = "OBJECT_PT_vertex_color_tool"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tarmunds Addons'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        row = layout.row()
        row.scale_y = 1.5
        # Determine the current shading color type
        shading_color_type = "MATERIAL"
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        shading_color_type = space.shading.color_type

        # Set the icon and depress state based on the shading color type
        if shading_color_type == 'VERTEX':
            row.operator(
                "view3d.flip_flop_shading",
                text="See Vertex Color",
                icon='HIDE_OFF',
                depress=True
            )
        else:
            row.operator(
                "view3d.flip_flop_shading",
                text="See Vertex Color",
                icon='HIDE_ON',
                depress=False
            )


        # Fill Colors Section
        box = layout.box()
        row = box.row()
        row.prop(scene, "show_fill_colors", text="", icon="BRUSH_DATA", emboss=False)
        row.label(text="Fill Colors")
        row.prop(scene, "show_fill_colors", text="", icon="TRIA_DOWN" if scene.show_fill_colors else "TRIA_RIGHT", emboss=False, icon_only=True, invert_checkbox=True)
        if scene.show_fill_colors:
            box.prop(scene, "vertex_fill_color", text="Vertex Fill Color")
            box.operator("object.vertex_color_fill", text="Apply Fill")
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
            box.prop(scene, "vertex_fill_alpha", text="Alpha Value")
            box.operator("object.fill_vertex_alpha", text="Apply Alpha Fill")



        # Gradient Fill Section
        box = layout.box()
        row = box.row()
        row.prop(scene, "show_gradient_fill", text="", icon="TRANSFORM_ORIGINS", emboss=False)
        row.label(text="Gradient Fill")
        row.prop(scene, "show_gradient_fill", text="", icon="TRIA_DOWN" if scene.show_gradient_fill else "TRIA_RIGHT", emboss=False, icon_only=True, invert_checkbox=True)
        if scene.show_gradient_fill:
            box.prop(scene, "gradient_direction", text="Direction")
            row = box.row()
            row.prop(scene, "gradient_target_channel", expand=True)
            box.prop(scene, "gradient_inverse", text="Inverse Gradient")
            box.prop(scene, "gradient_use_world_space", text="Use World Cordinate")
            box.prop(scene, "gradient_global", text="Global Gradient")
            box.operator("object.vertex_color_gradient_fill", text="Apply Gradient")
            box.prop(scene, "show_gradient_range",
                 icon='TRIA_DOWN' if scene.show_gradient_range else 'TRIA_RIGHT',
                 text="Gradient Range", emboss=False)            
            if scene.show_gradient_range:
                box.prop(context.scene, "gradient_start")
                box.prop(context.scene, "gradient_end")

        # Randomize Colors Section
        box = layout.box()
        row = box.row()
        row.prop(scene, "show_randomize_colors", text="", icon="PARTICLES", emboss=False)
        row.label(text="Randomize Colors")
        row.prop(scene, "show_randomize_colors", text="", icon="TRIA_DOWN" if scene.show_randomize_colors else "TRIA_RIGHT", emboss=False, icon_only=True, invert_checkbox=True)
        if scene.show_randomize_colors:
            row = box.row()
            row.prop(scene, "random_target_channel", expand=True)
            box.prop(scene, "random_normalize", text="Normalized Random")
            box.operator("object.vertex_color_randomize", text="Apply Randomization")

        # Baked Texture Section
        box = layout.box()
        row = box.row()
        row.prop(scene, "show_bake_texture", text="", icon="NODE_TEXTURE", emboss=False)
        row.label(text="Bake Texture into Channel")
        row.prop(scene, "show_bake_texture", text="", icon="TRIA_DOWN" if scene.show_bake_texture else "TRIA_RIGHT", emboss=False, icon_only=True, invert_checkbox=True)

        if scene.show_bake_texture:
            # Color Channel Selection
            row = box.row()
            row.prop(scene, "color_channel", expand=True)
            
            # UV Index Selection
            box.prop(scene, "uv_index", text="UV Index")
            
            # Image Selection Row
            row = box.row(align=True)
            row.prop(scene, "bake_texture_image", text="Image")
            row.operator("object.import_bake_image", text="", icon="FILE_IMAGE")
            
            # Bake Button
            box.operator("object.bake_texture_to_vertex_colors", text="Bake Texture")

        # Bake AO Section
        box = layout.box()
        row = box.row()
        row.prop(scene, "show_bake_ao", text="", icon="SHADING_RENDERED", emboss=False)
        row.label(text="Bake AO into channel")
        row.prop(scene, "show_bake_ao", text="", icon="TRIA_DOWN" if scene.show_bake_ao else "TRIA_RIGHT", emboss=False, icon_only=True, invert_checkbox=True)
        if scene.show_bake_ao:
            row = box.row()
            row.prop(scene, "ao_vertex_channel", expand=True)
            box.prop(scene, "ao_uv_index")
            box.operator("object.bake_ao_to_vertex_color")

            # Add progress bar
            if scene.bake_progress < 1.0:
                box.label(text=f"Progress: {int(scene.bake_progress * 100)}%")
                box.prop(scene, "bake_progress", text="", slider=True)
            else:
                box.label(text="Progress: Complete")

        # Switch Channels Section
        box = layout.box()
        row = box.row()
        row.prop(scene, "show_switch_channels", text="", icon="ARROW_LEFTRIGHT", emboss=False)
        row.label(text="Switch Channels Data")
        row.prop(scene, "show_switch_channels", text="", icon="TRIA_DOWN" if scene.show_switch_channels else "TRIA_RIGHT", emboss=False, icon_only=True, invert_checkbox=True)
        if scene.show_switch_channels:
            box.label(text="Select Channels to Switch:")
            row = box.row()
            row.prop(scene, "vc_source_channel", expand=True)
            row = box.row()
            row.prop(scene, "vc_target_channel", expand=True)
            box.operator("object.switch_vertex_colors", text="Switch Channels")

        # Clear Channels Section
        box = layout.box()
        row = box.row()
        row.prop(scene, "show_clear_channels", text="", icon="TRASH", emboss=False)
        row.label(text="Clear Channels Data")
        row.prop(scene, "show_clear_channels", text="", icon="TRIA_DOWN" if scene.show_clear_channels else "TRIA_RIGHT", emboss=False, icon_only=True, invert_checkbox=True)
        if scene.show_clear_channels:
            box.label(text="Select Channels to Clear:")
            row = box.row()
            row.prop(scene, "vertex_color_clear_channel", expand=True)
            box.operator("vertex_color.clear_channel", text="Clear to 0").value = 0
            box.operator("vertex_color.clear_channel", text="Clear to 1").value = 1

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
        description="Expand or collapse the Switch Channels section"
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
    VertexColorFillOperator,
    VertexColorFillWhiteOperator,
    VertexColorFillBlackOperator,
    VertexColorGradientFillOperator,
    VertexColorRandomizeOperator,
    FillVertexAlphaOperator,
    BakeAOToVertexColor,
    BAKE_OT_import_image,
    BAKE_OT_texture_to_vertex_colors,
    SwitchVertexColorsOperator,
    VertexColorClearChannelOperator,
    FlipFlopShading,
    VertexColorFillPanel,
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
