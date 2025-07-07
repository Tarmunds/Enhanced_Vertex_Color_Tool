bl_info = {
    "name": "Static 2D Circle Drawer",
    "author": "Kostia",
    "version": (1, 0),
    "blender": (4, 2, 0),
    "location": "3D View > Sidebar > Debug",
    "description": "Draws a static circle in the center of the viewport when enabled",
    "category": "Development",
}

import bpy
import gpu
from bpy.props import BoolProperty
from math import cos, sin, pi
from gpu_extras.batch import batch_for_shader

draw_handler = None


def draw_callback():
    region = bpy.context.region
    if not region:
        return

    width, height = region.width, region.height
    center = (width / 2, height / 2)
    radius = 100
    steps = 64

    points = [
        (
            center[0] + radius * cos(2 * pi * i / steps),
            center[1] + radius * sin(2 * pi * i / steps)
        )
        for i in range(steps + 1)
    ]

    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": points})

    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(2.0)
    shader.bind()
    shader.uniform_float("color", (1.0, 0.1, 0.1, 1.0))
    batch.draw(shader)
    gpu.state.blend_set('NONE')


class DEBUG_PT_DrawPanel(bpy.types.Panel):
    bl_label = "Static Circle Debug"
    bl_idname = "DEBUG_PT_draw_circle"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Debug'

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "draw_static_circle")


def update_draw_handler(self, context):
    global draw_handler

    if context.scene.draw_static_circle:
        if draw_handler is None:
            draw_handler = bpy.types.SpaceView3D.draw_handler_add(draw_callback, (), 'WINDOW', 'POST_PIXEL')
    else:
        if draw_handler:
            bpy.types.SpaceView3D.draw_handler_remove(draw_handler, 'WINDOW')
            draw_handler = None


def register():
    bpy.utils.register_class(DEBUG_PT_DrawPanel)
    bpy.types.Scene.draw_static_circle = BoolProperty(
        name="Draw Debug Circle",
        description="Enable static 2D circle overlay in viewport",
        default=False,
        update=update_draw_handler,
    )


def unregister():
    global draw_handler
    if draw_handler:
        bpy.types.SpaceView3D.draw_handler_remove(draw_handler, 'WINDOW')
        draw_handler = None

    del bpy.types.Scene.draw_static_circle
    bpy.utils.unregister_class(DEBUG_PT_DrawPanel)


if __name__ == "__main__":
    register()
