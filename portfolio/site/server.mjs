// Tiny static server for dist/. No dependencies. Railway sets PORT.
import { createServer } from 'node:http';
import { stat, readFile } from 'node:fs/promises';
import { join, extname, normalize } from 'node:path';

const root = new URL('./dist/', import.meta.url).pathname;
const port = Number(process.env.PORT || 3000);
const types = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.webp': 'image/webp', '.svg': 'image/svg+xml', '.ico': 'image/x-icon', '.txt': 'text/plain; charset=utf-8',
  '.mp4': 'video/mp4', '.webm': 'video/webm', '.woff2': 'font/woff2',
};

createServer(async (req, res) => {
  let path = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (path.endsWith('/')) path += 'index.html';
  const file = normalize(join(root, path));
  if (!file.startsWith(root)) { res.writeHead(403); return res.end(); }
  try {
    let target = file;
    let s = await stat(target).catch(() => null);
    if (s?.isDirectory()) { target = join(target, 'index.html'); s = await stat(target); }
    if (!s) throw new Error('missing');
    const ext = extname(target);
    const immutable = /^\/(shots|art|assets)\//.test(path);
    res.writeHead(200, {
      'content-type': types[ext] || 'application/octet-stream',
      'content-length': s.size,
      'cache-control': immutable ? 'public, max-age=31536000, immutable' : 'public, max-age=300',
    });
    res.end(await readFile(target));
  } catch {
    res.writeHead(404, { 'content-type': 'text/html; charset=utf-8' });
    res.end(await readFile(join(root, '404.html')).catch(() => 'Not found'));
  }
}).listen(port, () => console.log(`serving ${root} on :${port}`));
