import bpy, sys, math, mathutils, time, addon_utils
argv=sys.argv[sys.argv.index('--')+1:]
left, right, out, samples, res = argv[0], argv[1], argv[2], int(argv[3]), int(argv[4])
bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable('io_scene_x3d')
sc=bpy.context.scene
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
            return col + (round(b.inputs['Alpha'].default_value, 3),)
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


def imp(path):
    before=set(bpy.data.objects); t=time.time()
    bpy.ops.import_scene.x3d(filepath=path, axis_forward='Y', axis_up='Z')
    objs=[o for o in bpy.data.objects if o not in before]
    print('imported',path,len(objs),'in',round(time.time()-t),'s')
    bpy.context.view_layer.update()
    empties=[o for o in objs if o.type!='MESH']      # the importer's Transform nodes
    meshes=merge_by_material([o for o in objs if o.type=='MESH'])
    bpy.data.batch_remove(empties)
    print('merged into',len(meshes),'objects in',round(time.time()-t),'s')
    root=bpy.data.objects.new(path.split('/')[-1],None); sc.collection.objects.link(root)
    for o in meshes: o.parent=root
    root.scale=(0.001,)*3          # file is in mm, scene in m
    return root,meshes
def bbox(objs):
    bpy.context.view_layer.update()
    pts=[o.matrix_world@mathutils.Vector(c) for o in objs for c in o.bound_box]
    return (mathutils.Vector([min(p[i] for p in pts) for i in range(3)]),
            mathutils.Vector([max(p[i] for p in pts) for i in range(3)]))
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import materials, textured_parts
halves=[imp(left),imp(right)]
# checkpoint: the import and merge are the slow part (~25 min); rerender.py
# can finish from this file if anything below fails
bpy.ops.wm.save_as_mainfile(filepath=out.rsplit('.',1)[0]+'_imported.blend', compress=True)
materials.tag(bpy)
for (root,_),side in zip(halves,('left','right')):
    board=os.path.join(textured_parts.REPO,'poly_kybd',f'poly_kybd_split72_{side}.kicad_pcb')
    textured_parts.add(root, textured_parts.board_keys(board))
# add() deletes the imported cables: re-read each half's meshes
halves=[(root,[o for o in root.children_recursive if o.type=='MESH']) for root,_ in halves]
for root,objs in halves:
    lo,hi=bbox(objs); ext=hi-lo
    if ext.y<ext.z:                 # came in Y-up: stand it on the floor
        root.rotation_euler.x=math.radians(90)
    lo,hi=bbox(objs); print('bbox',lo,hi)
    root.location-= mathutils.Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
# split the halves apart with a slight splay, as on a desk
gap=0.05
for (root,objs),sgn in zip(halves,(-1,1)):
    lo,hi=bbox(objs); piv=bpy.data.objects.new('piv',None); sc.collection.objects.link(piv)
    root.parent=piv; piv.location.x=sgn*((hi.x-lo.x)/2+gap/2); piv.rotation_euler.z=math.radians(-sgn*10)
print('material roles', materials.apply(bpy))
# floor + lights + camera
bpy.ops.mesh.primitive_plane_add(size=8); fl=bpy.context.object
m=bpy.data.materials.new('floor'); m.use_nodes=True; b=m.node_tree.nodes['Principled BSDF']
b.inputs['Base Color'].default_value=(0.03,0.03,0.035,1); b.inputs['Roughness'].default_value=0.3; fl.data.materials.append(m)
tgt=bpy.data.objects.new('target',None); tgt.location=(0,0.01,0.01); sc.collection.objects.link(tgt)
import lighting
lighting.studio(sc, tgt)            # even light across both halves
cd=bpy.data.cameras.new('cam'); cd.lens=50; cam=bpy.data.objects.new('cam',cd); sc.collection.objects.link(cam); sc.camera=cam
cam.location=(0,-0.62,0.40); c=cam.constraints.new('TRACK_TO'); c.target=tgt
cd.dof.use_dof=True; cd.dof.focus_object=tgt; cd.dof.aperture_fstop=4
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.samples=samples; materials.scene_settings(sc)
sc.render.resolution_x=res; sc.render.resolution_y=int(res*9/16); sc.render.filepath=out
sc.view_settings.view_transform='AgX'
bpy.ops.wm.save_as_mainfile(filepath=out.rsplit('.',1)[0]+'.blend', compress=True)
t=time.time(); bpy.ops.render.render(write_still=True); print('render s',round(time.time()-t))
