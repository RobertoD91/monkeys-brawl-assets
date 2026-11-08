#!/usr/bin/env bash
# Pipeline completa mesh Hunyuan -> <id>.glb pronto per il gioco.
# Uso: tools/build_glb.sh <id> [<cartella personaggio>] [<francesco.glb decompresso>]
# Richiede: blender (4.2), python3 + trimesh, @gltf-transform/cli (+ node_modules raggiungibile da tools/)
set -euo pipefail
T=$(cd "$(dirname "$0")" && pwd)
ID=$1; DIR=$(realpath "${2:-$T/../$ID}"); REF=$(realpath "${3:-$T/../_ref/francesco.glb}")
TMP=$(mktemp -d)
cd "$DIR"
python3 "$T/landmarks.py" mesh/raw_textured.glb rig/landmarks.json
blender -b --python "$T/rig_fighter.py" -- mesh/raw_textured.glb "$REF" rig/landmarks.json "$ID" rig/${ID}_rig.blend rig/${ID}_raw.glb 2>&1 | grep -E '^(FACES|VGROUPS|SKIN_VERTS|CLEANED|BRIDGE_FACES|UNWEIGHTED|MAX_ORIENT|HIPS|HEIGHT|DONE)|Error|Traceback'
blender -b rig/${ID}_rig.blend --python "$T/fix_weights.py" -- rig/${ID}_raw.glb 2>&1 | grep -E 'FIXED|Error|Traceback'
rm -f rig/${ID}_rig.blend1
node "$T/restructure.mjs" rig/${ID}_raw.glb $TMP/rs.glb "$ID"
gltf-transform resize $TMP/rs.glb $TMP/r1.glb --width 1024 --height 1024 >/dev/null
gltf-transform webp $TMP/r1.glb $TMP/r2.glb --quality 90 >/dev/null
gltf-transform quantize $TMP/r2.glb $TMP/r3.glb --quantization-volume mesh >/dev/null
node "$T/fixquant.mjs" $TMP/r3.glb $TMP/r2.glb out/${ID}.glb
ls -la out/${ID}.glb
rm -rf $TMP
