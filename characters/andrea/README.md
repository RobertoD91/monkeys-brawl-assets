# andrea: pipeline del personaggio

Stessa pipeline di roberto (vedi `../tools/README.md`); le foto di partenza (`ref/`) sono nel repo privato `RobertoD91/brawl` (`characters/andrea/ref/`), non qui perché questo repo è pubblico.

| Cartella | Contenuto |
|---|---|
| `sheet/` | vista frontale da foto (FLUX Kontext: `front_stage1*` → `front_hr.png`), poi convertita in illustrazione 2D (`front_2d.png`): da quella Hunyuan ricava un viso pulito. `style_pair*` è un tentativo scartato. |
| `mesh/` | Hunyuan3D 2.1 da `front_2d_pad.png` (`attempt1/` = prima prova scartata: l'ombra a terra era diventata una lastra) |
| `rig/` | `landmarks.json`, `.blend`, pose di prova (`poses_v6.png` finale; v1–v5 mostrano i problemi risolti: profondità articolazioni, pugni attaccati alla giacca) |
| `out/` | `andrea.glb` |
| `art/` | ritratto (`portrait_src.png`) e testa HUD; `python3 build_art.py <pg_art.js> andrea '#B388FF' 460 230,30,710,520 portrait_src.png` |

Comando: `../tools/build_glb.sh andrea .`

## Da rivedere
- L'abito grigio con il materiale toon del gioco tende al blu.
- Nessun `andrea_fix.glb` (404 innocuo).
