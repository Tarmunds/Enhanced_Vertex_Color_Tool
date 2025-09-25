import bpy, bmesh, mathutils, random


#---- Utility Functions ----#

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

def fetch_mesh_in_context(context):
    if context.mode == 'OBJECT':
        return [obj for obj in context.selected_objects if obj.type == 'MESH']
    elif context.mode == 'EDIT_MESH':
        return [obj for obj in context.objects_in_mode if obj.type == 'MESH']
    return {'CANCELLED'}

#setup bm based on edit mode
def bmesh_from_object(context, mesh):
    if context.mode == 'EDIT_MESH':
        bm = bmesh.from_edit_mesh(mesh.data)
    else:
        bm = bmesh.new()
        bm.from_mesh(mesh.data)
    return bm

#restor bm to meshdata
def bmesh_to_object(context, bm, mesh):
    if context.mode == 'EDIT_MESH':
        bmesh.update_edit_mesh(mesh.data)
        mesh.data.update() 
    else:
        bm.to_mesh(mesh.data)
        mesh.data.update() 
        bm.free()

#verify color layer , or create one, and set it to active render layer
def fetch_color_layer(bm, mesh):
    color_layer = bm.loops.layers.color.verify()
    mesh.data.color_attributes.active_color = mesh.data.color_attributes["Col"] if mesh.data.color_attributes.get("Col") else mesh.data.color_attributes.new(name="Col", type='BYTE_COLOR', domain='CORNER')
    return color_layer

def value_to_channel(value, Echannel, current_color):
    return {
        'R': (value, current_color.y, current_color.z, current_color.w),
        'G': (current_color.x, value, current_color.z, current_color.w),
        'B': (current_color.x, current_color.y, value, current_color.w),
        'A': (current_color.x, current_color.y, current_color.z, value),
    }[Echannel]

#---- Main Functions ----#

def fill_vertex_color(context, overide_color=None):
    VCTproperties = context.scene.vct_properties
    color = overide_color if overide_color else VCTproperties.fill_color
    meshes = fetch_mesh_in_context(context)
    if not meshes:
        return {'CANCELLED'}

    for mesh in meshes:
        bm = bmesh_from_object(context, mesh)
        if VCTproperties.inspect_enable:
            if mesh in Inspect_meshes:
                color_layer = bm.loops.layers.color.get("ChannelChecker")
            else:
                return {'CANCELLED'}
        else:
            color_layer = fetch_color_layer(bm, mesh)

        for face in bm.faces:
            for loop in face.loops:
                if context.mode == 'EDIT_MESH':
                    if loop.vert.select or not VCTproperties.affect_only_selected:
                        loop[color_layer] = color
                else:
                    loop[color_layer] = color

        bmesh_to_object(context, bm, mesh)

    return {'FINISHED'}

def fill_gradient(context):
    VCTproperties = context.scene.vct_properties
    Echannel = VCTproperties.gradient_channel

    Edirection = VCTproperties.gradient_direction
    direction = {
        'X': (1, 0, 0),
        'Y': (0, 1, 0),
        'Z': (0, 0, 1)
    }[Edirection]

    meshes = fetch_mesh_in_context(context)
    if not meshes: 
        return {'CANCELLED'}
    
    for mesh in meshes:
        bm = bmesh_from_object(context, mesh)
        color_layer = fetch_color_layer(bm, mesh)
        
        if VCTproperties.gradient_WS_direction:
            MeshRotation = mesh.matrix_world.to_3x3().normalized()
            direction = (MeshRotation.inverted() @ mathutils.Vector(direction)).normalized()

        coords_local = [v.co.dot(direction) for v in bm.verts]
        min_coord = min(coords_local)
        max_coord = max(coords_local) or (min_coord + 1e-6)

        if min_coord == max_coord:
            max_coord += 1e-6  # Prevent division by zero

        for face in bm.faces:
            for loop in face.loops:
                projection_value = loop.vert.co.dot(direction)
                value = (projection_value - min_coord) / (max_coord - min_coord)
                loop[color_layer] = value_to_channel(value, Echannel, loop[color_layer])
    
        bmesh_to_object(context, bm, mesh)



def fill_random(context):
    VCTproperties = context.scene.vct_properties
    Echannel = VCTproperties.random_channel
    meshes = fetch_mesh_in_context(context)
    random_values = [0.0] * len(meshes)
    if not meshes: 
        return {'CANCELLED'}
    
    if VCTproperties.random_normalize:
        step = 1.0 / max(len(meshes) - 1, 1)
        random_values = [i * step for i in range(len(meshes))]
        random.shuffle(random_values)

    for mesh, rand_value in zip(meshes, random_values):
        bm = bmesh_from_object(context, mesh)
        color_layer = fetch_color_layer(bm, mesh)
        if VCTproperties.random_normalize:
            pass  # Use precomputed normalized value
        else:
            rand_value = random.random()

        for face in bm.faces:
            for loop in face.loops:
                if context.mode == 'EDIT_MESH':
                    if loop.vert.select or not VCTproperties.affect_only_selected:
                        loop[color_layer] = value_to_channel(rand_value, Echannel, loop[color_layer])
                else:
                    loop[color_layer] = value_to_channel(rand_value, Echannel, loop[color_layer])

        bmesh_to_object(context, bm, mesh)
    return {'FINISHED'}


Inspect_meshes = set() #container of meshes being inspected

def inspect_color_channel(context):

    VCTproperties = context.scene.vct_properties
    Echannel = VCTproperties.inspect_channel
    meshes = fetch_mesh_in_context(context)

    if VCTproperties.inspect_enable:
        remove_inspector(context, keep_data=True)
        return {'FINISHED'}
    
    if not meshes: 
        return {'CANCELLED'}
    
    Inspect_meshes.clear()
    Inspect_meshes.update(meshes)

    if not VCTproperties.inspect_enable:
        for mesh in meshes:
            bm = bmesh_from_object(context, mesh)
            color_layer = fetch_color_layer(bm, mesh)

            bm_channel_checker = bm.loops.layers.color.new("ChannelChecker")

            for face in bm.faces:
                for loop in face.loops:
                    value = getattr(loop[color_layer], {'R': 'x', 'G': 'y', 'B': 'z', 'A': 'w'}[Echannel])
                    loop[bm_channel_checker] = (value, value, value, 1.0)

            bmesh_to_object(context, bm, mesh)
            mesh.data.color_attributes.active_color = mesh.data.color_attributes["ChannelChecker"] 
        VCTproperties.inspect_enable = True
        return {'FINISHED'}



def remove_inspector(context, keep_data=True):
    VCTproperties = context.scene.vct_properties

    for mesh in Inspect_meshes:
        if not keep_data:
            mesh.data.color_attributes.remove(mesh.data.color_attributes.get("ChannelChecker"))
            bm = bmesh_from_object(context, mesh)
            color_layer = fetch_color_layer(bm, mesh)
            bmesh_to_object(context, bm, mesh)
        else:
            bm = bmesh_from_object(context, mesh)
            check_color_layer = bm.loops.layers.color.get("ChannelChecker")
            color_layer = bm.loops.layers.color.get("Col") if bm.loops.layers.color.get("Col") else bm.loops.layers.color.verify()
            
            for face in bm.faces:
                for loop in face.loops:
                    value = loop[check_color_layer].x  # Since it's grayscale, R=G=B
                    loop[color_layer] = value_to_channel(value, VCTproperties.inspect_channel, loop[color_layer])
            
            bm.loops.layers.color.remove(bm.loops.layers.color.get("ChannelChecker"))
            bmesh_to_object(context, bm, mesh)
            mesh.data.color_attributes.active_color = mesh.data.color_attributes["Col"]

    VCTproperties.inspect_enable = False
    Inspect_meshes.clear()


            


