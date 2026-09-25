const site = require('./site');
const { esc } = require('./html');

const NAV = [
  ['/about', 'About'],
  ['/services', 'Services'],
  ['/membership', 'Membership'],
  ['/faq', 'FAQ'],
  ['/contact', 'Contact'],
];

const leaf = `<svg class="leaf" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 4c-8 0-14 4-15 12 3-6 8-8 12-9-4 3-7 6-9 12 8 0 12-6 12-15z" fill="currentColor"/></svg>`;

function layout({ title, description, body, path = '/', bodyClass = '' }) {
  const fullTitle = title ? `${title} | ${site.practice.name}` : `${site.practice.name} | ${site.practice.tagline}`;
  const desc = description || site.practice.descriptor;
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>${esc(fullTitle)}</title>
<meta name="description" content="${esc(desc)}">
<meta name="theme-color" content="#f7ebd1">
<meta property="og:title" content="${esc(fullTitle)}">
<meta property="og:description" content="${esc(desc)}">
<meta property="og:image" content="${site.practice.url}/img/hero.webp">
<meta property="og:type" content="website">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preload" href="/fonts/fraunces-normal-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/nunito-normal-400.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/css/fonts.css">
<link rel="stylesheet" href="/css/site.css">
<script type="application/ld+json">${JSON.stringify({
  '@context': 'https://schema.org', '@type': 'MedicalClinic',
  name: site.practice.name, url: site.practice.url, telephone: site.contact.phone,
  address: { '@type': 'PostalAddress', streetAddress: site.contact.address1, addressLocality: 'Ojai', addressRegion: 'CA', postalCode: '93023' },
  medicalSpecialty: 'Family medicine',
})}</script>
</head>
<body class="${esc(bodyClass)}">
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="/" aria-label="${esc(site.practice.name)} home">
      ${leaf}
      <span class="brand-name">${esc(site.practice.name)}</span>
    </a>
    <button class="nav-toggle" aria-expanded="false" aria-controls="site-nav" data-nav-toggle>
      <span class="nav-toggle-bar"></span><span class="nav-toggle-bar"></span><span class="nav-toggle-bar"></span>
      <span class="visually-hidden">Menu</span>
    </button>
    <nav id="site-nav" class="site-nav" aria-label="Primary">
      <ul>
        ${NAV.map(([href, label]) => `<li><a href="${href}"${path === href ? ' aria-current="page"' : ''}>${label}</a></li>`).join('')}
        <li class="nav-cta"><a class="btn btn-primary" href="/schedule">Schedule a visit</a></li>
        <li class="nav-phone"><a href="${site.contact.phoneHref}">${esc(site.contact.phone)}</a></li>
      </ul>
    </nav>
  </div>
</header>

<main id="main">
${body}
</main>

<footer class="site-footer">
  <div class="footer-art" aria-hidden="true">
    <img src="/img/ojai_banner.webp" srcset="/img/ojai_banner-sm.webp 800w, /img/ojai_banner.webp 1600w" sizes="100vw" alt="" loading="lazy" decoding="async">
  </div>
  <div class="wrap footer-grid">
    <div class="footer-col footer-brand">
      <p class="brand-name">${esc(site.practice.name)}</p>
      <p class="hand">${esc(site.practice.tagline)}</p>
      <p><a href="${site.contact.phoneHref}">${esc(site.contact.phone)}</a><br>
      <a href="mailto:${esc(site.contact.email)}">${esc(site.contact.email)}</a></p>
      <address>${esc(site.contact.address1)}<br>${esc(site.contact.address2)}</address>
    </div>
    <div class="footer-col">
      <p class="footer-head">Visit</p>
      <ul class="plain">
        ${NAV.map(([href, label]) => `<li><a href="${href}">${label}</a></li>`).join('')}
        <li><a href="/schedule">Schedule a visit</a></li>
      </ul>
    </div>
    <div class="footer-col">
      <p class="footer-head">Patients</p>
      <ul class="plain">
        <li><a href="${esc(site.contact.portalUrl)}">Patient portal</a></li>
        <li><a href="/membership">Join the practice</a></li>
        <li><a href="/faq">New patient questions</a></li>
        <li><a href="/schedule?type=sameday">Same-day visit</a></li>
      </ul>
      <p class="footer-head">Hours</p>
      <ul class="plain small">
        ${site.contact.hours.map(h => `<li><strong>${esc(h.day)}</strong><br>${esc(h.time)}</li>`).join('')}
      </ul>
    </div>
  </div>
  <div class="wrap footer-legal">
    <p>If you are experiencing a medical emergency, call 911. &copy; ${new Date().getFullYear()} ${esc(site.practice.name)}. <a href="/privacy">Privacy</a> &middot; <a href="/accessibility">Accessibility</a></p>
    <p class="proto-note">Prototype site. Names, prices, address and phone number are placeholders.</p>
  </div>
</footer>
<div class="sticky-cta" data-sticky-cta>
  <a class="btn btn-primary" href="/schedule">Schedule a visit</a>
  <a class="btn btn-ghost" href="${site.contact.phoneHref}">Call</a>
</div>
<script src="/js/site.js" defer></script>
</body>
</html>`;
}

module.exports = { layout };
