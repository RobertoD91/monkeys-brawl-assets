# Assegna ai vertici senza pesi quelli del vertice pesato più vicino, normalizza a max 4 influenze, riesporta.
import bpy, sys
from mathutils import kdtree
OUT = sys.argv[sys.argv.index('--') + 1]
M = bpy.data.objects['roberto_mesh']
me = M.data
weighted = [v for v in me.vertices if any(g.weight > 1e-4 for g in v.groups)]
kd = kdtree.KDTree(len(weighted))
for i, v in enumerate(weighted): kd.insert(v.co, i)
kd.balance()
n = 0
for v in me.vertices:
    if not any(g.weight > 1e-4 for g in v.groups):
        co, i, d = kd.find(v.co)
        for g in weighted[i].groups:
            M.vertex_groups[g.group].add([v.index], g.weight, 'REPLACE')
        n += 1
bpy.context.view_layer.objects.active = M
M.select_set(True)
bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
bpy.ops.object.mode_set(mode='OBJECT')
print('FIXED', n)
bpy.ops.wm.save_mainfile()
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_animations=False, export_skins=True,
                          export_yup=True, export_def_bones=False, export_image_format='WEBP')
