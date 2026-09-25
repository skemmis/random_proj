// Static build: projects.json + src/ + public/ -> dist/. No dependencies.
import { readFile, writeFile, mkdir, rm, cp, access } from 'node:fs/promises';
import { join } from 'node:path';

const here = new URL('.', import.meta.url).pathname;
const dist = join(here, 'dist');
const data = JSON.parse(await readFile(join(here, 'projects.json'), 'utf8'));
const { site, projects } = data;

await rm(dist, { recursive: true, force: true });
await mkdir(dist, { recursive: true });
await cp(join(here, 'public'), dist, { recursive: true });
await cp(join(here, 'src/style.css'), join(dist, 'style.css'));
await cp(join(here, 'src/app.js'), join(dist, 'app.js'));

const exists = (p) => access(join(dist, p)).then(() => true, () => false);
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const accents = { play: '#e4552f', bet: '#2f8f5b', read: '#3b6fd6', also: '#b8862b' };
const statusLabel = { live: 'live', staging: 'staging', paused: 'paused', retired: 'retired', unlinked: 'no link yet' };

const initials = (name) => name.split(/[\s-]+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join('').toUpperCase();

// Fallback box art: a monogram on the group colour, with a faint dot grid.
const monogram = (p) => `
<svg class="mono-art" viewBox="0 0 400 400" role="img" aria-label="${esc(p.name)}">
  <rect width="400" height="400" fill="${accents[p.group]}"/>
  <g fill="rgba(255,255,255,.18)">${Array.from({ length: 8 }, (_, r) => Array.from({ length: 8 }, (_, c) => `<circle cx="${25 + c * 50}" cy="${25 + r * 50}" r="2"/>`).join('')).join('')}</g>
  <text x="200" y="228" text-anchor="middle" font-family="Bricolage Grotesque, system-ui, sans-serif" font-weight="800" font-size="150" fill="#fff" letter-spacing="-8">${esc(initials(p.name))}</text>
  <text x="200" y="330" text-anchor="middle" font-family="JetBrains Mono, ui-monospace, monospace" font-size="18" fill="rgba(255,255,255,.75)" letter-spacing="3">${esc(p.year.toUpperCase())}</text>
</svg>`;

for (const p of projects) {
  p.accent = accents[p.group];
  p.sq = p.sq || ((await exists(`shots/${p.slug}-sq.webp`)) ? `/shots/${p.slug}-sq.webp` : null);
  p.wide = p.wide || ((await exists(`shots/${p.slug}.webp`)) ? `/shots/${p.slug}.webp` : null);
  p.external = p.url && /^https?:/.test(p.url);
}

const tile = (p, i) => `
<li>
  <button class="tile" type="button" data-slug="${p.slug}" data-name="${esc(p.name)}" data-one="${esc(p.one)}" ${p.wide ? `data-wide="${p.wide}"` : ''} style="--accent:${p.accent}" aria-haspopup="dialog" aria-controls="dlg-${p.slug}">
    <span class="box">${p.sq ? `<img src="${p.sq}" alt="" loading="lazy" width="400" height="400">` : monogram(p)}</span>
    <span class="label">
      <span class="name">${esc(p.name)}</span>
      <span class="meta"><span class="num">${String(i + 1).padStart(2, '0')}</span><span class="dot ${p.status}"></span>${statusLabel[p.status] || p.status}</span>
    </span>
  </button>
</li>`;

const chips = (arr) => arr.map((t) => `<span class="chip">${esc(t)}</span>`).join('');

const dialog = (p) => `
<dialog id="dlg-${p.slug}" class="detail" style="--accent:${p.accent}" aria-labelledby="dlg-${p.slug}-h">
  <form method="dialog" class="detail-close"><button type="submit" aria-label="Close">×</button></form>
  <div class="detail-art">${p.wide ? `<img src="${p.wide}" alt="Screenshot of ${esc(p.name)}" loading="lazy">` : monogram(p)}</div>
  <div class="detail-body">
    <p class="eyebrow">${esc(site.groups.find((g) => g.key === p.group)?.label || p.group)} · ${esc(p.year)} · <span class="dot ${p.status}"></span>${statusLabel[p.status] || p.status}</p>
    <h2 id="dlg-${p.slug}-h">${esc(p.name)}</h2>
    <p class="one">${esc(p.one)}</p>
    <p>${esc(p.description)}</p>
    ${p.notes ? `<p class="note">${esc(p.notes)}</p>` : ''}
    <div class="chips"><span class="chips-k">built with</span>${chips(p.tools)}</div>
    <div class="chips"><span class="chips-k">stack</span>${chips(p.stack)}</div>
    <p class="links">
      ${p.url ? `<a class="btn primary" href="${esc(p.url)}" ${p.external ? 'target="_blank" rel="noopener"' : ''}>${p.external ? 'Launch ↗' : 'Open'}</a>` : `<span class="btn disabled">No public link yet</span>`}
      ${p.repo ? `<a class="btn" href="${esc(p.repo)}" target="_blank" rel="noopener">Code</a>` : ''}
      ${(p.links || []).map((l) => `<a class="btn" href="${esc(l.url)}" target="_blank" rel="noopener">${esc(l.label)} ↗</a>`).join('')}
    </p>
  </div>
</dialog>`;

const row = (p, i) => `
<tr style="--accent:${p.accent}">
  <td class="n">${String(i + 1).padStart(2, '0')}</td>
  <td><button class="linkish" type="button" data-open="dlg-${p.slug}">${esc(p.name)}</button></td>
  <td class="what">${esc(p.one)}</td>
  <td><span class="tag">${esc(site.groups.find((g) => g.key === p.group)?.label)}</span></td>
  <td class="mono">${esc(p.tools.join(' → '))}</td>
  <td><span class="dot ${p.status}"></span>${statusLabel[p.status] || p.status}</td>
  <td class="mono">${esc(p.year)}</td>
  <td class="mono">${p.url ? `<a href="${esc(p.url)}" ${p.external ? 'target="_blank" rel="noopener"' : ''}>${p.external ? 'launch ↗' : 'open'}</a>` : '—'}${p.repo ? ` · <a href="${esc(p.repo)}" target="_blank" rel="noopener">code</a>` : ''}</td>
</tr>`;

const groups = site.groups.map((g) => ({ ...g, items: projects.filter((p) => p.group === g.key) })).filter((g) => g.items.length);
let n = 0;
const shelf = groups.map((g) => `
<section class="group" id="${g.key}" style="--accent:${accents[g.key]}">
  <header class="group-head"><h2>${esc(g.label)}</h2><p>${esc(g.blurb)}</p></header>
  <ul class="grid">${g.items.map((p) => tile(p, n++)).join('')}</ul>
</section>`).join('');

const featured = projects.filter((p) => p.featured && p.wide).map((p) => ({ slug: p.slug, name: p.name, one: p.one, wide: p.wide }));

const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(site.name)}</title>
<meta name="description" content="${esc(site.tagline)}">
<meta property="og:title" content="${esc(site.name)}">
<meta property="og:description" content="${esc(site.tagline)}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css">
<script>window.FEATURED=${JSON.stringify(featured)};</script>
</head>
<body>
<a class="skip" href="#shelf">Skip to projects</a>
<header class="masthead">
  <div class="masthead-row">
    <h1>${esc(site.name)}</h1>
    <nav class="topnav" aria-label="Elsewhere">
      <a href="${esc(site.github)}" target="_blank" rel="noopener">GitHub</a>
      <a href="${esc(site.substack)}" target="_blank" rel="noopener">Substack</a>
    </nav>
  </div>
  <p class="tagline">${esc(site.tagline)}</p>
</header>

<section class="crt-wrap" aria-label="Preview">
  <div class="crt">
    <div class="bezel">
      <div class="screen" id="screen">
        <div class="boot" id="boot" aria-live="polite">
          <pre>SAMKEMMIS OS  v1.0
${String(projects.length).padStart(2, ' ')} projects loaded
${groups.map((g) => `  ${g.label.toLowerCase().padEnd(6)} ${String(g.items.length).padStart(2)}`).join('\n')}

ready. hover a cartridge<span class="cursor">▮</span></pre>
        </div>
        <div class="preview" id="preview" hidden>
          <img id="preview-img" alt="">
          <div class="preview-cap"><b id="preview-name"></b><span id="preview-one"></span></div>
        </div>
        <div class="scanlines" aria-hidden="true"></div>
        <div class="glare" aria-hidden="true"></div>
      </div>
      <div class="bezel-foot"><span class="led" aria-hidden="true"></span><span class="brand">SK-2600</span></div>
    </div>
  </div>
</section>

<div class="wrap">
<p class="intro">${esc(site.intro)}</p>
<div class="viewbar" role="tablist" aria-label="View">
  <button role="tab" type="button" aria-selected="true" data-view="shelf">Shelf</button>
  <button role="tab" type="button" aria-selected="false" data-view="ledger">Ledger</button>
</div>
</div>

<main id="shelf" class="view">
${shelf}
</main>

<div id="ledger" class="view" hidden>
  <table class="ledger">
    <thead><tr><th>#</th><th>Project</th><th class="what">What</th><th>Group</th><th>Built with</th><th>Status</th><th>Year</th><th>Links</th></tr></thead>
    <tbody>${projects.map(row).join('')}</tbody>
  </table>
</div>

${projects.map(dialog).join('')}

<footer class="foot">
  <p>Every project here was written with an AI coding agent, mostly Claude Code, a couple in Lovable and Replit. The ideas, the taste, and the bugs I chose to live with are mine.</p>
  <p class="mono">© ${new Date().getFullYear()} ${esc(site.name)} · <a href="${esc(site.github)}">github.com/skemmis</a></p>
</footer>
<script src="/app.js" defer></script>
</body>
</html>`;

await writeFile(join(dist, 'index.html'), html);
await writeFile(join(dist, '404.html'), `<!doctype html><meta charset="utf-8"><title>Not found</title><link rel="stylesheet" href="/style.css"><body class="plain"><main class="intro"><h1>404</h1><p>Nothing on this shelf at that address. <a href="/">Back to the projects.</a></p></main>`);
await writeFile(join(dist, 'favicon.svg'), `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#1a1712"/><rect x="10" y="12" width="44" height="32" rx="4" fill="#2f8f5b"/><rect x="24" y="48" width="16" height="6" rx="2" fill="#f4efe6"/></svg>`);
console.log(`built ${projects.length} projects → dist/ (${projects.filter((p) => p.sq).length} with screenshots)`);
