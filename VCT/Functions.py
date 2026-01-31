import bpy, bmesh, mathutils, random, gpu, math
from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils 

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

def linear_to_srgb(value):
    if value <= 0.0031308:
        return 12.92 * value
    else:
        return 1.055 * (value ** (1.0 / 2.4)) - 0.055
    
def linear_color_to_srgb(color):
    return mathutils.Color((
        linear_to_srgb(color.r),
        linear_to_srgb(color.g),
        linear_to_srgb(color.b)
    ))
    
def _unique_attr_name(ca, base: str) -> str:
    """Return a name not used by any attribute in this mesh."""
    existing = {a.name for a in ca}
    if base not in existing:
        return base
    i = 1
    while True:
        candidate = f"{base}_{i:03d}"
        if candidate not in existing:
            return candidate
        i += 1

#------verify color layer , or create one, and set it to active render layer------
def fetch_color_layer(bm, mesh, context):
    ca = mesh.data.color_attributes

    if mesh.data.color_attributes:
        if not ca.active_color:
            ca.active_color = mesh.data.color_attributes[0]
        keys = ca.active_color.name
        layer = bm.loops.layers.color.get(keys)
        layer_source = ca.get(keys)
        if layer_source.data_type != 'BYTE_COLOR' or layer_source.domain != 'CORNER':
            bm.free()
            wasinedit = False
            if context.mode == 'EDIT_MESH' or context.mode == 'EDIT':  # support both
                bpy.ops.object.mode_set(mode='OBJECT')
                wasinedit = True
            bpy.ops.geometry.color_attribute_convert(domain='CORNER', data_type='BYTE_COLOR')
            bm = bmesh_from_object(context, mesh)
            if wasinedit:
                bpy.ops.object.mode_set(mode='EDIT')
            keys = ca.active_color.name
            layer = bm.loops.layers.color.get(keys)
            layer_source = ca.get(keys)
        
    else:
        layer = bm.loops.layers.color.verify()
        bmesh_to_object(context, bm, mesh)
        bm = bmesh_from_object(context, mesh)

    ca.active_color = ca.get(layer.name)
    return layer, bm

def fetch_relevant_color_layer(bm, mesh, context):
    VCTproperties = bpy.context.scene.vct_properties
    if VCTproperties.inspect_enable:
        if mesh in Inspect_meshes:
            return bm.loops.layers.color.get("ChannelChecker"), bm
        else:
            return None, bm
    else:
        return fetch_color_layer(bm, mesh, context)



#---- Main Functions ----#

def value_to_channel(value, Echannel, current_color, fillgrayscale=False):
    VCTproperties = bpy.context.scene.vct_properties
    if fillgrayscale:
        return (value, value, value, 1.0)
    else:
        if VCTproperties.Bsrgb:
            value = linear_to_srgb(value)
        return {
            'R': (value, current_color.y, current_color.z, current_color.w),
            'G': (current_color.x, value, current_color.z, current_color.w),
            'B': (current_color.x, current_color.y, value, current_color.w),
            'A': (current_color.x, current_color.y, current_color.z, value),
        }[Echannel]

def fill_vertex_color(context, overide_color=None):
    VCTproperties = context.scene.vct_properties
    color = overide_color if overide_color else VCTproperties.fill_color
    if VCTproperties.Bsrgb:
        alpha = color[3]
        color = linear_color_to_srgb(mathutils.Color((color[0], color[1], color[2])))
        color = (color.r, color.g, color.b, alpha)

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
            color_layer, bm = fetch_color_layer(bm, mesh, context)

        for face in bm.faces:
            for loop in face.loops:
                if context.mode == 'EDIT_MESH':
                    if should_affect_loop_editmode(VCTproperties, face, loop):
                        loop[color_layer] = color
                else:
                    loop[color_layer] = color

        bmesh_to_object(context, bm, mesh)
    return {'FINISHED'}

def fill_channel(context):
    VCTproperties = context.scene.vct_properties
    Echannel = VCTproperties.fill_1channel
    value = VCTproperties.fill_1channel_value
    if VCTproperties.Bsrgb:
        value = linear_to_srgb(value)
    meshes = fetch_mesh_in_context(context)
    if not meshes: 
        return {'CANCELLED'}
    for mesh in meshes:
        bm = bmesh_from_object(context, mesh)
        color_layer, bm = fetch_relevant_color_layer(bm, mesh, context)

        for face in bm.faces:
            for loop in face.loops:
                if context.mode == 'EDIT_MESH':
                    if loop.vert.select or not VCTproperties.affect_only_selected:
                        loop[color_layer] = value_to_channel(value, Echannel, loop[color_layer], fillgrayscale=True if VCTproperties.inspect_enable else False)
                else:
                    loop[color_layer] = value_to_channel(value, Echannel, loop[color_layer], fillgrayscale=True if VCTproperties.inspect_enable else False)
        bmesh_to_object(context, bm, mesh)

    return {'FINISHED'}

def should_affect_loop_editmode(vct_props, face, loop):
    if not vct_props.affect_only_selected:
        return True

    if vct_props.Bedit_face_mode:
        return face.select
    else:
        return loop.vert.select

def fill_gradient(context):
    VCTproperties = context.scene.vct_properties
    Echannel = VCTproperties.gradient_channel
    use_global = VCTproperties.gradient_global
    Edirection = VCTproperties.gradient_direction
    InvertGradient = VCTproperties.gradient_invert
    direction = {
        'X': (1, 0, 0),
        'Y': (0, 1, 0),
        'Z': (0, 0, 1)
    }[Edirection]
    meshes = fetch_mesh_in_context(context)
    if not meshes: 
        return {'CANCELLED'}

    if use_global:  # case using global gradient

        if VCTproperties.gradient_WS_direction:
            # Always use pure world axis when WS mode is on
            worldDirection = mathutils.Vector(direction)
        elif VCTproperties.gradient_direction_inherit_from_active and context.active_object:
            R_active = context.active_object.matrix_world.to_3x3().normalized()
            worldDirection = (R_active @ mathutils.Vector(direction)).normalized()
        else:
            worldDirection = mathutils.Vector(direction)

        global_min = float('inf')
        global_max = float('-inf')

        # Scan all meshes to find global min/max projections in WORLD space
        for mesh in meshes:
            bm = bmesh_from_object(context, mesh)

            if context.mode == 'EDIT_MESH':
                verts_iter = (v for v in bm.verts if v.select or not VCTproperties.affect_only_selected)
            else:
                verts_iter = bm.verts

            mw = mesh.matrix_world
            for v in verts_iter:
                proj = (mw @ v.co).dot(worldDirection)
                if proj < global_min: global_min = proj
                if proj > global_max: global_max = proj

        if not (global_max > global_min):
            global_max = global_min + 1e-6
      
    for mesh in meshes:
        # get bm mesh and loop color layer
        bm = bmesh_from_object(context, mesh)
        if VCTproperties.inspect_enable:
            if mesh in Inspect_meshes:
                color_layer = bm.loops.layers.color.get("ChannelChecker")
            else:
                return {'CANCELLED'}
        else:
            color_layer, bm = fetch_color_layer(bm, mesh, context)
        
        if use_global:
            mw = mesh.matrix_world
            for face in bm.faces:
                for loop in face.loops:
                    if context.mode == 'EDIT_MESH' and VCTproperties.affect_only_selected and not loop.vert.select:
                        continue
                    projection_value = (mw @ loop.vert.co).dot(worldDirection)
                    value = (projection_value - global_min) / (global_max - global_min)
                    if InvertGradient:
                        value = 1.0 - value
                    loop[color_layer] = value_to_channel(value, Echannel, loop[color_layer], fillgrayscale=True if VCTproperties.inspect_enable else False)
        else:
            # calculate local direction if needed
            if VCTproperties.gradient_WS_direction:
                MeshRotation = mesh.matrix_world.to_3x3().normalized()
                LocalDirection = (MeshRotation.inverted() @ mathutils.Vector(direction)).normalized()

            elif VCTproperties.gradient_direction_inherit_from_active and context.active_object:
                R_active = context.active_object.matrix_world.to_3x3().normalized()
                R_mesh_inv = mesh.matrix_world.to_3x3().normalized().inverted()
                D_world = (R_active @ mathutils.Vector(direction)).normalized()
                LocalDirection = (R_mesh_inv @ D_world).normalized()

            else:
                LocalDirection = mathutils.Vector(direction)

            # gather all vertex coordinates in the chosen direction
            if not context.mode == 'EDIT_MESH':
                coords_local = [v.co.dot(LocalDirection) for v in bm.verts]
            else:
                coords_local = [v.co.dot(LocalDirection) for v in bm.verts if v.select or not VCTproperties.affect_only_selected]

            if not coords_local:
                bmesh_to_object(context, bm, mesh)
                continue

            min_coord = min(coords_local)
            max_coord = max(coords_local) or (min_coord + 1e-6)

            if min_coord == max_coord:
                max_coord += 1e-6  # Prevent division by zero

            # fill gradient
            for face in bm.faces:
                for loop in face.loops:
                    projection_value = loop.vert.co.dot(LocalDirection)
                    value = (projection_value - min_coord) / (max_coord - min_coord)
                    if InvertGradient:
                        value = 1.0 - value

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
            color_layer, bm = fetch_relevant_color_layer(bm, mesh, context)
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
            color_layer, bm = fetch_relevant_color_layer(bm, mesh, context)
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
            color_layer, bm = fetch_relevant_color_layer(bm, mesh, context)
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
            color_layer, bm = fetch_color_layer(bm, mesh, context)

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
            color_layer, bm = fetch_color_layer(bm, mesh, context)
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

def clear_channel(context, value):
    VCTproperties = context.scene.vct_properties
    Echannel = VCTproperties.clear_channel
    meshes = fetch_mesh_in_context(context)
    if not meshes:
        return {'CANCELLED'}
    for mesh in meshes:
        bm = bmesh_from_object(context, mesh)
        color_layer, bm = fetch_relevant_color_layer(bm, mesh, context)

        for face in bm.faces:
            for loop in face.loops:
                if context.mode == 'EDIT_MESH':
                    if loop.vert.select or not VCTproperties.affect_only_selected:
                        loop[color_layer] = value_to_channel(value, Echannel, loop[color_layer], fillgrayscale=True if VCTproperties.inspect_enable else False)
                else:
                    loop[color_layer] = value_to_channel(value, Echannel, loop[color_layer], fillgrayscale=True if VCTproperties.inspect_enable else False)
        bmesh_to_object(context, bm, mesh)
    return {'FINISHED'}

def switch_channel(context):
    VCTproperties = context.scene.vct_properties
    Echannel_source = VCTproperties.switch_source_channel
    Echannel_target = VCTproperties.switch_target_channel
    if Echannel_source == Echannel_target:
        return {'CANCELLED'}
    
    def switch_values(loop_color):
        # coerce to a plain tuple
        try:
            r, g, b, a = loop_color.x, loop_color.y, loop_color.z, loop_color.w
        except AttributeError:
            r, g, b, a = loop_color

        vals = {'R': r, 'G': g, 'B': b, 'A': a}
        vals[Echannel_source], vals[Echannel_target] = vals[Echannel_target], vals[Echannel_source]
        return (vals['R'], vals['G'], vals['B'], vals['A'])

    meshes = fetch_mesh_in_context(context)
    if not meshes:
        return {'CANCELLED'}
    for mesh in meshes:
        bm = bmesh_from_object(context, mesh)
        color_layer, bm = fetch_relevant_color_layer(bm, mesh, context)

        for face in bm.faces:
            for loop in face.loops:
                if context.mode == 'EDIT_MESH':
                    if loop.vert.select or not VCTproperties.affect_only_selected:
                        loop[color_layer] = switch_values(loop[color_layer])
                else:
                    loop[color_layer] = switch_values(loop[color_layer])

        bmesh_to_object(context, bm, mesh)
    return {'FINISHED'}


def bake_ao_to_vertex_color(context):
    scene = context.scene
    VCTproperties = scene.vct_properties
    texture_size_map = {
        '256': 256, '512': 512, '1024': 1024, '2048': 2048, '4096': 4096,
    }[VCTproperties.ao_texture_size]
    Echannel = VCTproperties.ao_vertex_channel
    fill_grayscale = True if VCTproperties.inspect_enable else False

    VCTproperties.ao_percent = 0.0
    VCTproperties.ao_show_progress = True

    meshes = fetch_mesh_in_context(context)
    if not meshes:
        return {'CANCELLED'}



    # Snapshot current selection & mode so we can restore it later
    prev_mode = bpy.context.mode
    prev_engine = scene.render.engine
    view_layer = context.view_layer
    prev_active = view_layer.objects.active
    prev_selected = [obj for obj in context.selected_objects]

    # Ensure Cycles + object mode for baking
    scene.render.engine = 'CYCLES'
    if prev_mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

    try:
        for mesh in meshes:
            # Skip invalid UV index early
            uv_index = VCTproperties.ao_uv_index
            if uv_index >= len(mesh.data.uv_layers):
                print(f"Skipping {mesh.name}: UV index {uv_index} does not exist")
                continue

            # Isolate current object selection to avoid "No active image" across others
            for o in prev_selected:
                o.select_set(False)
            mesh.select_set(True)
            view_layer.objects.active = mesh

            # Create temp image + material, make Image Texture node active
            temp_image = bpy.data.images.new(
                "AO_Temp", width=texture_size_map, height=texture_size_map, alpha=False
            )
            temp_material = bpy.data.materials.new(name="AO_Temp_Material")
            temp_material.use_nodes = True
            nt = temp_material.node_tree

            # Ensure there is at least one output so the node tree is valid (defensive)
            if not any(n.type == 'OUTPUT_MATERIAL' for n in nt.nodes):
                out = nt.nodes.new("ShaderNodeOutputMaterial")
                out.location = (300, 0)

            tex_node = nt.nodes.new("ShaderNodeTexImage")
            tex_node.image = temp_image
            # Important: make the image node the active one for baking
            for n in nt.nodes: n.select = False
            tex_node.select = True
            nt.nodes.active = tex_node

            # Remember original active material and slot index
            original_active_mat = mesh.active_material
            original_active_slot = mesh.active_material_index

            # Assign temp mat (make sure the object actually uses it)
            if mesh.data.materials:
                if original_active_slot < 0:
                    mesh.data.materials.append(temp_material)
                    mesh.active_material_index = len(mesh.data.materials) - 1
                else:
                    mesh.data.materials[mesh.active_material_index] = temp_material
            else:
                mesh.data.materials.append(temp_material)
                mesh.active_material_index = 0
            mesh.active_material = temp_material

            # Make the correct UV the active one for baking
            mesh.data.uv_layers.active_index = uv_index
            uv_layer_name = mesh.data.uv_layers[uv_index].name

            # Bake settings
            scene.cycles.bake_type = 'AO'
            scene.render.bake.use_pass_direct = False
            scene.render.bake.use_pass_indirect = False
            scene.render.bake.use_pass_color = True
            scene.render.bake.target = 'IMAGE_TEXTURES'  # explicit

            # Try baking this single object only
            try:
                bpy.ops.object.bake(type='AO')
            except RuntimeError as e:
                print(f"Baking failed for {mesh.name}: {e}")
                # Clean up safely and move to next object
                if temp_material and temp_material.users == 0:
                    try: bpy.data.materials.remove(temp_material)
                    except Exception: pass
                if temp_image and temp_image.users == 0:
                    try: bpy.data.images.remove(temp_image)
                    except Exception: pass
                # Restore original material if we had one
                if original_active_mat:
                    mesh.active_material = original_active_mat
                    if 0 <= original_active_slot < len(mesh.data.materials):
                        mesh.data.materials[mesh.active_material_index] = original_active_mat
                continue

            # ---- Transfer baked AO to vertex colors ----
            bm = bmesh_from_object(context, mesh)
            color_layer, bm = fetch_relevant_color_layer(bm, mesh, context)
            bm_uv_layer = bm.loops.layers.uv.get(uv_layer_name) or bm.loops.layers.uv.active

            width, height = temp_image.size
            pixels = temp_image.pixels[:]  # RGBA flat array

            def sample_ao(u, v):
                px = min(max(int(u * width), 0), width - 1)
                py = min(max(int(v * height), 0), height - 1)
                idx = (py * width + px) * 4
                return pixels[idx]  # R channel

            affect_only_selected = getattr(VCTproperties, "affect_only_selected", False)
            edit_mode = (prev_mode == 'EDIT_MESH')  # we switched to OBJECT for bake

            for face in bm.faces:
                for loop in face.loops:
                    if edit_mode and affect_only_selected and not loop.vert.select:
                        continue
                    uv = loop[bm_uv_layer].uv
                    ao_val = sample_ao(uv.x, uv.y)
                    current = loop[color_layer]
                    loop[color_layer] = value_to_channel(
                        ao_val, Echannel, current, fillgrayscale=fill_grayscale
                    )

            bmesh_to_object(context, bm, mesh)

            #update percent
            VCTproperties.ao_percent = round((meshes.index(mesh) + 1) / len(meshes) * 100, 2)

            # Cleanup temp data and restore original material
            # Put back original material if there was one, otherwise remove temp slot
            if original_active_mat:
                mesh.active_material = original_active_mat
                if 0 <= original_active_slot < len(mesh.data.materials):
                    mesh.data.materials[mesh.active_material_index] = original_active_mat
            else:
                # If we created a new slot, remove it
                if temp_material in mesh.data.materials.values():
                    idx = [i for i, m in enumerate(mesh.data.materials) if m == temp_material]
                    for i in idx[::-1]:
                        mesh.active_material_index = i
                        bpy.ops.object.material_slot_remove()

            # Remove temp datablocks if not used elsewhere
            try:
                if temp_material and temp_material.users == 0:
                    bpy.data.materials.remove(temp_material)
            except Exception:
                pass
            try:
                if temp_image and temp_image.users == 0:
                    bpy.data.images.remove(temp_image)
            except Exception:
                pass

        return {'FINISHED'}

    finally:
        # Restore engine, selection, active, and mode
        VCTproperties.ao_show_progress = False
        scene.render.engine = prev_engine
        for o in context.selected_objects:
            o.select_set(False)
        for o in prev_selected:
            o.select_set(True)
        view_layer.objects.active = prev_active
        if prev_mode != bpy.context.mode:
            try:
                bpy.ops.object.mode_set(mode=prev_mode, toggle=False)
            except Exception:
                pass

def invert_vertex_colors(context):
    VCTproperties = context.scene.vct_properties
    meshes = fetch_mesh_in_context(context)
    Echannel = VCTproperties.clear_channel
    if not meshes:
        return {'CANCELLED'}

    for mesh in meshes:
        bm = bmesh_from_object(context, mesh)
        color_layer, bm = fetch_relevant_color_layer(bm, mesh, context)

        for face in bm.faces:
            for loop in face.loops:
                if context.mode == 'EDIT_MESH':
                    if loop.vert.select or not VCTproperties.affect_only_selected:
                        source_value = getattr(loop[color_layer], {'R': 'x', 'G': 'y', 'B': 'z', 'A': 'w'}[Echannel])
                        loop[color_layer] = value_to_channel(1.0 - source_value, Echannel, loop[color_layer], fillgrayscale=True if VCTproperties.inspect_enable else False)
                else:
                    source_value = getattr(loop[color_layer], {'R': 'x', 'G': 'y', 'B': 'z', 'A': 'w'}[Echannel])
                    loop[color_layer] = value_to_channel(1.0 - source_value, Echannel, loop[color_layer], fillgrayscale=True if VCTproperties.inspect_enable else False)

        bmesh_to_object(context, bm, mesh)

    return {'FINISHED'}

#---- GPU Functions ----#

def draw_2d(self, context):
    VCTproperties = context.scene.vct_properties
    if not self.is_drawing or not self.start or not self.current:
        return

    x1, y1 = self.start
    x2, y2 = self.current

    if VCTproperties.inspect_enable:
        channel_color = (1, 0, 0, 1.0)
    else:
        channel_color = {
            'R': (1, 0, 0, 1.0),
            'G': (0, 1, 0, 1.0),
            'B': (0, 0, 1, 1.0),
            'A': (1, 1, 1, 1.0),
        }[context.scene.vct_properties.gradient_channel]

    if self.shader is None:
        self.shader = gpu.shader.from_builtin("SMOOTH_COLOR")

    if not self.Bcircle:
        coords = [(x1, y1), (x2, y2)]
        primitive = 'LINES'
        colors = [ (0.0, 0.0, 0.0, 1.0), channel_color]

        batch = batch_for_shader(self.shader, primitive, {"pos": coords, "color": colors})
        gpu.state.line_width_set(2.0)
        self.shader.bind()
        batch.draw(self.shader)

    else:
        dx, dy = x2 - x1, y2 - y1
        radius = math.sqrt(dx*dx + dy*dy)
        segments = 64
        circle_coords = [
            (x1 + math.cos(2*math.pi*i/segments)*radius,
             y1 + math.sin(2*math.pi*i/segments)*radius)
            for i in range(segments + 1)
        ]
        circle_colors = [channel_color] * len(circle_coords)

        # batch for circle
        circle_batch = batch_for_shader(self.shader, 'LINE_STRIP',
                                        {"pos": circle_coords, "color": circle_colors})

        # batch for single point at start
        point_batch = batch_for_shader(self.shader, 'POINTS',
                                       {"pos": [(x1, y1)], "color": [channel_color]})

        gpu.state.blend_set('ALPHA')

        # Draw circle
        gpu.state.line_width_set(2.0)
        self.shader.bind()
        circle_batch.draw(self.shader)

        # Draw the single point
        gpu.state.point_size_set(8.0)   # size in pixels
        point_batch.draw(self.shader)

        gpu.state.blend_set('NONE')


def add_handler(self, context):
    if self.handle is None:
        self.handle = bpy.types.SpaceView3D.draw_handler_add(
            draw_2d, (self, context), 'WINDOW', 'POST_PIXEL'
        )

def remove_handler(self):
    if self.handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(self.handle, 'WINDOW')
        self.handle = None
        self.shader = None

def set_no_active_trace(context):
    for i in context.scene.vct_properties.trace_gradient_active:
        context.scene.vct_properties.trace_gradient_active[i] = False

def trace_gradient_modal(self, context, event):
        # ask the area to redraw so our _draw_2d runs smoothly
        if context.area:
            context.area.tag_redraw()

        if context.area and context.area.type != 'VIEW_3D':
            remove_handler(self)
            self.report({'INFO'}, "Not in 3D View")
            set_no_active_trace(context)
            return {'CANCELLED'}

        if event.type in {'ESC', 'RIGHTMOUSE'}:
            self.is_drawing = False
            remove_handler(self)
            self.report({'INFO'}, "Cancelled")
            set_no_active_trace(context)
            return {'CANCELLED'}

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.start = (event.mouse_region_x, event.mouse_region_y)
            self.current = self.start
            self.is_drawing = True
            return {'RUNNING_MODAL'}

        if event.type == 'MOUSEMOVE' and self.is_drawing:
            self.current = (event.mouse_region_x, event.mouse_region_y)
            return {'RUNNING_MODAL'}

        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE' and self.is_drawing:
            end = (event.mouse_region_x, event.mouse_region_y)
            self.end = end
            self.is_drawing = False
            remove_handler(self)

            if self.Bcircle:
                # radial: center at start, radius from start->end
                cx, cy = self.start
                ex, ey = end
                radius = ((ex - cx) ** 2 + (ey - cy) ** 2) ** 0.5
                result = fill_gradient_camera_radial(
                    context,
                    self.start, radius,
                    region=context.region, rv3d=context.region_data
                )
            else:
                # linear along the traced line
                result = fill_gradient_camera_space(
                    context,
                    self.start, end,
                    region=context.region, rv3d=context.region_data
                )

            self.report({'INFO'}, "Trace Gradient applied" if result == {'FINISHED'} else "Trace Gradient failed")
            set_no_active_trace(context)
            return result
        
        return {'RUNNING_MODAL'}

def fill_gradient_camera_space(context, start_xy, end_xy, region=None, rv3d=None):
    VCTproperties = context.scene.vct_properties
    Echannel = VCTproperties.gradient_channel
    InvertGradient = VCTproperties.gradient_invert

    # Validate the line
    x1, y1 = start_xy
    x2, y2 = end_xy
    dx, dy = (x2 - x1), (y2 - y1)
    length_sq = dx*dx + dy*dy
    if length_sq <= 1e-12:
        return {'CANCELLED'}

    # Fallback to the active 3D view's region/rv3d if not provided
    if region is None or rv3d is None:
        area_3d = None
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area_3d = area
                break
        if area_3d is None:
            return {'CANCELLED'}
        region = next((r for r in area_3d.regions if r.type == 'WINDOW'), None)
        rv3d = area_3d.spaces.active.region_3d if area_3d.spaces.active else None
        if region is None or rv3d is None:
            return {'CANCELLED'}

    line_origin = mathutils.Vector((x1, y1))
    line_dir = mathutils.Vector((dx, dy))
    line_dir_n = line_dir / math.sqrt(length_sq)

    meshes = fetch_mesh_in_context(context)
    if not meshes:
        return {'CANCELLED'}

    for mesh in meshes:
        bm = bmesh_from_object(context, mesh)

        # choose the correct color layer (respects Inspect mode)
        color_layer, bm = fetch_relevant_color_layer(bm, mesh, context)
        if color_layer is None:
            bmesh_to_object(context, bm, mesh)
            continue

        mw = mesh.matrix_world
        affect_only_selected = getattr(VCTproperties, "affect_only_selected", False)
        edit_mode = (context.mode == 'EDIT_MESH')

        for face in bm.faces:
            for loop in face.loops:
                if edit_mode and affect_only_selected and not loop.vert.select:
                    continue

                world_co = mw @ loop.vert.co
                # Project to 2D (region) coordinates
                p2d = view3d_utils.location_3d_to_region_2d(region, rv3d, world_co)
                if p2d is None:
                    continue

                # Project this point onto the traced line to get normalized t in [0..1]
                v = mathutils.Vector((p2d.x, p2d.y)) - line_origin
                t = v.dot(line_dir_n) / math.sqrt(length_sq) * math.sqrt(length_sq)  # collapses to v.dot(n)
                # Because n is unit along the line direction, t is in pixels from start; normalize by line length:
                t = v.dot(line_dir) / length_sq  # equivalent and clearer
                t = max(0.0, min(1.0, t))

                value = 1.0 - t if InvertGradient else t
                loop[color_layer] = value_to_channel(
                    value, Echannel, loop[color_layer],
                    fillgrayscale=True if VCTproperties.inspect_enable else False
                )

        bmesh_to_object(context, bm, mesh)

    return {'FINISHED'}


def fill_gradient_camera_radial(context, center_xy, radius_px, region=None, rv3d=None):
    VCTproperties = context.scene.vct_properties
    Echannel = VCTproperties.gradient_channel
    InvertGradient = VCTproperties.gradient_invert

    if radius_px <= 1e-6:
        return {'CANCELLED'}

    # Fallback to active 3D view region/rv3d if not provided
    if region is None or rv3d is None:
        area_3d = None
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area_3d = area
                break
        if area_3d is None:
            return {'CANCELLED'}
        region = next((r for r in area_3d.regions if r.type == 'WINDOW'), None)
        rv3d = area_3d.spaces.active.region_3d if area_3d.spaces.active else None
        if region is None or rv3d is None:
            return {'CANCELLED'}

    c = mathutils.Vector(center_xy)

    meshes = fetch_mesh_in_context(context)
    if not meshes:
        return {'CANCELLED'}

    for mesh in meshes:
        bm = bmesh_from_object(context, mesh)
        color_layer, bm = fetch_relevant_color_layer(bm, mesh, context)
        if color_layer is None:
            bmesh_to_object(context, bm, mesh)
            continue

        mw = mesh.matrix_world
        affect_only_selected = getattr(VCTproperties, "affect_only_selected", False)
        edit_mode = (context.mode == 'EDIT_MESH')

        for face in bm.faces:
            for loop in face.loops:
                if edit_mode and affect_only_selected and not loop.vert.select:
                    continue

                world_co = mw @ loop.vert.co
                p2d = view3d_utils.location_3d_to_region_2d(region, rv3d, world_co)
                if p2d is None:
                    continue

                d = (mathutils.Vector((p2d.x, p2d.y)) - c).length
                t = max(0.0, min(1.0, d / radius_px))  # 0 at center, 1 at radius
                value = t if InvertGradient else 1.0 - t

                loop[color_layer] = value_to_channel(
                    value, Echannel, loop[color_layer],
                    fillgrayscale=True if VCTproperties.inspect_enable else False
                )

        bmesh_to_object(context, bm, mesh)

    return {'FINISHED'}

