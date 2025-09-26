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

def fetch_relevant_color_layer(bm, mesh):
    VCTproperties = bpy.context.scene.vct_properties
    if VCTproperties.inspect_enable:
        if mesh in Inspect_meshes:
            return bm.loops.layers.color.get("ChannelChecker")
        else:
            return None
    else:
        return fetch_color_layer(bm, mesh)

def value_to_channel(value, Echannel, current_color, fillgrayscale=False):
    if fillgrayscale:
        return (value, value, value, 1.0)
    else:
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
        if VCTproperties.inspect_enable:
            if mesh in Inspect_meshes:
                color_layer = bm.loops.layers.color.get("ChannelChecker")
            else:
                return {'CANCELLED'}
        else:
            color_layer = fetch_color_layer(bm, mesh)
        
        if VCTproperties.gradient_WS_direction:
            MeshRotation = mesh.matrix_world.to_3x3().normalized()
            LocalDirection = (MeshRotation.inverted() @ mathutils.Vector(direction)).normalized()
        else:
            LocalDirection = mathutils.Vector(direction)

        if not context.mode == 'EDIT_MESH':
            coords_local = [v.co.dot(LocalDirection) for v in bm.verts]
        else:
            coords_local = [v.co.dot(LocalDirection) for v in bm.verts if v.select or not VCTproperties.affect_only_selected]

        min_coord = min(coords_local)
        max_coord = max(coords_local) or (min_coord + 1e-6)

        if min_coord == max_coord:
            max_coord += 1e-6  # Prevent division by zero

        for face in bm.faces:
            for loop in face.loops:
                projection_value = loop.vert.co.dot(LocalDirection)
                value = (projection_value - min_coord) / (max_coord - min_coord)

                if context.mode == 'EDIT_MESH' and VCTproperties.affect_only_selected:
                    if loop.vert.select:
                        loop[color_layer] = value_to_channel(value, Echannel, loop[color_layer], fillgrayscale=True if VCTproperties.inspect_enable else False)
                else:
                    loop[color_layer] = value_to_channel(value, Echannel, loop[color_layer], fillgrayscale=True if VCTproperties.inspect_enable else False)

    
        bmesh_to_object(context, bm, mesh)
    return {'FINISHED'}



def fill_random(context):
    VCTproperties = context.scene.vct_properties
    Echannel = VCTproperties.random_channel
    meshes = fetch_mesh_in_context(context)
    if not meshes: 
        return {'CANCELLED'}
    
    #final writing to channel function
    def write_random_value_to_loops(loops, rand_value):
        for loop in loops:
            if context.mode == 'EDIT_MESH':
                if loop.vert.select or not VCTproperties.affect_only_selected:
                    loop[color_layer] = value_to_channel(rand_value, Echannel, loop[color_layer], fillgrayscale=True if VCTproperties.inspect_enable else False)
            else:
                loop[color_layer] = value_to_channel(rand_value, Echannel, loop[color_layer], fillgrayscale=True if VCTproperties.inspect_enable else False)

    random_per_connected = VCTproperties.random_per_connected
    random_per_uv_island = VCTproperties.random_per_uv_island
    if not random_per_connected and not random_per_uv_island:
        random_values = [0.0] * len(meshes)

        if VCTproperties.random_normalize:
            step = 1.0 / max(len(meshes) - 1, 1)
            random_values = [i * step for i in range(len(meshes))]
            random.shuffle(random_values)

        for mesh, rand_value in zip(meshes, random_values):
            bm = bmesh_from_object(context, mesh)
            color_layer = fetch_relevant_color_layer(bm, mesh)
            if VCTproperties.random_normalize:
                pass  # Use precomputed normalized value
            else:
                rand_value = random.random()

            for face in bm.faces:
                write_random_value_to_loops(face.loops, rand_value)
            bmesh_to_object(context, bm, mesh)
        return {'FINISHED'}
    if random_per_connected:
        for mesh in meshes:
            bm = bmesh_from_object(context, mesh)
            color_layer = fetch_relevant_color_layer(bm, mesh)
            connected_loops_list = fetch_connected_loops(bm)
            random_values = [0.0] * len(connected_loops_list)

            if VCTproperties.random_normalize:
                step = 1.0 / max(len(connected_loops_list) - 1, 1)
                random_values = [i * step for i in range(len(connected_loops_list))]
                random.shuffle(random_values)
            
            for loops, rand_value in zip(connected_loops_list, random_values):
                if VCTproperties.random_normalize:
                    pass  # Use precomputed normalized value
                else:
                    rand_value = random.random()
                write_random_value_to_loops(loops, rand_value)
            bmesh_to_object(context, bm, mesh)
        return {'FINISHED'}
    if random_per_uv_island:
        for mesh in meshes:
            bm = bmesh_from_object(context, mesh)
            color_layer = fetch_relevant_color_layer(bm, mesh)
            uv_island_loops_list = fetch_uv_island_loops(bm)
            random_values = [0.0] * len(uv_island_loops_list)

            if VCTproperties.random_normalize:
                step = 1.0 / max(len(uv_island_loops_list) - 1, 1)
                random_values = [i * step for i in range(len(uv_island_loops_list))]
                random.shuffle(random_values)
            
            for loops, rand_value in zip(uv_island_loops_list, random_values):
                if VCTproperties.random_normalize:
                    pass  # Use precomputed normalized value
                else:
                    rand_value = random.random()
                write_random_value_to_loops(loops, rand_value)
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
                    loop[color_layer] = value_to_channel(value, VCTproperties.inspect_channel, loop[color_layer], fillgrayscale=False)
            
            bm.loops.layers.color.remove(bm.loops.layers.color.get("ChannelChecker"))
            bmesh_to_object(context, bm, mesh)
            mesh.data.color_attributes.active_color = mesh.data.color_attributes["Col"]

    VCTproperties.inspect_enable = False
    Inspect_meshes.clear()

def random_fill_per_connect_component(context):
    VCTproperties = context.scene.vct_properties
    Echannel = VCTproperties.random_channel
    meshes = fetch_mesh_in_context(context)
    if not meshes: 
        return {'CANCELLED'}

def fetch_connected_loops(bm):
    visited = set()
    loops_list = []

    for face in bm.faces:
        for loop in face.loops:
            if loop.index in visited:
                continue

            stack = [loop]
            component = []

            while stack:
                current = stack.pop()
                if current.index in visited:
                    continue

                visited.add(current.index)
                component.append(current)

                # 1) Walk around the same face
                next_loop = current.link_loop_next
                prev_loop = current.link_loop_prev
                if next_loop.index not in visited:
                    stack.append(next_loop)
                if prev_loop.index not in visited:
                    stack.append(prev_loop)

                # 2) Cross the shared edge to neighbouring face(s)
                radial_next = current.link_loop_radial_next
                radial_prev = current.link_loop_radial_prev
                if radial_next is not None and radial_next is not current and radial_next.index not in visited:
                    stack.append(radial_next)
                if radial_prev is not None and radial_prev is not current and radial_prev.index not in visited:
                    stack.append(radial_prev)

            loops_list.append(component)

    return loops_list


def fetch_uv_island_loops(bm, uv_layer=None, eps=1e-6):
    if uv_layer is None:
        uv_layer = bm.loops.layers.uv.active
        if uv_layer is None:
            raise RuntimeError("No active UV layer")

    visited = set()       # store visited FACE indices
    loops_list = []       # list of components; each component is a list of BMLoop

    # helper to compare two (u, v) with tolerance
    def uv_equal(uv1, uv2):
        du = uv1.x - uv2.x
        dv = uv1.y - uv2.y
        return (du * du + dv * dv) <= (eps * eps)

    for face in bm.faces:
        if face.index in visited:
            continue

        stack = [face]
        faces_component = []

        while stack:
            f = stack.pop()
            if f.index in visited:
                continue

            visited.add(f.index)
            faces_component.append(f)

            # map: vertex -> loop on this face (fast UV lookup per vertex)
            f_v2l = {l.vert: l for l in f.loops}

            # try to cross each boundary edge if UVs are welded
            for l in f.loops:
                e = l.edge

                # find the other face(s) around this edge
                for el in e.link_loops:
                    of = el.face
                    if of is f:
                        continue  # same face

                    # need UVs at both edge vertices on both faces
                    vA, vB = e.verts[0], e.verts[1]

                    # loops on current face for vA and vB
                    la = f_v2l.get(vA)
                    lb = f_v2l.get(vB)
                    if la is None or lb is None:
                        continue  # should not happen, but be safe

                    uvA_cur = la[uv_layer].uv
                    uvB_cur = lb[uv_layer].uv

                    # loops on other face for vA and vB
                    of_v2l = {ol.vert: ol for ol in of.loops}
                    ola = of_v2l.get(vA)
                    olb = of_v2l.get(vB)
                    if ola is None or olb is None:
                        continue

                    uvA_other = ola[uv_layer].uv
                    uvB_other = olb[uv_layer].uv

                    # cross only if both endpoints have identical UVs
                    if uv_equal(uvA_cur, uvA_other) and uv_equal(uvB_cur, uvB_other):
                        if of.index not in visited:
                            stack.append(of)

        # convert the collected faces into loops for this UV island
        component = []
        for f in faces_component:
            component.extend(list(f.loops))

        loops_list.append(component)

    return loops_list

