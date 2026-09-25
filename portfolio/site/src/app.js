// Shelf behaviour: CRT preview on hover, dialogs on click, shelf/ledger toggle.
(() => {
  const screen = document.getElementById('screen');
  const boot = document.getElementById('boot');
  const preview = document.getElementById('preview');
  const img = document.getElementById('preview-img');
  const name = document.getElementById('preview-name');
  const one = document.getElementById('preview-one');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const canHover = matchMedia('(hover: hover)').matches;
  if (!reduced) screen.classList.add('flicker');

  let idle;
  function show(t) {
    clearTimeout(idle);
    if (!t.dataset.wide) return showBoot();
    if (img.getAttribute('src') !== t.dataset.wide) img.src = t.dataset.wide;
    name.textContent = t.dataset.name;
    one.textContent = t.dataset.one;
    boot.hidden = true; preview.hidden = false;
  }
  function showBoot() { preview.hidden = true; boot.hidden = false; }

  const tiles = [...document.querySelectorAll('.tile')];
  tiles.forEach((t) => {
    t.addEventListener('pointerenter', () => show(t));
    t.addEventListener('focus', () => show(t));
    t.addEventListener('pointerleave', () => { idle = setTimeout(showBoot, 1800); });
    t.addEventListener('click', () => open(t.getAttribute('aria-controls')));
  });

  // Touch devices: no hover, so rotate the featured projects on the screen.
  if (!canHover && window.FEATURED && window.FEATURED.length) {
    let i = 0;
    const tick = () => { const f = window.FEATURED[i++ % window.FEATURED.length]; show({ dataset: { wide: f.wide, name: f.name, one: f.one } }); };
    setTimeout(() => { tick(); if (!reduced) setInterval(tick, 4500); }, 1500);
  }

  function open(id) {
    const d = document.getElementById(id);
    if (!d) return;
    d.showModal();
    d.addEventListener('click', (e) => { if (e.target === d) d.close(); }, { once: true });
  }
  document.querySelectorAll('[data-open]').forEach((b) => b.addEventListener('click', () => open(b.dataset.open)));

  // Deep link: #slug opens that project.
  const openHash = () => { const s = location.hash.slice(1); if (s && document.getElementById('dlg-' + s)) open('dlg-' + s); };
  openHash(); addEventListener('hashchange', openHash);

  // Shelf / ledger toggle, remembered per browser.
  const tabs = [...document.querySelectorAll('.viewbar [data-view]')];
  const views = { shelf: document.getElementById('shelf'), ledger: document.getElementById('ledger') };
  function setView(v) {
    tabs.forEach((t) => t.setAttribute('aria-selected', String(t.dataset.view === v)));
    Object.entries(views).forEach(([k, el]) => { el.hidden = k !== v; });
    try { localStorage.setItem('view', v); } catch {}
  }
  tabs.forEach((t) => t.addEventListener('click', () => setView(t.dataset.view)));
  let saved = null; try { saved = localStorage.getItem('view'); } catch {}
  if (saved === 'ledger') setView('ledger');
})();
