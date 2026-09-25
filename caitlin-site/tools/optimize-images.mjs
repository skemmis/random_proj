// Converts public/img/*.raw.png into web-ready webp files:
//   name.webp (max 1600w), name-sm.webp (800w), spot_*.webp (400px square).
import fs from 'node:fs';
import path from 'node:path';
import sharp from 'sharp';

const dir = path.resolve('public/img');
const raws = fs.readdirSync(dir).filter(f => f.endsWith('.raw.png'));
for (const f of raws) {
  const name = f.replace(/\.raw\.png$/, '');
  const src = path.join(dir, f);
  if (name.startsWith('spot_')) {
    await sharp(src).resize(400, 400, { fit: 'cover' }).webp({ quality: 82 }).toFile(path.join(dir, `${name}.webp`));
  } else {
    await sharp(src).resize({ width: 1600, withoutEnlargement: true }).webp({ quality: 80 }).toFile(path.join(dir, `${name}.webp`));
    await sharp(src).resize({ width: 800 }).webp({ quality: 78 }).toFile(path.join(dir, `${name}-sm.webp`));
  }
  console.log('optimised', name);
}
