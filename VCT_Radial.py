bl_info = {
    "name": "Radial Vertex Color Gradient (Visualizer)",
    "author": "Kostia",
    "version": (1, 2),
    "blender": (3, 5, 0),
    "location": "View3D > Sidebar > Vertex Color",
    "description": "Paints a radial grayscale gradient into vertex colors with live preview overlay",
    "category": "Paint",
}

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from math import cos, sin, pi
from mathutils import Vector
from bpy.types import Operator, Panel
from bpy.props import EnumProperty, PointerProperty, BoolProperty
from bpy_extras.view3d_utils import location_3d_to_region_2d

draw_handler = None
draw_timer = None


# === GRADIENT APPLICATION ===

def get_gradient_center(context):
    settings = context.scene.rvc_settings
    if settings.center_mode == 'CURSOR':
        return context.scene.cursor.location
    elif settings.center_mode == 'ACTIVE':
        return context.active_object.matrix_world.translation if context.active_object else Vector()
    elif settings.center_mode == 'REFERENCE':
        return settings.reference_object.matrix_world.translation if settings.reference_object else Vector()
    return Vector()


def apply_radial_gradient(context):
    settings = context.scene.rvc_settings
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
                value = 1.0 - min(dist / max_radius, 1.0)
                vcol_layer.data[loop_idx].color = (value, value, value, 1.0)

        mesh.update()


# === OPERATOR ===

class RVC_OT_ApplyGradient(Operator):
    bl_idname = "object.rvc_apply_gradient"
    bl_label = "Apply Radial Gradient"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        apply_radial_gradient(context)
        self.report({'INFO'}, "Gradient applied to vertex colors.")
        return {'FINISHED'}


# === PANEL ===

class RVC_PT_GradientPanel(Panel):
    bl_label = "Radial Gradient"
    bl_idname = "RVC_PT_radial_gradient"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Vertex Color'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.rvc_settings

        layout.prop(settings, "center_mode")
        if settings.center_mode == 'REFERENCE':
            layout.prop(settings, "reference_object")

        layout.prop(settings, "include_center")
        layout.prop(settings, "show_preview")
        layout.operator("object.rvc_apply_gradient", icon='BRUSH_DATA')


# === PROPERTIES ===

class RVC_GradientSettings(bpy.types.PropertyGroup):
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


# === REGISTER ===

classes = (
    RVC_OT_ApplyGradient,
    RVC_PT_GradientPanel,
    RVC_GradientSettings,
)


def register():
    global draw_handler, draw_timer
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.rvc_settings = bpy.props.PointerProperty(type=RVC_GradientSettings)

    draw_handler = bpy.types.SpaceView3D.draw_handler_add(draw_visualizer, (), 'WINDOW', 'POST_PIXEL')
    draw_timer = bpy.app.timers.register(timer_redraw)


def unregister():
    global draw_handler, draw_timer
    if draw_handler:
        bpy.types.SpaceView3D.draw_handler_remove(draw_handler, 'WINDOW')
        draw_handler = None
    if draw_timer:
        bpy.app.timers.unregister(draw_timer)
        draw_timer = None

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.rvc_settings


if __name__ == "__main__":
    register()
