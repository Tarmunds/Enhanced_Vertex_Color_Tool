bl_info = {
    "name": "Vertex Color Channel Clearer",
    "author": "Your Name",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "3D View > Sidebar > Vertex Color",
    "description": "Allows clearing specific vertex color channels (R, G, B, A) for all selected meshes by setting them to 0 or 1.",
    "category": "Mesh",
}

import bpy

class VertexColorChannelClearerPanel(bpy.types.Panel):
    bl_label = "Vertex Color Channel Clearer"
    bl_idname = "VIEW3D_PT_vertex_color_channel_clearer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Vertex Color'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "vertex_color_clear_channel", text="Channel")
        layout.operator("vertex_color.clear_channel", text="Clear to 0").value = 0
        layout.operator("vertex_color.clear_channel", text="Clear to 1").value = 1


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


def register():
    bpy.utils.register_class(VertexColorChannelClearerPanel)
    bpy.utils.register_class(VertexColorClearChannelOperator)
    
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


def unregister():
    bpy.utils.unregister_class(VertexColorChannelClearerPanel)
    bpy.utils.unregister_class(VertexColorClearChannelOperator)
    
    del bpy.types.Scene.vertex_color_clear_channel


if __name__ == "__main__":
    register()
