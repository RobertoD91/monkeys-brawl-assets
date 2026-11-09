# Rig di un lottatore: riusa lo scheletro Mixamo di francesco.glb (stesse rotazioni di riposo),
# adatta le articolazioni (da landmarks.py) alle proporzioni della mesh Hunyuan e la porta in T-pose.
# Uso: blender -b --python rig_fighter.py -- <mesh.glb> <ref_francesco.glb> <landmarks.json> <id> <out.blend> <out.glb>
import bpy, sys, math, json
from mathutils import Vector, Matrix, Quaternion

args = sys.argv[sys.argv.index('--') + 1:]
MESH, REF, LMK, FID, OUT_BLEND, OUT_GLB = args
TARGET_FACES = 9000
LM = json.load(open(LMK))
H_TARGET = LM['H']
JT = LM['joints']

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
M.name = FID + '_mesh'
# riduzione poligoni (come gli altri personaggi, ~8k triangoli)
nf = len(M.data.polygons)
if nf > TARGET_FACES:
    d = M.modifiers.new('dec', 'DECIMATE'); d.ratio = TARGET_FACES / nf
    bpy.ops.object.modifier_apply(modifier='dec')
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.0005); bpy.ops.object.mode_set(mode='OBJECT')
print('FACES', nf, '->', len(M.data.polygons))

# nuca color pelle -> UV su un punto "capelli" (vedi paint_back_head.py), se richiesto
import os
HB = os.path.join(os.path.dirname(LMK), 'hair_back.json')
if os.path.exists(HB):
    hb = json.load(open(HB))
    zc = hb['neck_frac'] * H_TARGET
    uvl = M.data.uv_layers.active.data
    nb = 0
    for poly in M.data.polygons:
        if poly.normal.y > hb['normal'] and poly.center.z > zc:
            for li in poly.loop_indices:
                uvl[li].uv = hb['uv']
            nb += 1
    print('HAIR_BACK_FACES', nb)
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

Y0 = None  # landmarks.json ha la profondità (y) come terzo valore, già nella scala finale
for nm in ['Hips', 'Spine', 'Spine1', 'Spine2', 'Neck', 'Head']:
    L(nm, JT[nm][0], JT[nm][1], y=JT[nm][2])
J['mixamorigHeadTop_End'] = Vector((0, J['mixamorigHead'].y, H_TARGET))
sx, sz = JT['LeftShoulder'][:2]
L('LeftShoulder', sx, sz, y=JT['LeftShoulder'][2])
for nm in ['LeftArm', 'LeftForeArm', 'LeftHand', 'LeftUpLeg', 'LeftLeg', 'LeftFoot']:
    L(nm, JT[nm][0], JT[nm][1], y=JT[nm][2])
fx = JT['LeftFoot'][0]
ft = front(fx, 0.05)
ay = J['mixamorigLeftFoot'].y
L('LeftToeBase', fx, 0.035, y=ay + 0.6 * (ft - ay))
L('LeftToe_End', fx, 0.02, y=ft)
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
    tip = Vector((sx * JT['HandTip'][0], J[hn].y, JT['HandTip'][1]))
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

# ---------- pulizia pesi con la geometria (braccia attaccate al busto, capelli, lati) ----------
CUT = sorted(LM.get('arm_cut', []))
INFO = LM['info']
def cut_at(z):
    if not CUT:
        return None
    if z <= CUT[0][0]:
        return CUT[0][1]
    for (z0, b0), (z1, b1) in zip(CUT, CUT[1:]):
        if z0 <= z <= z1:
            return b0 + (b1 - b0) * (z - z0) / (z1 - z0)
    return CUT[-1][1]
gname = {g.index: g.name for g in M.vertex_groups}
# colore della texture per vertice (per riconoscere la pelle delle mani attaccate alla giacca)
import numpy as np
SKIN = set()
try:
    img = next(n.image for m in M.data.materials for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image)
    iw, ih = img.size
    pix = np.array(img.pixels[:], dtype=np.float32).reshape(ih, iw, img.channels)
    uv = M.data.uv_layers.active.data
    acc = {}
    for poly in M.data.polygons:
        for li in poly.loop_indices:
            vi = M.data.loops[li].vertex_index
            u, w = uv[li].uv
            c = pix[min(ih - 1, max(0, int(w * ih))), min(iw - 1, max(0, int(u * iw)))][:3]
            acc.setdefault(vi, []).append(c)
    for vi, cs in acc.items():
        r, g, b_ = np.mean(cs, axis=0)
        if r > 0.45 and g > 0.28 and b_ < g and (r - b_) > 0.12 and (r - g) < 0.3:
            SKIN.add(vi)
except StopIteration:
    pass
print('SKIN_VERTS', len(SKIN))
is_arm = lambda n: ('Arm' in n or 'Hand' in n) and 'Shoulder' not in n
removed = 0
for v in M.data.vertices:
    x, z = v.co.x, v.co.z
    drop = set()
    for g in v.groups:
        n = gname[g.group]
        if ('Left' in n and x < -0.03) or ('Right' in n and x > 0.03):
            drop.add(g.group)                                   # lato opposto
        elif is_arm(n) and z > INFO['shoulder_top']:
            drop.add(g.group)                                   # capelli/testa
    b = cut_at(z)
    if b is not None and v.index in SKIN and abs(x) > 0.2 and INFO['hand_bottom'] - 0.02 <= z <= JT['LeftHand'][1] + 0.06:
        b = 0.0   # pelle della mano: sempre lato braccio
    if b is not None and INFO['hand_bottom'] - 0.02 <= z <= INFO['armpit']:
        for g in v.groups:
            n = gname[g.group]
            if abs(x) < b and is_arm(n) and z < INFO['armpit'] - 0.10:
                drop.add(g.group)                               # busto: niente braccio
            elif abs(x) > b + 0.01 and z < INFO['armpit'] - 0.10 and not is_arm(n):
                drop.add(g.group)                               # braccio: niente busto
    if drop and len(drop) < len(v.groups):
        for gi in drop:
            M.vertex_groups[gi].remove([v.index])
        removed += 1
    elif drop:
        # tutto da togliere: assegna l'osso giusto per la zona (braccio o busto) con peso 1
        for gi in drop:
            M.vertex_groups[gi].remove([v.index])
        side = 'Left' if x > 0 else 'Right'
        if b is not None and abs(x) > b and INFO['hand_bottom'] - 0.02 <= z <= INFO['armpit']:
            part = 'Hand' if z < JT['LeftHand'][1] + 0.04 else ('ForeArm' if z < JT['LeftForeArm'][1] else 'Arm')
            bone = 'mixamorig' + side + part
        elif z > INFO['shoulder_top']:
            bone = 'mixamorigHead' if z > JT['Head'][1] else 'mixamorigNeck'
        else:
            bone = 'mixamorigHips' if z < JT['Spine'][1] else 'mixamorigSpine1'
        M.vertex_groups[bone].add([v.index], 1.0, 'REPLACE')
        removed += 1
print('CLEANED_VERTS', removed)
# facce "ponte" tra pugno e giacca (vertici metà braccio e metà busto): si allungherebbero, le togliamo
import bmesh
arm_dom = []
for v in M.data.vertices:
    aw = sum(g.weight for g in v.groups if is_arm(gname[g.group]))
    tw = sum(g.weight for g in v.groups)
    arm_dom.append(tw > 0 and aw / tw > 0.5)
bm = bmesh.new(); bm.from_mesh(M.data)
z0, z1 = INFO['hand_bottom'] - 0.03, JT['LeftHand'][1] + 0.1
bridge = [f for f in bm.faces
          if z0 <= f.calc_center_median().z <= z1 and abs(f.calc_center_median().x) > 0.2
          and len({arm_dom[v.index] for v in f.verts}) == 2]
bmesh.ops.delete(bm, geom=bridge, context='FACES')
bm.to_mesh(M.data); bm.free(); M.data.update()
print('BRIDGE_FACES', len(bridge))
unweighted = sum(1 for v in M.data.vertices if not any(x.weight > 1e-4 for x in v.groups))
print('UNWEIGHTED_VERTS', unweighted)
# normalizza (i vertici senza pesi li sistema fix_weights.py con il vicino pesato)
bpy.context.view_layer.objects.active = M
bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.objects.active = A

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
A.name = FID + '_rig'; A.data.name = FID + '_rig'
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
    m.name = FID + '_mat'
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
