// Removes the flat cream background from spot_*.raw.png so the icons sit on any surface.
// Soft chroma key: alpha ramps from 0 to 1 as a pixel's distance from the sampled
// corner colour goes from LO to HI. Output: public/img/spot_*.webp (400px, with alpha).
import fs from 'node:fs';
import path from 'node:path';
import sharp from 'sharp';

const dir = path.resolve('public/img');
const LO = 14, HI = 60;
for (const f of fs.readdirSync(dir).filter(f => /^spot_.*\.raw\.png$/.test(f))) {
  const name = f.replace(/\.raw\.png$/, '');
  const { data, info } = await sharp(path.join(dir, f)).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  const { width: w, height: h, channels: c } = info;
  // background colour = mean of the four 24px corner patches
  let r = 0, g = 0, b = 0, n = 0;
  for (const [x0, y0] of [[0, 0], [w - 24, 0], [0, h - 24], [w - 24, h - 24]])
    for (let y = y0; y < y0 + 24; y++) for (let x = x0; x < x0 + 24; x++) { const i = (y * w + x) * c; r += data[i]; g += data[i + 1]; b += data[i + 2]; n++; }
  r /= n; g /= n; b /= n;
  for (let i = 0; i < data.length; i += c) {
    const d = Math.sqrt((data[i] - r) ** 2 + (data[i + 1] - g) ** 2 + (data[i + 2] - b) ** 2);
    let a = (d - LO) / (HI - LO); a = a < 0 ? 0 : a > 1 ? 1 : a;
    a = a * a * (3 - 2 * a); // smoothstep
    data[i + 3] = Math.round(a * 255);
    if (a > 0 && a < 1) { // un-premultiply the fringe toward the ink colour so edges don't go pale
      data[i] = Math.round(Math.min(255, Math.max(0, r + (data[i] - r) / a)));
      data[i + 1] = Math.round(Math.min(255, Math.max(0, g + (data[i + 1] - g) / a)));
      data[i + 2] = Math.round(Math.min(255, Math.max(0, b + (data[i + 2] - b) / a)));
    }
  }
  await sharp(data, { raw: { width: w, height: h, channels: 4 } })
    .trim({ threshold: 8 }).resize(400, 400, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
    .extend({ top: 20, bottom: 20, left: 20, right: 20, background: { r: 0, g: 0, b: 0, alpha: 0 } })
    .resize(400, 400)
    .webp({ quality: 85, alphaQuality: 90 }).toFile(path.join(dir, `${name}.webp`));
  console.log('keyed', name, `bg rgb(${r | 0},${g | 0},${b | 0})`);
}
