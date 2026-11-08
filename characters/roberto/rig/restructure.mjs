// Allinea la struttura del glb a quella dei personaggi esistenti: <id>_rig -> [<id>_lo -> mesh, Hips]
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { prune } from '@gltf-transform/functions';
const [inp, out, id] = process.argv.slice(2);
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);
const doc = await io.read(inp);
const root = doc.getRoot();
const scene = root.getDefaultScene() || root.listScenes()[0];
const rig = root.listNodes().find(n => n.getName() === id + '_rig');
const meshNode = root.listNodes().find(n => n.getMesh() && n.getSkin());
for (const n of scene.listChildren()) if (n !== rig) { scene.removeChild(n); if (!n.getMesh()) n.dispose(); }
const lo = doc.createNode(id + '_lo');
rig.removeChild(meshNode); lo.addChild(meshNode); meshNode.setName('');
const hips = rig.listChildren().find(n => n.getName() === 'mixamorigHips');
rig.removeChild(hips); rig.addChild(lo); rig.addChild(hips);
for (const m of root.listMaterials()) { m.setName(id + '_mat'); m.setMetallicRoughnessTexture(null); m.setMetallicFactor(0); m.setRoughnessFactor(1); const t = m.getBaseColorTexture(); if (t) t.setName(id + '_tex'); }
await doc.transform(prune());
await io.write(out, doc);
console.log('ok', scene.listChildren().map(n => n.getName()), rig.listChildren().map(n => n.getName()));
