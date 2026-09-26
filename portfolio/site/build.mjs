// Static build: projects.json + src/ + public/ -> dist/. No dependencies.
// Output is a single-screen "SKOS" desktop: boot sequence, icons, windows, taskbar.
import { readFile, writeFile, mkdir, rm, cp, access } from 'node:fs/promises';
import { join } from 'node:path';

const here = new URL('.', import.meta.url).pathname;
const dist = join(here, 'dist');
const { site, projects } = JSON.parse(await readFile(join(here, 'projects.json'), 'utf8'));

await rm(dist, { recursive: true, force: true });
await mkdir(dist, { recursive: true });
await cp(join(here, 'public'), dist, { recursive: true });
await cp(join(here, 'src/style.css'), join(dist, 'style.css'));
await cp(join(here, 'src/app.js'), join(dist, 'app.js'));

const exists = (p) => access(join(dist, p)).then(() => true, () => false);
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const accents = { play: '#e4552f', bet: '#2f8f5b', read: '#3b6fd6', also: '#b8862b' };
const statusLabel = { live: 'live', staging: 'staging', paused: 'paused', retired: 'retired', unlinked: 'no link yet' };
const groupLabel = (k) => site.groups.find((g) => g.key === k)?.label || k;
const initials = (name) => name.split(/[\s-]+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join('').toUpperCase();

for (const p of projects) {
  p.accent = accents[p.group];
  p.wide = p.wide || ((await exists(`shots/${p.slug}.webp`)) ? `/shots/${p.slug}.webp` : null);
  p.external = p.url && /^https?:/.test(p.url);
}

const avatar = (await exists('art/avatar.png')) ? '/art/avatar.png' : null;

// Pixel cartridge icon, coloured by group, with a monogram label.
const cartridge = (p) => `
<svg class="ico" viewBox="0 0 32 32" aria-hidden="true" shape-rendering="crispEdges">
  <rect x="4" y="2" width="24" height="26" fill="#2a2622"/>
  <rect x="5" y="3" width="22" height="24" fill="#3d3833"/>
  <rect x="6" y="28" width="20" height="2" fill="#2a2622"/>
  <rect x="8" y="5" width="16" height="12" fill="${p.accent}"/>
  <rect x="8" y="5" width="16" height="1" fill="rgba(255,255,255,.35)"/>
  <rect x="9" y="19" width="14" height="1" fill="#57514a"/><rect x="9" y="21" width="14" height="1" fill="#57514a"/><rect x="9" y="23" width="14" height="1" fill="#57514a"/>
  <text x="16" y="14.5" text-anchor="middle" font-family="Pixelify Sans, monospace" font-size="10" font-weight="700" fill="#fff">${esc(initials(p.name))}</text>
</svg>`;

const fileIcon = (kind) => ({
  txt: `<svg class="ico" viewBox="0 0 32 32" aria-hidden="true" shape-rendering="crispEdges"><path d="M7 2h13l6 6v22H7z" fill="#f4efe6" stroke="#2a2622" stroke-width="1"/><path d="M20 2v6h6" fill="#d8d4c8" stroke="#2a2622" stroke-width="1"/><rect x="10" y="12" width="12" height="1" fill="#57514a"/><rect x="10" y="15" width="12" height="1" fill="#57514a"/><rect x="10" y="18" width="9" height="1" fill="#57514a"/><rect x="10" y="21" width="12" height="1" fill="#57514a"/><rect x="10" y="24" width="7" height="1" fill="#57514a"/></svg>`,
  ledger: `<svg class="ico" viewBox="0 0 32 32" aria-hidden="true" shape-rendering="crispEdges"><rect x="3" y="4" width="26" height="24" fill="#f4efe6" stroke="#2a2622"/><rect x="3" y="4" width="26" height="5" fill="#2f8f5b"/><rect x="6" y="12" width="20" height="1" fill="#57514a"/><rect x="6" y="16" width="20" height="1" fill="#57514a"/><rect x="6" y="20" width="20" height="1" fill="#57514a"/><rect x="6" y="24" width="20" height="1" fill="#57514a"/><rect x="12" y="9" width="1" height="19" fill="#57514a"/></svg>`,
  trash: `<svg class="ico" viewBox="0 0 32 32" aria-hidden="true" shape-rendering="crispEdges"><rect x="12" y="3" width="8" height="3" fill="#8f8a7e"/><rect x="6" y="6" width="20" height="3" fill="#8f8a7e" stroke="#2a2622"/><path d="M8 10h16l-2 19H10z" fill="#c9c4b8" stroke="#2a2622"/><rect x="12" y="13" width="1" height="13" fill="#57514a"/><rect x="16" y="13" width="1" height="13" fill="#57514a"/><rect x="20" y="13" width="1" height="13" fill="#57514a"/></svg>`,
  link: `<svg class="ico" viewBox="0 0 32 32" aria-hidden="true" shape-rendering="crispEdges"><rect x="3" y="6" width="26" height="20" fill="#3b6fd6" stroke="#2a2622"/><rect x="3" y="6" width="26" height="4" fill="#2a2622"/><rect x="6" y="14" width="20" height="2" fill="#fff"/><rect x="6" y="19" width="12" height="2" fill="#fff"/></svg>`,
})[kind];

const icon = (id, label, svg, extra = '') => `
<button class="desk-icon" type="button" data-open="${id}" ${extra}>
  ${svg}
  <span class="ico-label">${esc(label)}</span>
</button>`;

const chips = (arr) => (arr || []).map((t) => `<span class="chip">${esc(t)}</span>`).join('');

const win = (id, title, body, opts = {}) => `
<section class="win ${opts.cls || ''}" id="${id}" hidden role="dialog" aria-labelledby="${id}-t" style="--accent:${opts.accent || '#3d3833'}" data-w="${opts.w || 720}">
  <header class="win-title">
    <button class="wbtn close" type="button" data-close aria-label="Close"></button>
    <span class="win-name" id="${id}-t">${esc(title)}</span>
    <span class="win-ctl"><button class="wbtn min" type="button" data-min aria-label="Minimize"></button><button class="wbtn zoom" type="button" data-zoom aria-label="Zoom"></button></span>
  </header>
  <div class="win-body">${body}</div>
</section>`;

const projectWin = (p) => win(`win-${p.slug}`, p.name, `
  ${p.wide ? `<img class="shot" src="${p.wide}" alt="Screenshot of ${esc(p.name)}" loading="lazy">` : ''}
  <div class="doc">
    <p class="eyebrow">${esc(groupLabel(p.group))} · ${esc(p.year)} · <span class="dot ${p.status}"></span>${statusLabel[p.status] || p.status}</p>
    <h2>${esc(p.name)}</h2>
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
  </div>`, { accent: p.accent, w: 760 });

const ledgerWin = win('win-ledger', 'All projects', `
  <table class="ledger">
    <thead><tr><th>#</th><th>Project</th><th class="what">What</th><th>Group</th><th>Built with</th><th>Status</th><th>Year</th></tr></thead>
    <tbody>${projects.map((p, i) => `
      <tr style="--accent:${p.accent}">
        <td class="n">${String(i + 1).padStart(2, '0')}</td>
        <td><button class="linkish" type="button" data-open="win-${p.slug}">${esc(p.name)}</button></td>
        <td class="what">${esc(p.one)}</td>
        <td><span class="tag">${esc(groupLabel(p.group))}</span></td>
        <td class="mono">${esc(p.tools.join(' → '))}</td>
        <td><span class="dot ${p.status}"></span>${statusLabel[p.status] || p.status}</td>
        <td class="mono">${esc(p.year)}</td>
      </tr>`).join('')}
    </tbody>
  </table>`, { w: 900, cls: 'win-ledger' });

const aboutWin = win('win-about', 'README.txt', `
  <div class="doc">
    ${avatar ? `<img class="avatar" src="${avatar}" alt="Pixel-art portrait of ${esc(site.name)}" width="96" height="96">` : ''}
    <h2>${esc(site.name)}</h2>
    <p class="one">${esc(site.tagline)}</p>
    <p>${esc(site.intro)}</p>
    <p>I work at the seam between technical systems and the people who have to understand them. These projects are where I test ideas end to end: design, build, ship, and see who shows up. Each window lists the tools it was built with.</p>
    <p class="links"><a class="btn" href="${esc(site.github)}" target="_blank" rel="noopener">GitHub ↗</a><a class="btn" href="${esc(site.substack)}" target="_blank" rel="noopener">Substack ↗</a></p>
    <p class="mono small">Double-click a cartridge to open it. Drag icons and windows anywhere. The SKOS menu lists everything.</p>
  </div>`, { w: 560 });

const trashWin = win('win-trash', 'Trash', `
  <div class="doc">
    <p class="mono small">3 items. Recovered fragments of things that didn't make it.</p>
    <ul class="trash-list">
      <li><span class="mono">crucible.exe</span><span>An agent-governed evolution sim. I no longer remember what it was for.</span></li>
      <li><span class="mono">feed-unfucker</span><span>A calmer social feed by email. Never shipped.</span></li>
      <li><span class="mono">culty-clicker</span><span>A Replit-era clicker. The repo is empty.</span></li>
    </ul>
  </div>`, { w: 520 });

const groups = site.groups.map((g) => ({ ...g, items: projects.filter((p) => p.group === g.key) })).filter((g) => g.items.length);

const bootLines = [
  'SK-2600 BIOS  v2.6',
  'Copyright (C) 1994-2026 Kemmis Systems',
  '',
  'Memory test ........ 640K OK',
  `Detecting cartridges ...... ${projects.length} found`,
  ...groups.map((g) => `  ${g.label.toLowerCase().padEnd(6)} ${String(g.items.length).padStart(2)}`),
  '',
  'Loading SKOS',
];

const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>${esc(site.name)}</title>
<meta name="description" content="${esc(site.tagline)}">
<meta property="og:title" content="${esc(site.name)}">
<meta property="og:description" content="${esc(site.tagline)}">
<meta name="theme-color" content="#0a100c">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=VT323&family=Pixelify+Sans:wght@400;700&family=IBM+Plex+Sans:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css">
<script>window.BOOT=${JSON.stringify(bootLines)};</script>
</head>
<body>
<div class="crt" id="crt">
  <div class="screen" id="screen">

    <div class="boot" id="boot" aria-live="polite"><pre id="boot-text"></pre><p class="boot-skip">press any key or tap to skip</p></div>

    <div class="desktop" id="desktop" hidden>
      <div class="icons" id="icons">
        ${groups.map((g) => g.items.map((p) => icon(`win-${p.slug}`, p.name, cartridge(p), `data-group="${g.key}"`)).join('')).join('')}
        ${icon('win-about', 'README.txt', fileIcon('txt'))}
        ${icon('win-ledger', 'All projects', fileIcon('ledger'))}
        ${icon('win-trash', 'Trash', fileIcon('trash'))}
      </div>

      <div class="wins" id="wins">
        ${projects.map(projectWin).join('')}
        ${aboutWin}
        ${ledgerWin}
        ${trashWin}
      </div>

      <nav class="taskbar" aria-label="Taskbar">
        <button class="start" id="start" type="button" aria-haspopup="menu" aria-expanded="false">${avatar ? `<img class="start-av" src="${avatar}" alt="">` : '<span class="start-dot"></span>'}SKOS</button>
        <div class="tasks" id="tasks"></div>
        <span class="clock mono" id="clock" aria-live="off"></span>
      </nav>
      <div class="menu" id="menu" hidden role="menu">
        ${groups.map((g) => `<div class="menu-group"><span class="menu-h" style="--accent:${accents[g.key]}">${esc(g.label)}</span>${g.items.map((p) => `<button role="menuitem" type="button" data-open="win-${p.slug}">${esc(p.name)}</button>`).join('')}</div>`).join('')}
        <div class="menu-group"><span class="menu-h">System</span>
          <button role="menuitem" type="button" data-open="win-about">README.txt</button>
          <button role="menuitem" type="button" data-open="win-ledger">All projects</button>
          <a role="menuitem" href="${esc(site.github)}" target="_blank" rel="noopener">GitHub ↗</a>
          <a role="menuitem" href="${esc(site.substack)}" target="_blank" rel="noopener">Substack ↗</a>
          <button role="menuitem" type="button" id="cleanup">Clean up desktop</button>
          <button role="menuitem" type="button" id="reboot">Restart…</button>
        </div>
      </div>
    </div>

    <div class="scanlines" aria-hidden="true"></div>
    <div class="vignette" aria-hidden="true"></div>
  </div>
</div>
<noscript><main class="plain"><h1>${esc(site.name)}</h1><p>${esc(site.tagline)}</p><ul>${projects.map((p) => `<li><a href="${esc(p.url || '#')}">${esc(p.name)}</a>: ${esc(p.one)}</li>`).join('')}</ul></main></noscript>
<script src="/app.js" defer></script>
</body>
</html>`;

await writeFile(join(dist, 'index.html'), html);
await writeFile(join(dist, '404.html'), `<!doctype html><meta charset="utf-8"><title>Not found</title><link rel="stylesheet" href="/style.css"><body class="plain"><main class="plain"><h1>404</h1><p>No cartridge at that address. <a href="/">Back to the desktop.</a></p></main>`);
await writeFile(join(dist, 'favicon.svg'), `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="10" fill="#1a1712"/><rect x="8" y="10" width="48" height="36" rx="4" fill="#0a100c" stroke="#3d3833" stroke-width="3"/><rect x="14" y="18" width="20" height="4" fill="#8cff9f"/><rect x="14" y="26" width="30" height="4" fill="#8cff9f"/><rect x="24" y="50" width="16" height="5" rx="2" fill="#3d3833"/></svg>`);
console.log(`built ${projects.length} projects → dist/ (${projects.filter((p) => p.wide).length} with screenshots)`);
