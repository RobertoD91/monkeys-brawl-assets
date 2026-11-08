#!/usr/bin/env python3
"""Ritratto e testa HUD di roberto per pg_art.js.

Uso: python3 build_art.py <pg_art.js>   (dalla cartella art/)
- portrait_raw.png (FLUX Kontext, sfondo bianco) -> sfondo trasparente (flood fill dai bordi)
- ritratto 512 px di larghezza (come gli altri) -> MB_PG_ART.roberto + MB_PG_META.roberto
- testa 256x248 con pennellate del colore d'accento -> MB_HUD_HEAD.roberto
"""
import base64, io, json, re, sys
from collections import deque
from PIL import Image, ImageDraw, ImageFilter

ACCENT = (0x00, 0xB3, 0xA4)
src = Image.open('portrait_raw.png').convert('RGB')
W, H = src.size
px = src.load()

# --- sfondo: flood fill dei pixel quasi bianchi collegati ai bordi ---
bg = bytearray(W * H)
def white(x, y):
    r, g, b = px[x, y]
    return r > 232 and g > 232 and b > 232
q = deque()
for x in range(W):
    for y in (0, H - 1):
        if white(x, y): q.append((x, y))
for y in range(H):
    for x in (0, W - 1):
        if white(x, y): q.append((x, y))
while q:
    x, y = q.popleft()
    i = y * W + x
    if bg[i]: continue
    bg[i] = 1
    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
        if 0 <= nx < W and 0 <= ny < H and not bg[ny * W + nx] and white(nx, ny):
            q.append((nx, ny))
alpha = Image.frombytes('L', (W, H), bytes(255 - 255 * v for v in bg))
alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
img = src.convert('RGBA'); img.putalpha(alpha)
bbox = alpha.point(lambda a: 255 if a > 20 else 0).getbbox()
img = img.crop(bbox)
img.save('portrait_cut.png')

# --- ritratto 512 px ---
pw = 512
ph = round(img.height * pw / img.width)
pg = img.resize((pw, ph), Image.LANCZOS)
# viso: in portrait_raw il centro del viso è a ~(490, 290) su 1024
fx = (490 - bbox[0]) / (bbox[2] - bbox[0])
fy = 0.15
buf = io.BytesIO(); pg.save(buf, 'WEBP', quality=86, method=6)
pg_uri = 'data:image/webp;base64,' + base64.b64encode(buf.getvalue()).decode()
meta = [pw, ph, round(fx, 3), fy]

# --- testa HUD 256x248 ---
hw, hh = 256, 248
head = Image.new('RGBA', (hw, hh), (0, 0, 0, 0))
d = ImageDraw.Draw(head)
dark = tuple(int(c * 0.55) for c in ACCENT)
for (x0, y0, x1, y1, w, col) in [(10, 200, 250, 30, 34, ACCENT), (0, 150, 200, 0, 22, dark), (60, 248, 256, 90, 26, ACCENT),
                                 (150, 240, 256, 160, 18, dark), (0, 90, 90, 20, 16, ACCENT)]:
    d.line((x0, y0, x1, y1), fill=col + (235,), width=w)
crop_box = (270, 0, 750, 465)  # testa e collo nel ritratto originale 1024x1024
face = src.convert('RGBA'); face.putalpha(alpha)
face = face.crop(crop_box).resize((hw, round(hw * (crop_box[3] - crop_box[1]) / (crop_box[2] - crop_box[0]))), Image.LANCZOS)
head.alpha_composite(face.crop((0, 0, hw, hh)))
head.save('hud_head.png')
buf = io.BytesIO(); head.save(buf, 'WEBP', quality=86, method=6)
hud_uri = 'data:image/webp;base64,' + base64.b64encode(buf.getvalue()).decode()

# --- inserimento in pg_art.js (idempotente) ---
path = sys.argv[1]
s = open(path, encoding='utf-8').read()
if "\n  roberto: 'data:" in s:
    print('roberto già presente in', path); sys.exit(0)
s = s.replace('window.MB_PG_ART = {\n', "window.MB_PG_ART = {\n  roberto: '%s',\n" % pg_uri, 1)
s = s.replace('window.MB_HUD_HEAD = {\n', "window.MB_HUD_HEAD = {\n  roberto: '%s',\n" % hud_uri, 1)
s = s.replace('window.MB_PG_META = {', 'window.MB_PG_META = {"roberto":%s,' % json.dumps(meta), 1)
assert s.count("roberto: 'data:") == 2 and '"roberto":[' in s
open(path, 'w', encoding='utf-8').write(s)
print('ok', meta, len(pg_uri), len(hud_uri))
