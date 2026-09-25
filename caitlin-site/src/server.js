const path = require('node:path');
const crypto = require('node:crypto');
const express = require('express');
const { layout } = require('./layout');
const pages = require('./pages');
const site = require('./site');

const app = express();
app.set('trust proxy', 1);
app.disable('x-powered-by');
app.use(express.urlencoded({ extended: false, limit: '20kb' }));
app.use(express.static(path.join(__dirname, '..', 'public'), {
  maxAge: process.env.NODE_ENV === 'production' ? '7d' : 0,
  extensions: false,
}));

const send = (res, page, status = 200) => res.status(status).type('html').send(layout(page));

app.get('/', (req, res) => send(res, pages.home()));
app.get('/about', (req, res) => send(res, pages.about()));
app.get('/services', (req, res) => send(res, pages.services()));
app.get('/membership', (req, res) => send(res, pages.membership()));
app.get('/faq', (req, res) => send(res, pages.faq()));
app.get('/contact', (req, res) => send(res, pages.contact()));
app.get('/privacy', (req, res) => send(res, pages.privacy()));
app.get('/accessibility', (req, res) => send(res, pages.accessibility()));

app.get('/schedule', (req, res) => {
  const type = site.visitTypes.some(t => t.value === req.query.type) ? req.query.type : undefined;
  send(res, pages.schedule({ values: type ? { visitType: type } : {} }));
});

// Prototype: submissions are validated, logged, and shown back on a confirmation page.
// In production this handler would email the office (e.g. via Resend/Postmark) and/or
// store the request. Confirmation state is kept briefly in memory so a refresh is safe.
const recent = new Map();
const TTL = 15 * 60 * 1000;

function validate(b) {
  const errors = {};
  const s = (k) => (typeof b[k] === 'string' ? b[k].trim() : '');
  const v = {
    name: s('name').slice(0, 120), email: s('email').slice(0, 200), phone: s('phone').slice(0, 40),
    status: s('status'), who: s('who'), visitType: s('visitType'), address: s('address').slice(0, 200),
    days: (Array.isArray(b.days) ? b.days : b.days ? [b.days] : []).filter(d => typeof d === 'string').slice(0, 5),
    time: s('time'), note: s('note').slice(0, 600), consent: s('consent'),
  };
  if (v.name.length < 2) errors.name = 'Please enter your name.';
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.email)) errors.email = 'Please enter a valid email address.';
  if (v.phone.replace(/\D/g, '').length < 10) errors.phone = 'Please enter a 10-digit phone number.';
  if (!site.visitTypes.some(t => t.value === v.visitType)) errors.visitType = 'Please choose a visit type.';
  if (v.visitType === 'home' && v.address.length < 5) errors.address = 'Please tell us where the home visit should be.';
  if (v.consent !== 'yes') errors.consent = 'Please confirm you understand this form is not for emergencies.';
  return { values: v, errors };
}

app.post('/schedule', (req, res) => {
  if (req.body.website) return res.redirect(303, '/schedule/thanks'); // honeypot: pretend success
  const { values, errors } = validate(req.body || {});
  if (Object.keys(errors).length) return send(res, pages.schedule({ values, errors }), 422);
  const id = crypto.randomBytes(8).toString('hex');
  recent.set(id, { ...values, at: Date.now() });
  setTimeout(() => recent.delete(id), TTL).unref();
  console.log(`[schedule] ${new Date().toISOString()} ${values.visitType} request from ${values.name} <${values.email}>`);
  res.redirect(303, `/schedule/thanks?r=${id}`);
});

app.get('/schedule/thanks', (req, res) => {
  const r = recent.get(String(req.query.r || ''));
  if (!r) return res.redirect(302, '/schedule');
  send(res, pages.scheduleThanks(r));
});

app.get('/healthz', (req, res) => res.json({ ok: true }));
app.use((req, res) => send(res, pages.notFound(), 404));

const port = Number(process.env.PORT) || 3000;
app.listen(port, '0.0.0.0', () => console.log(`${site.practice.name} prototype listening on http://localhost:${port}`));
