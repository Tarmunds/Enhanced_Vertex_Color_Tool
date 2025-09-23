import bpy

def fetch_view_shading(context):
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    return space.shading
    return None

def fetch_view_lighting(context):
    shading = fetch_view_shading(context)
    if shading:
        return shading.light
    return None

def fetch_view_color_type(context):
    shading = fetch_view_shading(context)
    if shading:
        return shading.color_type
    return None