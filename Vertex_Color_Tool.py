bl_info = {
    "name": "Enhanced Vertex Color Tool",
    "blender": (2, 80, 0),
    "category": "Object",
    "version": (2, 0, 0),
    "author": "Tarmunds",
    "description": "Advanced vertex color tools: fill, gradients, randomization, transfer, and preview mode."
}

import bpy
import random

class VertexColorFillPreviewOperator(bpy.types.Operator):
    bl_idname = "object.vertex_color_fill_preview"
    bl_label = "Preview Vertex Color Fill"
    bl_options = {'REGISTER', 'UNDO'}

    original_colors = {}

    def execute(self, context):
        color = context.scene.vertex_fill_color
        self.original_colors.clear()
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                self.store_original_colors(obj)
                self.fill_vertex_color_preview(obj, color)
        return {'FINISHED'}

    def store_original_colors(self, obj):
        if obj.data.vertex_colors:
            vcol_layer = obj.data.vertex_colors.active
            self.original_colors[obj] = [tuple(loop.color) for loop in vcol_layer.data]

    def fill_vertex_color_preview(self, obj, color):
        if not obj.data.vertex_colors:
            obj.data.vertex_colors.new()

        vcol_layer = obj.data.vertex_colors.active
        r, g, b = color[:3]

        for poly in obj.data.polygons:
            for loop_idx in poly.loop_indices:
                vcol_layer.data[loop_idx].color = (r, g, b, 1.0)

    def cancel(self, context):
        for obj, colors in self.original_colors.items():
            if obj.data.vertex_colors:
                vcol_layer = obj.data.vertex_colors.active
                for i, color in enumerate(colors):
                    vcol_layer.data[i].color = color

class VertexColorGradientFillOperator(bpy.types.Operator):
    bl_idname = "object.vertex_color_gradient_fill"
    bl_label = "Apply Gradient to Vertex Color"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        direction = context.scene.gradient_direction
        target_channel = context.scene.gradient_target_channel
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                self.apply_gradient(obj, direction, target_channel)
        return {'FINISHED'}

    def apply_gradient(self, obj, direction, target_channel):
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

class VertexColorRandomizeOperator(bpy.types.Operator):
    bl_idname = "object.vertex_color_randomize"
    bl_label = "Randomize Vertex Colors"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target_channel = context.scene.random_target_channel
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                self.randomize_colors(obj, target_channel)
        return {'FINISHED'}

    def randomize_colors(self, obj, target_channel):
        if not obj.data.vertex_colors:
            obj.data.vertex_colors.new()

        vcol_layer = obj.data.vertex_colors.active

        for poly in obj.data.polygons:
            for loop_idx in poly.loop_indices:
                r, g, b, a = vcol_layer.data[loop_idx].color
                rand_value = random.random()
                if target_channel == 'RED':
                    vcol_layer.data[loop_idx].color = (rand_value, g, b, a)
                elif target_channel == 'GREEN':
                    vcol_layer.data[loop_idx].color = (r, rand_value, b, a)
                elif target_channel == 'BLUE':
                    vcol_layer.data[loop_idx].color = (r, g, rand_value, a)

class VertexColorFillPanel(bpy.types.Panel):
    bl_label = "Enhanced Vertex Color Tool"
    bl_idname = "OBJECT_PT_vertex_color_tool"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tarmunds Addons'

    def draw(self, context):
        layout = self.layout

        # Fill
        layout.label(text="Fill Colors")
        layout.prop(context.scene, "vertex_fill_color", text="Fill Color")
        layout.operator("object.vertex_color_fill_preview", text="Preview Fill")
        layout.operator("object.vertex_color_fill", text="Apply Fill")

        # Gradient
        layout.separator()
        layout.label(text="Gradient Fill")
        layout.prop(context.scene, "gradient_direction", text="Direction")
        layout.prop(context.scene, "gradient_target_channel", text="Target Channel")
        layout.operator("object.vertex_color_gradient_fill")

        # Randomize
        layout.separator()
        layout.label(text="Randomize Colors")
        layout.prop(context.scene, "random_target_channel", text="Target Channel")
        layout.operator("object.vertex_color_randomize")

classes = [
    VertexColorFillPreviewOperator,
    VertexColorGradientFillOperator,
    VertexColorRandomizeOperator,
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

    bpy.types.Scene.random_target_channel = bpy.props.EnumProperty(
        name="Random Target Channel",
        items=[
            ('RED', "Red", "Randomize Red channel"),
            ('GREEN', "Green", "Randomize Green channel"),
            ('BLUE', "Blue", "Randomize Blue channel")
        ],
        default='RED'
    )

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.vertex_fill_color
    del bpy.types.Scene.gradient_direction
    del bpy.types.Scene.gradient_target_channel
    del bpy.types.Scene.random_target_channel

if __name__ == "__main__":
    register()
