/* section.js: the one script a page includes so it can run inside the 6:11 p.m. spine.
   Opened on its own, a page that includes this behaves exactly as before: Spine.embedded is false and register() does nothing.
   Opened inside the spine (an <iframe data-spine> on the same origin), it:
     - marks <html> with the class "in-spine", so the page's CSS can hide its own sound prompt, Begin links and the like;
     - stops the reader scrolling the page directly; the spine scrolls it instead, so a scroll-driven page keeps reading
       window.scrollY exactly as it does on its own;
     - passes the reader's wheel, touch and keyboard scrolling up to the spine;
     - hands the page's hooks (register) to the spine.
   Include it before the page's own script: <script src="../../section.js"></script> */
(function () {
  let host = null, frame = null;
  try { frame = window.frameElement; if (frame && frame.hasAttribute('data-spine') && window.parent.SpineHost) host = window.parent.SpineHost; } catch (e) { host = null; }

  const Spine = window.Spine = {
    embedded: !!host,
    get sound() { return host ? host.sound : false; },   // the reader's choice at the spine's sound prompt, kept current
    register() {},                         // standalone pages: a no-op
    done() {},                             // a played section calls this when it has finished, so the spine can invite the reader on
    host
  };
  if (!host) return;

  document.documentElement.classList.add('in-spine');
  const st = document.createElement('style');
  // only the root: overflow on <html> applies to the viewport, while overflow on <body> as well would make the body its own scroller and break position: sticky
  st.textContent = 'html.in-spine { overflow: hidden !important; overscroll-behavior: none; scrollbar-width: none; } html.in-spine::-webkit-scrollbar { display: none; }';
  (document.head || document.documentElement).appendChild(st);

  Spine.register = hooks => host.register(frame, hooks || {});
  Spine.done = () => host.done(frame);

  // scrolling over the section moves the whole piece, never the section on its own
  addEventListener('wheel', e => { if (e.ctrlKey) return; e.preventDefault(); host.wheel(e.deltaY * (e.deltaMode === 1 ? 32 : e.deltaMode === 2 ? innerHeight : 1)); }, { passive: false });
  let ty = null;
  // controls that need a finger of their own (a slider, a button, anything marked data-own-touch) keep it
  addEventListener('touchstart', e => { const own = e.target.closest && e.target.closest('input, button, select, [data-own-touch]'); ty = !own && e.touches.length === 1 ? e.touches[0].clientY : null; if (ty !== null) host.touch('start'); }, { passive: true });
  addEventListener('touchmove', e => { if (ty === null) return; const y = e.touches[0].clientY; e.preventDefault(); host.touch('move', ty - y); ty = y; }, { passive: false });
  addEventListener('touchend', () => { ty = null; host.touch('end'); }, { passive: true });
  addEventListener('keydown', e => {
    const t = e.target; if (t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))) return;
    if (host.key(e.key, e.shiftKey)) e.preventDefault();
  });
})();
