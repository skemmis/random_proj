(function () {
  // Mobile nav
  var toggle = document.querySelector('[data-nav-toggle]');
  var nav = document.getElementById('site-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!open));
      document.body.classList.toggle('nav-open', !open);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && document.body.classList.contains('nav-open')) {
        toggle.setAttribute('aria-expanded', 'false');
        document.body.classList.remove('nav-open');
        toggle.focus();
      }
    });
  }

  // Hide the sticky mobile CTA when the hero CTA or the form is on screen, and on the schedule page.
  var sticky = document.querySelector('[data-sticky-cta]');
  if (sticky && 'IntersectionObserver' in window) {
    var targets = document.querySelectorAll('[data-cta-anchor]');
    if (!targets.length) { sticky.classList.add('is-visible'); }
    else {
      var visible = 0;
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) { visible += en.isIntersecting ? 1 : -1; });
        visible = Math.max(0, visible);
        sticky.classList.toggle('is-visible', visible === 0);
      }, { rootMargin: '0px 0px -40px 0px' });
      targets.forEach(function (t) { io.observe(t); });
    }
  }

  // Schedule form: show/hide the address field for home visits, remember the visit type from the URL.
  var form = document.querySelector('[data-schedule-form]');
  if (form) {
    var type = form.querySelector('[name=visitType]');
    var homeWrap = form.querySelector('[data-home-only]');
    function syncHome() {
      if (!type || !homeWrap) return;
      var isHome = type.value === 'home';
      homeWrap.hidden = !isHome;
      var input = homeWrap.querySelector('input');
      if (input) input.required = isHome;
    }
    if (type) { type.addEventListener('change', syncHome); syncHome(); }

    // Friendlier phone formatting
    var phone = form.querySelector('[name=phone]');
    if (phone) phone.addEventListener('input', function () {
      var d = phone.value.replace(/\D/g, '').slice(0, 10);
      var out = d;
      if (d.length > 6) out = '(' + d.slice(0, 3) + ') ' + d.slice(3, 6) + '-' + d.slice(6);
      else if (d.length > 3) out = '(' + d.slice(0, 3) + ') ' + d.slice(3);
      phone.value = out;
    });

    form.addEventListener('submit', function () {
      var btn = form.querySelector('button[type=submit]');
      if (btn) { btn.disabled = true; btn.textContent = 'Sending...'; }
    });
  }

  // FAQ: only one open at a time on small screens (nice-to-have)
  var details = document.querySelectorAll('.faq details');
  details.forEach(function (d) {
    d.addEventListener('toggle', function () {
      if (d.open && window.innerWidth < 700) details.forEach(function (o) { if (o !== d) o.open = false; });
    });
  });
})();
