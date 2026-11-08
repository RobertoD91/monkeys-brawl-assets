# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Lingua e branch

- Parla con l'utente **in italiano**.
- Lavora direttamente su **`main`**.

## Cos'è questo repo

Asset binari di **Monkey Brawl League**, il gioco che sta nel repo `../monkeys-brawl` (vedi il suo CLAUDE.md per l'architettura). Qui non c'è codice da compilare né test: solo file serviti così come sono. Nessun file LICENSE.

I commit ("Monkey Brawl League: modelli, suoni e musica") sono deploy automatici dal progetto upstream di Francesco De Nittis (`Fraffo96`); questo repo è un fork.

## Come il gioco usa questi file

- Il gioco li scarica da jsDelivr fissando un commit preciso: `https://cdn.jsdelivr.net/gh/<owner>/monkeys-brawl-assets@<commit>/<file>` (in `index.html`: `MB_ASSET_CDN`, `three.min.js`, `MB_MUSIC`, `sfx_samples.js`). Se il CDN fallisce ripiega sul Cloudflare Worker (`…workers.dev/assets/…`, `/music/…`). Oggi `index.html` punta a **`Fraffo96`**, non a questo fork: un file nuovo pushato qui non viene usato finché non si cambiano owner e commit in `MB_ASSET_CDN` (e si aggiunge la voce in `MB_ASSET_VER`/`MB_ASSET_META`).
- Tutti i file stanno nella root, senza sottocartelle: il gioco usa l'ultimo segmento del percorso logico (`chars/ada` → `ada.glb`, `anim/library` → `library.glb`).

| File | Ruolo |
|---|---|
| `<id>.glb` | Modello del lottatore `<id>` (id di `HCG_ROSTER`), con scheletro Mixamo (`mixamorig:*`). Caricato con `GLTFLoader` + `MeshoptDecoder`, quindi può essere compresso con meshopt. |
| `<id>_fix.glb` | Variante opzionale caricata insieme a `<id>.glb`; se manca il gioco va avanti lo stesso. |
| `<id>_<forma>.glb` | Trasformazioni (`vito_gorilla`, `antonio_baboon`, `francesco_fat`, `simone_maranza`, `ada_fata`, `monkey`), mappate nel codice del gioco. |
| `library.glb` | Libreria unica delle animazioni condivise da tutti i lottatori (clip indicizzate per nome). Un personaggio nuovo deve avere la stessa rest pose e gli stessi nomi di ossa per poterla usare. |
| `*.mp3` | Musica (elenco e titoli in `MB_MUSIC`). |
| `sfx_samples.js` | Effetti sonori come data URI; nell'intestazione ci sono fonti e licenze (Kenney CC0, Mixkit, QuickSounds, Pixabay). Generato da script upstream (`tools/*.py`, non presenti qui). |
| `three.min.js` | Build di three.js usata dal gioco. |

## Aggiungere o modificare un personaggio

Segui la pipeline del brief upstream (https://gist.github.com/Fraffo96/88142dc00eb05afd5be5141da5ca62b5), riassunta nel CLAUDE.md di `monkeys-brawl`: sheet 2D approvato dall'utente → mesh (Hunyuan3D) → rig Mixamo in Blender → pose di prova approvate → export `<id>.glb`. Non modificare i `.glb` dei personaggi già approvati. Dopo il push, aggiorna in `index.html` e `test/index.html` del gioco: commit in `MB_ASSET_CDN`, hash in `MB_ASSET_VER`, misure e dimensione in `MB_ASSET_META`.
