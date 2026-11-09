# roberto: pipeline del personaggio

Segue il brief https://gist.github.com/Fraffo96/88142dc00eb05afd5be5141da5ca62b5 (vedi CLAUDE.md).

| Cartella | Contenuto |
|---|---|
| `ref/` | foto di partenza: nel repo privato `RobertoD91/brawl` (`characters/roberto/ref/`) |
| `sheet/` | sheet 2D approvato (Canva, solo miniatura) e vista frontale ad alta risoluzione rigenerata con FLUX.1 Kontext dev (HF) |
| `mesh/` | output grezzo di Hunyuan3D 2.1 (`raw_shape.glb`, `raw_textured.glb`) e anteprime |
| `rig/` | script Blender/glTF-Transform, `.blend` del rig, pose di prova (`poses_v1.png` prima versione, `poses_v2.png` finale) |
| `out/` | `roberto.glb` finale (copiato nella root del repo) |
| `art/` | ritratto e testa HUD per `pg_art.js` |

## Rifare il `.glb`

Strumenti: Blender 4.2 LTS (headless), `@gltf-transform/cli` 4.x. `francesco.glb` va prima decompresso (`gltf-transform copy francesco.glb ref/francesco.glb`).

1. `blender -b --python rig/rig_roberto.py -- mesh/raw_textured.glb ref/francesco.glb rig/roberto_rig.blend rig/roberto_raw.glb`
   riusa lo scheletro Mixamo di Francesco con le **stesse rotazioni di riposo** (le clip di `library.glb` sono solo rotazioni + posizione dei fianchi), adatta le articolazioni alla mesh in A-pose, pesi automatici, porta la mesh in T-pose.
2. `blender -b rig/roberto_rig.blend --python rig/fix_weights.py -- rig/roberto_raw.glb` (vertici senza pesi, max 4 influenze)
3. `node rig/restructure.mjs rig/roberto_raw.glb /tmp/rs.glb roberto` (struttura `roberto_rig` → `roberto_lo` → mesh, come gli altri)
4. `gltf-transform resize … --width 1024 --height 1024`, `webp --quality 90`, `quantize --quantization-volume mesh`
5. `node rig/fixquant.mjs <quantizzato> <non quantizzato> out/roberto.glb`: copia la dequantizzazione anche sul nodo mesh (bounding box e frustum culling corretti, come nei glb originali) e comprime con meshopt.

Pose di prova: servire `characters/tools/` insieme a `three.min.js`, `library.glb`, i `.glb` e lo script del loader estratto da `index.html` del gioco (riga con `window.MB_GLTF=`), poi `node tools/shot.js 'http://localhost:8123/poses.html?ids=roberto,francesco' out.png 2400 760`.

## Da rivedere
- Mani aperte con dita fuse: le clip chiudono le dita ma la mesh non le segue (i pugni sembrano schiaffi; per questo il moveset è quello a schiaffi di Francesco).
- Nessun file `roberto_fix.glb` (correzioni delle braccia per clip): il gioco lo cerca e riceve un 404 innocuo.
- `art/`: ritratto (FLUX Kontext dalla foto) e testa HUD, inseriti in `pg_art.js` del gioco con `python3 art/build_art.py ../../../monkeys-brawl/pg_art.js`.
