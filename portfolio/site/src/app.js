// SKOS: boot sequence, desktop icons, a tiny window manager, taskbar, menu.
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const screen = $('#screen'), bootEl = $('#boot'), bootText = $('#boot-text'), desktop = $('#desktop');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const touch = matchMedia('(hover: none)').matches;
  const small = () => innerWidth <= 640;

  // ---- boot --------------------------------------------------------------
  let bootDone = false, bootTimer = null;
  function finishBoot() {
    if (bootDone) return; bootDone = true; clearTimeout(bootTimer);
    bootEl.hidden = true; desktop.hidden = false;
    screen.classList.remove('poweron');
    if (!reduced) { screen.classList.add('degauss'); setTimeout(() => screen.classList.remove('degauss'), 520); }
    if (!openHash()) { let welcomed = false; try { welcomed = sessionStorage.getItem('welcomed') === '1'; } catch {} if (!welcomed) { open('win-about'); try { sessionStorage.setItem('welcomed', '1'); } catch {} } }
  }
  function boot(fast) {
    bootDone = false; desktop.hidden = true; bootEl.hidden = false; bootText.innerHTML = '';
    if (!reduced) { screen.classList.remove('poweron'); void screen.offsetWidth; screen.classList.add('poweron'); }
    if (fast || reduced) { bootText.textContent = window.BOOT.join('\n') + ' ▓▓▓▓▓▓▓▓▓▓ OK'; bootTimer = setTimeout(finishBoot, fast ? 500 : 250); return; }
    const lines = window.BOOT; let i = 0;
    const step = () => {
      if (bootDone) return;
      if (i < lines.length) {
        const l = lines[i++];
        bootText.textContent += (bootText.textContent ? '\n' : '') + l;
        bootTimer = setTimeout(step, l === '' ? 120 : 90 + Math.random() * 220);
      } else {
        let n = 0; const fill = () => {
          if (bootDone) return;
          bootText.textContent = lines.join('\n') + ' ' + '▓'.repeat(n) + '░'.repeat(10 - n);
          if (n++ < 10) bootTimer = setTimeout(fill, 60 + Math.random() * 90);
          else { bootText.textContent += ' OK'; bootTimer = setTimeout(finishBoot, 350); }
        }; fill();
      }
    };
    bootTimer = setTimeout(step, reduced ? 0 : 700);
  }
  screen.addEventListener('animationend', (e) => { if (e.animationName === 'poweron') screen.classList.remove('poweron'); });
  bootEl.addEventListener('click', finishBoot);
  addEventListener('keydown', (e) => { if (!bootDone && !e.metaKey && !e.ctrlKey) { e.preventDefault(); finishBoot(); } }, { capture: true });
  boot(false);
  $('#reboot').addEventListener('click', () => { closeMenu(); wins.forEach((w) => close(w)); boot(false); });

  // ---- window manager ----------------------------------------------------
  const wins = [...document.querySelectorAll('.win')];
  const tasks = $('#tasks');
  let z = 10, cascade = 0, active = null;

  function place(w) {
    if (small()) return;
    const area = $('#wins').getBoundingClientRect();
    const width = Math.min(+w.dataset.w || 720, area.width - 24);
    const x = Math.min(120 + (cascade % 7) * 32, Math.max(12, area.width - width - 12));
    const y = Math.min(28 + (cascade % 7) * 28, Math.max(12, area.height * 0.25));
    cascade++;
    w.style.setProperty('--w', width + 'px'); w.style.left = x + 'px'; w.style.top = y + 'px';
  }
  function focus(w) {
    wins.forEach((o) => o.classList.toggle('blur', o !== w));
    w.style.zIndex = ++z; active = w; renderTasks();
  }
  function open(id) {
    const w = document.getElementById(id); if (!w) return;
    if (w.hidden) { if (!w.dataset.placed) { place(w); w.dataset.placed = '1'; } w.hidden = false; w.dataset.min = ''; }
    focus(w);
    const first = w.querySelector('.win-body'); first.setAttribute('tabindex', '-1'); first.focus({ preventScroll: true });
    history.replaceState(null, '', id.startsWith('win-') ? '#' + id.slice(4) : location.pathname);
  }
  function close(w) { w.hidden = true; w.classList.remove('max'); if (active === w) active = null; renderTasks(); if (location.hash === '#' + w.id.slice(4)) history.replaceState(null, '', location.pathname); }
  function minimize(w) { w.hidden = true; w.dataset.min = '1'; if (active === w) active = null; renderTasks(); }
  function renderTasks() {
    tasks.innerHTML = '';
    wins.filter((w) => !w.hidden || w.dataset.min === '1').forEach((w) => {
      const b = document.createElement('button'); b.className = 'task' + (w === active && !w.hidden ? ' active' : ''); b.type = 'button';
      b.textContent = w.querySelector('.win-name').textContent;
      b.addEventListener('click', () => { if (!w.hidden && w === active) minimize(w); else open(w.id); });
      tasks.appendChild(b);
    });
  }
  wins.forEach((w) => {
    w.addEventListener('pointerdown', () => { if (active !== w) focus(w); });
    w.querySelector('[data-close]').addEventListener('click', () => close(w));
    w.querySelector('[data-min]').addEventListener('click', () => minimize(w));
    w.querySelector('[data-zoom]').addEventListener('click', () => w.classList.toggle('max'));
    // drag by title bar
    const t = w.querySelector('.win-title'); let drag = null;
    t.addEventListener('pointerdown', (e) => {
      if (e.target.closest('.wbtn') || w.classList.contains('max') || small()) return;
      drag = { x: e.clientX - w.offsetLeft, y: e.clientY - w.offsetTop }; t.setPointerCapture(e.pointerId);
    });
    t.addEventListener('pointermove', (e) => {
      if (!drag) return;
      const area = $('#wins').getBoundingClientRect();
      w.style.left = Math.max(-w.offsetWidth + 80, Math.min(area.width - 80, e.clientX - drag.x)) + 'px';
      w.style.top = Math.max(0, Math.min(area.height - 30, e.clientY - drag.y)) + 'px';
    });
    t.addEventListener('pointerup', () => { drag = null; });
    t.addEventListener('dblclick', (e) => { if (!e.target.closest('.wbtn')) w.classList.toggle('max'); });
  });
  addEventListener('keydown', (e) => { if (e.key === 'Escape' && active && !active.hidden) close(active); });

  // ---- icons -------------------------------------------------------------
  const icons = [...document.querySelectorAll('.desk-icon')];
  let selected = null;
  function select(i) { icons.forEach((o) => o.classList.toggle('sel', o === i)); selected = i; }
  // Drag icons around the desktop (mouse/pen only; touch keeps its scrolling grid). Positions persist per browser.
  const iconsEl = $('#icons');
  const KEY = 'skos-icons';
  let iconZ = 1;
  function saved() { try { return JSON.parse(localStorage.getItem(KEY) || 'null'); } catch { return null; } }
  function freeze() {
    if (iconsEl.classList.contains('free')) return;
    const rects = icons.map((i) => i.getBoundingClientRect()); const base = iconsEl.getBoundingClientRect();
    iconsEl.classList.add('free');
    icons.forEach((i, k) => { i.style.left = (rects[k].left - base.left) + 'px'; i.style.top = (rects[k].top - base.top) + 'px'; });
  }
  function persist() { const o = {}; icons.forEach((i) => { o[i.dataset.open] = [parseInt(i.style.left), parseInt(i.style.top)]; }); try { localStorage.setItem(KEY, JSON.stringify(o)); } catch {} }
  function restore() {
    const o = saved(); if (!o || touch || small()) return;
    freeze(); icons.forEach((i) => { const p = o[i.dataset.open]; if (p) { i.style.left = p[0] + 'px'; i.style.top = p[1] + 'px'; } });
  }
  function cleanup() { iconsEl.classList.remove('free'); icons.forEach((i) => { i.style.left = i.style.top = ''; }); try { localStorage.removeItem(KEY); } catch {} }
  $('#cleanup').addEventListener('click', () => { closeMenu(); cleanup(); });
  restore();
  icons.forEach((i) => {
    let d = null;
    i.addEventListener('pointerdown', (e) => {
      if (touch || small() || e.button !== 0) return;
      d = { x: e.clientX, y: e.clientY, moved: false }; select(i);
    });
    i.addEventListener('pointermove', (e) => {
      if (!d) return;
      if (!d.moved) { if (Math.hypot(e.clientX - d.x, e.clientY - d.y) < 5) return; freeze(); d.moved = true; d.ox = i.offsetLeft; d.oy = i.offsetTop; i.classList.add('dragging'); i.style.zIndex = ++iconZ; i.setPointerCapture(e.pointerId); }
      const area = iconsEl.getBoundingClientRect();
      i.style.left = Math.max(0, Math.min(area.width - i.offsetWidth, d.ox + e.clientX - d.x)) + 'px';
      i.style.top = Math.max(0, Math.min(area.height - i.offsetHeight, d.oy + e.clientY - d.y)) + 'px';
    });
    const end = () => { if (d && d.moved) { i.classList.remove('dragging'); persist(); } d = null; };
    i.addEventListener('pointerup', end); i.addEventListener('pointercancel', end);
  });
  icons.forEach((i) => {
    i.addEventListener('click', () => { select(i); if (touch) open(i.dataset.open); });
    i.addEventListener('dblclick', () => open(i.dataset.open));
    i.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(i.dataset.open); } });
    i.setAttribute('title', touch ? 'Tap to open' : 'Double-click to open');
  });
  desktop.addEventListener('pointerdown', (e) => { if (e.target === desktop || e.target.id === 'icons') select(null); });
  addEventListener('resize', () => { if (iconsEl.classList.contains('free') && small()) cleanup(); });
  document.querySelectorAll('.win [data-open], .menu [data-open]').forEach((b) => b.addEventListener('click', () => { closeMenu(); open(b.dataset.open); }));

  // ---- menu + clock ------------------------------------------------------
  const start = $('#start'), menu = $('#menu');
  function closeMenu() { menu.hidden = true; start.setAttribute('aria-expanded', 'false'); }
  start.addEventListener('click', () => { const o = menu.hidden; menu.hidden = !o; start.setAttribute('aria-expanded', String(o)); if (o) menu.querySelector('[role=menuitem]').focus(); });
  document.addEventListener('pointerdown', (e) => { if (!menu.hidden && !e.target.closest('#menu, #start')) closeMenu(); });
  addEventListener('keydown', (e) => { if (e.key === 'Escape' && !menu.hidden) { closeMenu(); start.focus(); } });
  const clock = $('#clock');
  const tick = () => { const d = new Date(); clock.textContent = d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }); };
  tick(); setInterval(tick, 15000);

  // ---- deep links: /#slug opens that project after boot ------------------
  function openHash() { const s = location.hash.slice(1); if (s && document.getElementById('win-' + s)) { open('win-' + s); return true; } return false; }
  addEventListener('hashchange', () => { if (bootDone) openHash(); });
})();
