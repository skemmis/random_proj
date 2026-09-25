// Tiny HTML helpers. No template engine: pages are plain functions returning strings.
const esc = (s) => String(s ?? '')
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  .replace(/"/g, '&quot;').replace(/'/g, '&#39;');

const attrs = (o) => Object.entries(o || {})
  .filter(([, v]) => v !== false && v != null)
  .map(([k, v]) => v === true ? ` ${k}` : ` ${k}="${esc(v)}"`).join('');

// Pre-optimised illustration: <picture> with a small and a large webp.
function pic(name, { alt = '', cls = '', sizes = '100vw', eager = false, width, height } = {}) {
  return `<img src="/img/${name}.webp" srcset="/img/${name}-sm.webp 800w, /img/${name}.webp 1600w" sizes="${esc(sizes)}" alt="${esc(alt)}" class="${esc(cls)}"${eager ? ' fetchpriority="high"' : ' loading="lazy"'} decoding="async"${width ? ` width="${width}" height="${height}"` : ''}>`;
}

function spot(name, cls = '') {
  return `<img src="/img/${name}.webp" alt="" class="spot ${esc(cls)}" width="200" height="200" loading="lazy" decoding="async">`;
}

module.exports = { esc, attrs, pic, spot };
