bl_info = {
    "name": "Bake AO to Vertex Color Channel",
    "author": "Kostia",
    "version": (1, 1, 2),
    "blender": (3, 0, 0),
    "description": "Bake AO using Cycles and store it in a chosen vertex color channel.",
    "category": "Object",
}

import bpy

class BAKE_OT_ao_to_vertex_color(bpy.types.Operator):
    bl_idname = "object.bake_ao_to_vertex_color"
    bl_label = "Bake AO to Vertex Color"
    bl_description = "Bakes AO to the selected vertex color channel"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Active object is not a mesh")
            return {'CANCELLED'}

        if not context.scene.bake_ao_vertex_color_channel:
            self.report({'ERROR'}, "No vertex color channel selected")
            return {'CANCELLED'}

        color_layer = obj.data.color_attributes.active
        if not color_layer:
            self.report({'ERROR'}, "No active vertex color attribute found")
            return {'CANCELLED'}

        channel_index = int(context.scene.bake_ao_vertex_color_channel)

        # Set render engine to Cycles
        bpy.context.scene.render.engine = 'CYCLES'

        # Backup current color data
        original_colors = [list(data.color) for data in color_layer.data]

        # Prepare AO bake
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj

        # Ensure the color layer is active
        obj.data.color_attributes.active = color_layer

        # Set up bake settings
        original_bake_type = bpy.context.scene.cycles.bake_type
        bpy.context.scene.cycles.bake_type = 'AO'

        try:
            bpy.ops.object.bake(type='AO')

            # Apply the baked results to the selected channel while restoring other channels
            for i, poly in enumerate(obj.data.polygons):
                for loop_index in poly.loop_indices:
                    loop = obj.data.loops[loop_index]
                    baked_value = color_layer.data[loop_index].color[0]  # AO is baked into the first channel
                    new_color = original_colors[loop_index]
                    new_color[channel_index] = baked_value
                    color_layer.data[loop_index].color = tuple(new_color)

            self.report({'INFO'}, "AO bake completed and applied to vertex color")
        except Exception as e:
            self.report({'ERROR'}, f"Bake failed: {str(e)}")
        finally:
            bpy.context.scene.cycles.bake_type = original_bake_type

        return {'FINISHED'}


class BAKE_PT_ao_vertex_color_panel(bpy.types.Panel):
    bl_idname = "BAKE_PT_ao_vertex_color_panel"
    bl_label = "AO to Vertex Color"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AO Bake'

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(context.scene, "bake_ao_vertex_color_channel", text="Channel")
        col.operator("object.bake_ao_to_vertex_color", text="Bake AO")


classes = [
    BAKE_OT_ao_to_vertex_color,
    BAKE_PT_ao_vertex_color_panel
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

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

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.bake_ao_vertex_color_channel

if __name__ == "__main__":
    register()
