import bpy, random, bmesh, time, numpy as np

class VCT_VertexColorFillPanel(bpy.types.Panel):
    bl_label = "Enhanced Vertex Color Tool"
    bl_idname = "OBJECT_PT_vertex_color_tool"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tarmunds Addons'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # layout.prop(scene, "curvature_vertex_channel", expand=True)
        # layout.operator("object.bake_curvature_to_vertex_color", text="Bake Curvature")

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