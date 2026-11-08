# Rig di roberto: riusa lo scheletro Mixamo di francesco.glb (stesse rotazioni di riposo),
# adatta le articolazioni alle proporzioni della mesh Hunyuan (A-pose) e la porta in T-pose.
# Uso: blender -b --python rig_roberto.py -- <mesh.glb> <ref_francesco.glb> <out.blend> <out.glb>
import bpy, sys, math
from mathutils import Vector, Matrix, Quaternion

args = sys.argv[sys.argv.index('--') + 1:]
MESH, REF, OUT_BLEND, OUT_GLB = args
TARGET_FACES = 9000
H_TARGET = 1.985

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# ---------- riferimento: armatura di francesco ----------
bpy.ops.import_scene.gltf(filepath=REF)
R = next(o for o in sc.objects if o.type == 'ARMATURE')
for o in list(sc.objects):
    if o.type != 'ARMATURE':
        bpy.data.objects.remove(o, do_unlink=True)
R.name = 'REF'

# ---------- mesh ----------
before = set(sc.objects)
bpy.ops.import_scene.gltf(filepath=MESH)
M = next(o for o in sc.objects if o not in before and o.type == 'MESH')
for o in list(sc.objects):
    if o not in before and o is not M and o.type != 'MESH':
        pass
bpy.ops.object.select_all(action='DESELECT')
M.select_set(True); bpy.context.view_layer.objects.active = M
M.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
vs = [v.co for v in M.data.vertices]
mn = Vector([min(v[i] for v in vs) for i in range(3)]); mx = Vector([max(v[i] for v in vs) for i in range(3)])
s = H_TARGET / (mx.z - mn.z)
off = Vector(((mn.x + mx.x) / 2, 0, mn.z))
for v in M.data.vertices:
    v.co = (v.co - off) * s
M.name = 'roberto_mesh'
# riduzione poligoni (come gli altri personaggi, ~8k triangoli)
nf = len(M.data.polygons)
if nf > TARGET_FACES:
    d = M.modifiers.new('dec', 'DECIMATE'); d.ratio = TARGET_FACES / nf
    bpy.ops.object.modifier_apply(modifier='dec')
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.0005); bpy.ops.object.mode_set(mode='OBJECT')
print('FACES', nf, '->', len(M.data.polygons))

V = [v.co.copy() for v in M.data.vertices]
def depth(x, z, rx=0.06, rz=0.04):
    pts = [v for v in V if abs(v.x - x) < rx and abs(v.z - z) < rz]
    if not pts:
        return 0.0
    return (min(p.y for p in pts) + max(p.y for p in pts)) / 2
def front(x, zmax, rx=0.09):
    pts = [v for v in V if abs(v.x - x) < rx and v.z < zmax]
    return min(p.y for p in pts)

# ---------- punti articolari (lato sinistro = +x) ----------
J = {}
def L(name, x, z, y=None, rx=0.06, rz=0.04):
    yy = depth(x, z, rx, rz) if y is None else y
    J['mixamorig' + name] = Vector((x, yy, z))
    if 'Left' in name:
        J['mixamorig' + name.replace('Left', 'Right')] = Vector((-x, yy, z))

L('Hips', 0.0, 0.70, rx=0.2)
L('Spine', 0.0, 0.80, rx=0.2)
L('Spine1', 0.0, 0.93, rx=0.2)
L('Spine2', 0.0, 1.06, rx=0.2)
L('Neck', 0.0, 1.27, rx=0.1)
L('Head', 0.0, 1.36, rx=0.12)
J['mixamorigHeadTop_End'] = Vector((0, J['mixamorigHead'].y, H_TARGET))
L('LeftShoulder', 0.06, 1.20, y=depth(0.15, 1.2, 0.1))
L('LeftArm', 0.285, 1.15)
L('LeftForeArm', 0.365, 0.88)
L('LeftHand', 0.415, 0.66)
L('LeftUpLeg', 0.14, 0.66)
L('LeftLeg', 0.155, 0.37)
L('LeftFoot', 0.165, 0.10)
ft = front(0.17, 0.05)
ay = J['mixamorigLeftFoot'].y
L('LeftToeBase', 0.17, 0.035, y=ay + 0.6 * (ft - ay))
L('LeftToe_End', 0.17, 0.02, y=ft)
for k, v in sorted(J.items()):
    print('J', k, [round(c, 3) for c in v])

# ---------- armatura A (A-pose, sulla mesh) ----------
bpy.ops.object.select_all(action='DESELECT')
R.select_set(True); bpy.context.view_layer.objects.active = R
bpy.ops.object.duplicate()
A = bpy.context.active_object; A.name = 'A'

rest = {b.name: (b.matrix_local.copy(), b.length) for b in R.data.bones}
bpy.ops.object.mode_set(mode='EDIT')
eb = A.data.edit_bones
main_child = {
    'Hips': 'Spine', 'Spine': 'Spine1', 'Spine1': 'Spine2', 'Spine2': 'Neck', 'Neck': 'Head', 'Head': 'HeadTop_End',
    'LeftShoulder': 'LeftArm', 'LeftArm': 'LeftForeArm', 'LeftForeArm': 'LeftHand', 'LeftHand': None,
    'LeftUpLeg': 'LeftLeg', 'LeftLeg': 'LeftFoot', 'LeftFoot': 'LeftToeBase', 'LeftToeBase': 'LeftToe_End',
}
for k in list(main_child):
    if 'Left' in k:
        main_child[k.replace('Left', 'Right')] = main_child[k].replace('Left', 'Right') if main_child[k] else None
main_child = {'mixamorig' + k: ('mixamorig' + v if v else None) for k, v in main_child.items()}

def set_bone(e, head, Rm, Rlen, direction=None, length=None):
    rdir = (Rm.to_3x3() @ Vector((0, 1, 0))).normalized()
    rot = rdir.rotation_difference(direction.normalized()) if direction is not None else Quaternion()
    m3 = rot.to_matrix() @ Rm.to_3x3()
    e.use_connect = False
    e.matrix = Matrix.Translation(head) @ m3.to_4x4()
    e.length = length if length else Rlen

newmat = {}
for name in [b.name for b in R.data.bones]:
    if name not in J:
        continue
    Rm, Rlen = rest[name]
    c = main_child.get(name)
    if c:
        dvec = J[c] - J[name]
        set_bone(eb[name], J[name], Rm, Rlen, dvec, dvec.length)
    else:
        scale = 0.55 if 'Hand' in name else 1.0
        set_bone(eb[name], J[name], Rm, Rlen, None, Rlen * scale)

# mano: direzione verso la punta delle dita della mesh
for side, sx in (('Left', 1), ('Right', -1)):
    hn = 'mixamorig%sHand' % side
    tip = Vector((sx * 0.455, J[hn].y, 0.50))
    Rm, Rlen = rest[hn]
    set_bone(eb[hn], J[hn], Rm, Rlen, tip - J[hn], (tip - J[hn]).length * 0.6)
    # dita: trasformazione rigida+scala dalla mano di francesco alla mano di roberto
    RH = rest[hn][0]
    AH = eb[hn].matrix.copy()
    k = (tip - J[hn]).length / 0.29
    T = AH @ Matrix.Scale(k, 4) @ RH.inverted()
    rotT = (AH.to_3x3() @ RH.to_3x3().inverted())
    for b in R.data.bones:
        if b.name.startswith('mixamorig%sHand' % side) and b.name != hn:
            Rm, Rlen = rest[b.name]
            e = eb[b.name]; e.use_connect = False
            m3 = rotT @ Rm.to_3x3()
            e.matrix = Matrix.Translation(T @ Rm.to_translation()) @ m3.to_4x4()
            e.length = Rlen * k
bpy.ops.object.mode_set(mode='OBJECT')

# ---------- pesi automatici (bone heat) ----------
bpy.ops.object.select_all(action='DESELECT')
M.select_set(True); A.select_set(True); bpy.context.view_layer.objects.active = A
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
empty = [g.name for g in M.vertex_groups if not any(g.index in [x.group for x in v.groups if x.weight > 0.01] for v in M.data.vertices)]
print('VGROUPS', len(M.vertex_groups), 'empty', empty)
unweighted = sum(1 for v in M.data.vertices if not any(x.weight > 1e-4 for x in v.groups))
print('UNWEIGHTED_VERTS', unweighted)

# ---------- porta A nella T-pose di riferimento ----------
bpy.ops.object.mode_set(mode='POSE')
order = []
def walk(b):
    order.append(b.name)
    for c in b.children:
        walk(c)
for b in A.data.bones:
    if b.parent is None:
        walk(b)
for name in order:
    pb = A.pose.bones[name]
    bpy.context.view_layer.update()
    head = pb.head.copy()
    q = rest[name][0].to_quaternion()
    pb.matrix = Matrix.Translation(head) @ q.to_matrix().to_4x4()
bpy.context.view_layer.update()
bpy.ops.object.mode_set(mode='OBJECT')

# applica la deformazione alla mesh (ora in T-pose)
bpy.ops.object.select_all(action='DESELECT')
M.select_set(True); bpy.context.view_layer.objects.active = M
modname = next(m.name for m in M.modifiers if m.type == 'ARMATURE')
bpy.ops.object.modifier_apply(modifier=modname)
M.parent = None
M.matrix_world = Matrix.Identity(4)

# armatura finale: la posa di A diventa il riposo
bpy.ops.object.select_all(action='DESELECT')
A.select_set(True); bpy.context.view_layer.objects.active = A
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.select_all(action='SELECT')
bpy.ops.pose.armature_apply(selected=False)
bpy.ops.object.mode_set(mode='OBJECT')
A.name = 'roberto_rig'; A.data.name = 'roberto_rig'
bpy.data.objects.remove(R, do_unlink=True)

# controllo orientamenti
maxdev = 0
for b in A.data.bones:
    q1 = b.matrix_local.to_quaternion(); q2 = rest[b.name][0].to_quaternion()
    maxdev = max(maxdev, q1.rotation_difference(q2).angle)
print('MAX_ORIENT_DEV_DEG', round(math.degrees(maxdev), 4))

# rilega la mesh allo scheletro finale con gli stessi gruppi
M.parent = A
am = M.modifiers.new('Armature', 'ARMATURE'); am.object = A
for m in M.data.materials:
    m.name = 'roberto_mat'
hips = A.data.bones['mixamorigHips'].head_local
print('HIPS', [round(c, 4) for c in hips])
vs = [M.matrix_world @ v.co for v in M.data.vertices]
print('HEIGHT', round(max(v.z for v in vs) - min(v.z for v in vs), 4), 'XSPAN', round(min(v.x for v in vs), 3), round(max(v.x for v in vs), 3))

bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.export_scene.gltf(filepath=OUT_GLB, export_format='GLB', export_animations=False,
                          export_skins=True, export_yup=True, export_apply=False,
                          export_def_bones=False, export_image_format='WEBP')
print('DONE')
