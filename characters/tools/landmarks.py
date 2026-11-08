#!/usr/bin/env python3
"""Stima le articolazioni di un personaggio Hunyuan (in piedi, frontale, braccia lungo i fianchi)
dalle sezioni orizzontali della mesh. Coordinate come in Blender dopo la normalizzazione del rig:
x (sinistra del personaggio = +x), z in alto, piedi a z=0, altezza H, centrato sui bounds in x.

Uso: python3 landmarks.py <mesh.glb> <out.json> [H=1.985]
"""
import json, sys
import numpy as np
import trimesh

src, out = sys.argv[1], sys.argv[2]
H = float(sys.argv[3]) if len(sys.argv) > 3 else 1.985
m = trimesh.load(src, force='mesh')
P = m.sample(400000)
x, z = P[:, 0], P[:, 1]                     # glTF: Y in alto
s = H / (z.max() - z.min())
x = (x - (m.bounds[0][0] + m.bounds[1][0]) / 2) * s
z = (z - z.min()) * s

def iv(zz, half=0.006, gap=0.03):
    xs = np.sort(x[(z > zz - half) & (z < zz + half)])
    if len(xs) == 0:
        return []
    br = np.where(np.diff(xs) > gap)[0]
    st, en = np.r_[0, br + 1], np.r_[br, len(xs) - 1]
    return [(xs[a], xs[b]) for a, b in zip(st, en)]

zs = np.arange(0.02, H, 0.01)
S = {round(zz, 2): iv(zz) for zz in zs}
def at(zz):
    return S[round(min(max(zz, 0.02), H - 0.01), 2)]
def center_iv(zz):
    return next((a for a in at(zz) if a[0] <= 0 <= a[1]), None)
def width(zz):
    c = center_iv(zz)
    return (c[1] - c[0]) if c else 0

# inforcatura: primo z (dal basso, sopra le caviglie) in cui un intervallo contiene x=0
crotch = next(zz for zz in zs if zz > 0.15 * H and center_iv(zz))
# ascella: primo z sopra l'inforcatura con un solo intervallo (braccia unite al busto)
armpit = next(zz for zz in zs if zz > crotch and len(at(zz)) == 1)
# fondo delle mani: z minimo con intervalli laterali staccati sopra/sotto l'inforcatura
def side_ivs(zz):
    ivs = at(zz)
    if zz >= crotch:
        return [a for a in ivs if not (a[0] <= 0 <= a[1]) and a[0] > 0]
    legs = sorted(ivs, key=lambda a: abs((a[0] + a[1]) / 2))[:2]
    return [a for a in ivs if a not in legs and a[0] > 0]
hand_bottom = next(zz for zz in zs if zz > 0.1 * H and side_ivs(zz))
# spalle: dove la larghezza del busto crolla sopra l'ascella
w0 = width(armpit + 0.05)
shoulder_top = next(zz for zz in zs if zz > armpit + 0.08 and width(zz) < 0.7 * w0)
neck = shoulder_top - 0.03
rng = [zz for zz in zs if shoulder_top <= zz <= shoulder_top + 0.12]
head = min(rng, key=width)
hips = crotch + 0.12
upleg = crotch + 0.07
ankle = 0.05 * H
knee = (upleg + ankle) / 2
shoulder_z = armpit + 0.6 * (shoulder_top - armpit)
arm_w = np.mean([a[1] - a[0] for zz in np.arange(armpit - 0.12, armpit - 0.02, 0.01) for a in side_ivs(zz)])
torso_out = max(a[1] for a in at(shoulder_z))
wrist = hand_bottom + 0.4 * (armpit - hand_bottom)
elbow = (shoulder_z + wrist) / 2

def arm_x(zz):
    a = side_ivs(zz)
    return float((a[0][0] + a[0][1]) / 2) if a else None
def leg_x(zz):
    legs = [a for a in at(zz) if a[0] > 0]
    return float((legs[0][0] + legs[0][1]) / 2) if legs else None

L = {
    'Hips': [0.0, hips], 'Spine': [0.0, hips + (neck - hips) * 0.18], 'Spine1': [0.0, hips + (neck - hips) * 0.40],
    'Spine2': [0.0, hips + (neck - hips) * 0.63], 'Neck': [0.0, neck], 'Head': [0.0, head],
    'LeftShoulder': [0.06, shoulder_z + 0.05],
    'LeftArm': [float(torso_out - arm_w / 2), shoulder_z],
    'LeftForeArm': [arm_x(elbow), elbow],
    'LeftHand': [arm_x(wrist), wrist],
    'HandTip': [arm_x(hand_bottom + 0.01), hand_bottom],
    'LeftUpLeg': [leg_x(crotch - 0.04), upleg],
    'LeftLeg': [leg_x(knee), knee],
    'LeftFoot': [leg_x(ankle + 0.03), ankle],
}
L = {k: [round(float(v[0]), 4), round(float(v[1]), 4)] for k, v in L.items()}
info = dict(crotch=crotch, armpit=armpit, hand_bottom=hand_bottom, shoulder_top=shoulder_top, arm_w=arm_w)
json.dump({'H': H, 'joints': L, 'info': {k: round(float(v), 4) for k, v in info.items()}}, open(out, 'w'), indent=1)
print(json.dumps(info, default=float))
for k, v in L.items():
    print(k, v)
