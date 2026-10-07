"""Join many small mesh objects into one per material look, in world space.

Shared by blender_scene.py (the ~95k objects the VRML importer makes per half)
and export_web.py (the unmerged single-key scene).
"""
import bpy


def merge_by_material(objs):
    """Rebuild the importer's ~95k small objects as one mesh per material.

    Importing the second half next to 95k loose objects took over 30 min,
    and bpy.ops.object.join() over them stalled for as long again. Reading
    the world-space vertices with foreach_get and writing one mesh per
    material takes seconds."""
    import numpy as np
    # the importer makes ~one material per VRML shape (1839 for one half), so
    # group by what the material looks like, not by the material itself; 3
    # decimals, since the display face (0.100) and switch housing (0.098) differ by 0.002
    def look(m):
        if not m:
            return None
        if m.use_nodes and m.node_tree.nodes.get('Principled BSDF'):
            b = m.node_tree.nodes['Principled BSDF']
            col = tuple(round(c, 3) for c in b.inputs['Base Color'].default_value[:3])
            # the role too: after materials.apply() the case and the stem share a
            # colour but not a roughness, and must not merge into one material
            return (m.get('pk_role'),) + col + (round(b.inputs['Alpha'].default_value, 3),)
        return tuple(round(c, 3) for c in m.diffuse_color)
    groups, first = {}, {}
    for o in objs:
        k = look(o.active_material)
        first.setdefault(k, o.active_material)
        groups.setdefault(first[k], []).append(o)
    merged = []
    for mat, group in groups.items():
        verts, loops, sizes, base = [], [], [], 0
        for o in group:
            me = o.data
            n = len(me.vertices)
            if n == 0 or len(me.polygons) == 0:
                continue
            co = np.empty(n * 3, dtype=np.float32)
            me.vertices.foreach_get('co', co)
            co = co.reshape(-1, 3)
            mw = np.array(o.matrix_world, dtype=np.float32)
            verts.append(co @ mw[:3, :3].T + mw[:3, 3])
            vi = np.empty(len(me.loops), dtype=np.int32)
            me.loops.foreach_get('vertex_index', vi)
            ls = np.empty(len(me.polygons), dtype=np.int32)
            me.polygons.foreach_get('loop_total', ls)
            loops.append(vi + base); sizes.append(ls); base += n
        if not verts:
            continue
        v = np.concatenate(verts); li = np.concatenate(loops); ls = np.concatenate(sizes)
        me = bpy.data.meshes.new(mat.name if mat else 'nomat')
        me.vertices.add(len(v)); me.vertices.foreach_set('co', v.ravel())
        me.loops.add(len(li)); me.loops.foreach_set('vertex_index', li)
        me.polygons.add(len(ls))
        starts = np.concatenate(([0], np.cumsum(ls)[:-1])).astype(np.int32)
        me.polygons.foreach_set('loop_start', starts); me.polygons.foreach_set('loop_total', ls)
        me.update(calc_edges=True); me.validate()
        if mat: me.materials.append(mat)
        ob = bpy.data.objects.new(me.name, me); bpy.context.scene.collection.objects.link(ob)
        merged.append(ob)
    bpy.data.batch_remove([o for o in objs] + [o.data for o in objs if o.data and o.data.users <= 1])
    return merged
