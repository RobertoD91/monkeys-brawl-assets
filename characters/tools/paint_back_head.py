#!/usr/bin/env python3
"""Copre la nuca con il colore dei capelli (Hunyuan proietta sul retro della testa il viso
specchiato, partendo dalla sola vista frontale). Non dipinge la texture (le isole UV del retro
possono coincidere con quelle del viso): trova un punto della texture che è già "capelli" (es. la
coda) e scrive <out.json>; rig_fighter.py, se trova rig/hair_back.json, rimappa su quel punto le UV
delle facce rivolte all'indietro sopra il collo.

Uso: python3 paint_back_head.py <mesh.glb> <rig/hair_back.json> <collo_z_frazione (es. 0.705)> [soglia_normale=-0.25]
"""
import json
import sys
import numpy as np
import trimesh

src, dst, neck_frac = sys.argv[1], sys.argv[2], float(sys.argv[3])
nthr = float(sys.argv[4]) if len(sys.argv) > 4 else -0.3
scene = trimesh.load(src)
name, m = next(iter(scene.geometry.items()))
img = np.asarray(m.visual.material.baseColorTexture.convert('RGB')).astype(np.float32) / 255
H, W = img.shape[:2]
uv = m.visual.uv
zmin, zmax = m.bounds[0][1], m.bounds[1][1]
neck = zmin + neck_frac * (zmax - zmin)

def color_at(u, v):
    return img[min(H - 1, max(0, int((1 - v) * H))), min(W - 1, max(0, int(u * W)))]

fc, fn = m.triangles_center, m.face_normals
fuv = uv[m.faces].mean(axis=1)
back = (fn[:, 2] < nthr) & (fc[:, 1] > neck)
cols = np.array([color_at(u, v) for u, v in fuv])
# capelli: facce rivolte all'indietro in alto, colore scuro e "caldo" (marrone)
top = back & (fc[:, 1] > neck + 0.5 * (zmax - neck))
hairish = top & (cols.sum(axis=1) < 1.4) & (cols[:, 0] >= cols[:, 2])
hair_col = np.median(cols[hairish], axis=0)
# punto UV di riferimento: la faccia "capelli" col colore più vicino alla mediana
cand = np.where(hairish)[0]
ref = cand[np.argmin(np.abs(cols[cand] - hair_col).sum(axis=1))]
ref_uv = fuv[ref]
target = np.where(back)[0]
print('facce nuca:', len(target), 'colore capelli:', (hair_col * 255).astype(int).tolist(), 'uv', ref_uv.round(3).tolist())

json.dump({'neck_frac': neck_frac, 'normal': -nthr, 'uv': [float(ref_uv[0]), float(ref_uv[1])]}, open(dst, 'w'))
print('scritto', dst)
