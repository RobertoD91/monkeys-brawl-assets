// Copia la trasformazione di dequantizzazione (già nelle inverseBindMatrices) anche sul nodo mesh
// (come nei glb originali del gioco) e comprime con meshopt senza ri-quantizzare.
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS, EXTMeshoptCompression } from '@gltf-transform/extensions';
import { MeshoptDecoder, MeshoptEncoder } from 'meshoptimizer';
const [quantized, orig, out] = process.argv.slice(2);
await MeshoptDecoder.ready; await MeshoptEncoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder, 'meshopt.encoder': MeshoptEncoder });
const dq = await io.read(quantized), dn = await io.read(orig);
const ibmQ = dq.getRoot().listSkins()[0].getInverseBindMatrices();
const ibmO = dn.getRoot().listSkins()[0].getInverseBindMatrices();
// Q = IBM_orig^-1 * IBM_quant ; Q è traslazione + scala uniforme: dal joint 0
const a = ibmO.getElement(0, []), b = ibmQ.getElement(0, []);
const inv = m => { // inversa 4x4 column-major (affine)
  const r = [m[0],m[1],m[2],m[4],m[5],m[6],m[8],m[9],m[10]];
  const det = r[0]*(r[4]*r[8]-r[5]*r[7]) - r[3]*(r[1]*r[8]-r[2]*r[7]) + r[6]*(r[1]*r[5]-r[2]*r[4]);
  const i = [ (r[4]*r[8]-r[5]*r[7])/det, -(r[1]*r[8]-r[2]*r[7])/det, (r[1]*r[5]-r[2]*r[4])/det,
             -(r[3]*r[8]-r[5]*r[6])/det, (r[0]*r[8]-r[2]*r[6])/det, -(r[0]*r[5]-r[2]*r[3])/det,
              (r[3]*r[7]-r[4]*r[6])/det, -(r[0]*r[7]-r[1]*r[6])/det, (r[0]*r[4]-r[1]*r[3])/det ];
  const t = [m[12],m[13],m[14]];
  const it = [-(i[0]*t[0]+i[3]*t[1]+i[6]*t[2]), -(i[1]*t[0]+i[4]*t[1]+i[7]*t[2]), -(i[2]*t[0]+i[5]*t[1]+i[8]*t[2])];
  return [i[0],i[1],i[2],0,i[3],i[4],i[5],0,i[6],i[7],i[8],0,it[0],it[1],it[2],1];
};
const mul = (x, y) => { const o = new Array(16).fill(0); for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) for (let k = 0; k < 4; k++) o[c*4+r] += x[k*4+r]*y[c*4+k]; return o; };
const Q = mul(inv(a), b);
const s = Q[0], t = [Q[12], Q[13], Q[14]];
console.log('Q scale', s, 'off', t, 'check', Q[5], Q[10], Q[1], Q[4]);
// three.js (bindMode 'attached') annulla la trasformazione del nodo: le IBM restano quelle quantizzate,
// il nodo mesh riceve Q solo per bounding box / frustum culling corretti (come nei glb originali)
const mn = dq.getRoot().listNodes().find(n => n.getMesh() && n.getSkin());
mn.setTranslation(t).setScale([s, s, s]);
dq.createExtension(EXTMeshoptCompression).setRequired(true).setEncoderOptions({ method: EXTMeshoptCompression.EncoderMethod.QUANTIZE });
await io.write(out, dq);
console.log('scritto', out);
