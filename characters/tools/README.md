# Strumenti della pipeline personaggi

`build_glb.sh <id> [<cartella personaggio>] [<francesco.glb decompresso>]` esegue tutta la catena dalla mesh Hunyuan (`mesh/raw_textured.glb`) a `out/<id>.glb`:

1. `landmarks.py`: stima le articolazioni dalle sezioni orizzontali della mesh (inforcatura, ascelle, mani, spalle, collo) → `rig/landmarks.json`
2. `rig_fighter.py` (Blender 4.2 headless): scheletro di Francesco con le stesse rotazioni di riposo, articolazioni spostate sulla mesh, pesi automatici, T-pose
3. `fix_weights.py`: vertici senza pesi, max 4 influenze
4. `restructure.mjs`: struttura `<id>_rig` → `<id>_lo` → mesh, come gli altri glb
5. `gltf-transform` resize 1024 / webp / quantize, poi `fixquant.mjs` (dequantizzazione anche sul nodo mesh + meshopt)

Requisiti: `blender`, `python3` con `trimesh`, `@gltf-transform/cli` 4.x (con `node_modules` raggiungibile da questa cartella: `ln -s $(npm root -g)/@gltf-transform/cli/node_modules node_modules`), il `francesco.glb` decompresso con `gltf-transform copy francesco.glb ../_ref/francesco.glb`.

Pose di prova: `poses.html` + `shot.js` (vedi `../roberto/README.md`).
