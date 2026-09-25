const site = require('./site');
const { esc, pic, spot } = require('./html');

const svc = (slug) => site.services.find(s => s.slug === slug);

function serviceCard(s, { compact = false } = {}) {
  return `<article class="card svc-card" id="${esc(s.slug)}">
    ${spot(s.icon)}
    <h3>${esc(s.name)}</h3>
    <p>${esc(s.blurb)}</p>
    ${compact ? `<a class="more" href="/services#${esc(s.slug)}">Learn more</a>` : `<p class="detail">${esc(s.detail)}</p>`}
  </article>`;
}

function ctaBand({ title, text, primary = ['/schedule', 'Schedule a visit'], secondary, image = 'garden' }) {
  return `<section class="section cta-band">
    <div class="wrap cta-band-inner">
      <div class="cta-band-art">${pic(image, { alt: '', sizes: '(min-width: 900px) 40vw, 90vw' })}</div>
      <div class="cta-band-text">
        <h2>${title}</h2>
        <p>${text}</p>
        <div class="btn-row">
          <a class="btn btn-primary" href="${primary[0]}">${primary[1]}</a>
          ${secondary ? `<a class="btn btn-ghost" href="${secondary[0]}">${secondary[1]}</a>` : ''}
        </div>
      </div>
    </div>
  </section>`;
}

/* ---------------- Home ---------------- */
function home() {
  const promises = [
    { icon: 'spot_clock', h: 'Seen today, not next month', p: 'Time is held open every weekday. Reach Dr. Caitlin directly and be seen the same day.' },
    { icon: 'spot_house', h: 'We come to you', p: 'Home visits across the Ojai Valley and an after-hours line for evenings and weekends.' },
    { icon: 'spot_family', h: 'One doctor for everyone', p: 'Newborns to grandparents, all cared for by a physician who knows the whole family.' },
  ];
  const steps = [
    { icon: 'spot_teapot', h: 'Come say hello', p: 'Start with a free 20-minute meet-and-greet, in the office or by video.' },
    { icon: 'spot_calendar', h: 'Join the practice', p: 'Choose an individual or family membership. Your insurance covers visits as usual.' },
    { icon: 'spot_phone', h: 'Call whenever you need us', p: 'Same-day visits, a direct line, home visits and a plan built around you.' },
  ];
  const body = `
<section class="hero">
  <div class="wrap hero-inner">
    <div class="hero-text">
      <p class="hand eyebrow">${esc(site.practice.opening)}</p>
      <h1>Family medicine the way it used to feel, with the medicine of today.</h1>
      <p class="lede">${esc(site.practice.descriptor)} Same-day visits, house calls, unhurried appointments, and a doctor who picks up the phone.</p>
      <div class="btn-row" data-cta-anchor>
        <a class="btn btn-primary btn-lg" href="/schedule">Schedule a visit</a>
        <a class="btn btn-ghost btn-lg" href="/membership">How membership works</a>
      </div>
      <ul class="trust-row" aria-label="At a glance">
        <li>Most insurance accepted</li><li>Same-day access</li><li>Home visits</li><li>All ages</li>
      </ul>
    </div>
    <div class="hero-art">
      ${pic('hero', { alt: 'Illustration of a small cottage clinic under an oak tree with the Ojai mountains behind', sizes: '(min-width: 900px) 55vw, 100vw', eager: true, width: 1600, height: 900 })}
    </div>
  </div>
</section>

<section class="section promises">
  <div class="wrap">
    <div class="grid-3">
      ${promises.map(p => `<div class="promise">${spot(p.icon)}<h2 class="h3">${esc(p.h)}</h2><p>${esc(p.p)}</p></div>`).join('')}
    </div>
  </div>
</section>

<section class="section about-teaser">
  <div class="wrap split">
    <div class="portrait-frame">
      <img src="${site.doctor.photo}" alt="Portrait of ${esc(site.doctor.display)}" width="460" height="460" loading="lazy">
    </div>
    <div>
      <p class="hand eyebrow">Meet your doctor</p>
      <h2>${esc(site.doctor.display)}</h2>
      <p>${esc(site.doctor.title)}, trained at Touro College of Osteopathic Medicine and the University of Wisconsin's Department of Family Medicine and Community Health. Dr. Caitlin opened ${esc(site.practice.name)} to practice medicine the way she was taught it should be: slowly, thoroughly, and close to home.</p>
      <blockquote class="pull">"The best medicine I know is time. Time to listen, time to explain, and time to follow up. That is what this practice is built around."</blockquote>
      <a class="btn btn-ghost" href="/about">More about Dr. Caitlin</a>
    </div>
  </div>
</section>

<section class="section services-teaser">
  <div class="wrap">
    <div class="section-head">
      <p class="hand eyebrow">What we do</p>
      <h2>Care for every age and every season</h2>
      <p>From well-child visits to menopause to blood pressure, all under one roof, with an integrative approach that treats the whole person.</p>
    </div>
    <div class="grid-3">
      ${['whole-family', 'same-day', 'home-visits', 'integrative', 'pediatrics', 'omt'].map(s => serviceCard(svc(s), { compact: true })).join('')}
    </div>
    <p class="center"><a class="btn btn-ghost" href="/services">See all services</a></p>
  </div>
</section>

<section class="band band-visit">
  <div class="wrap band-inner">
    <div class="band-art">${pic('visit', { alt: 'Illustration of the doctor talking with a parent and child at a table', sizes: '(min-width: 900px) 50vw, 100vw' })}</div>
    <div class="band-text">
      <p class="hand eyebrow">Integrative, not instead of</p>
      <h2>Modern medicine with an old-fashioned bedside manner</h2>
      <p>Integrative family medicine means using the full toolbox: evidence-based conventional care, plus honest attention to nutrition, sleep, movement, stress and, where it helps, botanicals and hands-on osteopathic treatment. Visits run 45 to 60 minutes so there is time to actually talk.</p>
      <a class="btn btn-ghost" href="/services#integrative">Our approach</a>
    </div>
  </div>
</section>

<section class="section how">
  <div class="wrap">
    <div class="section-head">
      <p class="hand eyebrow">How it works</p>
      <h2>Joining is simple</h2>
    </div>
    <ol class="steps">
      ${steps.map((s, i) => `<li class="step">${spot(s.icon)}<span class="step-num" aria-hidden="true">${i + 1}</span><h3>${esc(s.h)}</h3><p>${esc(s.p)}</p></li>`).join('')}
    </ol>
    <div class="member-summary">
      <div>
        <p class="hand eyebrow">Membership</p>
        <p class="price-line"><strong>From $55 a month</strong> for children, <strong>$160</strong> for adults, <strong>$320</strong> for the whole family.</p>
        <p>Your insurance still covers your visits. The membership covers the time, access and house calls that insurance never did.</p>
        <a class="btn btn-primary" href="/membership">See membership details</a>
      </div>
      <div class="insurance-chips">
        <p class="small"><strong>In network with</strong></p>
        <ul class="chips">${site.insurance.map(i => `<li>${esc(i)}</li>`).join('')}</ul>
      </div>
    </div>
  </div>
</section>

${ctaBand({
  title: 'Come meet Dr. Caitlin',
  text: 'A free 20-minute meet-and-greet is the easiest way to find out if the practice is a good fit for your family. No commitment, just a conversation.',
  primary: ['/schedule?type=meet', 'Book a free meet and greet'],
  secondary: [site.contact.phoneHref, `Call ${site.contact.phone}`],
})}`;
  return { title: '', description: site.practice.descriptor, body, path: '/', bodyClass: 'page-home' };
}

/* ---------------- About ---------------- */
function about() {
  const body = `
<section class="page-hero">
  <div class="wrap split split-tight">
    <div class="portrait-frame portrait-lg">
      <img src="${site.doctor.photo}" alt="Portrait of ${esc(site.doctor.display)}" width="460" height="460" fetchpriority="high">
    </div>
    <div>
      <p class="hand eyebrow">About</p>
      <h1>${esc(site.doctor.display)}</h1>
      <p class="lede">${esc(site.doctor.title)}, osteopathic physician, and your neighbor in the Ojai Valley.</p>
      <p>Dr. Caitlin trained in family medicine because she wanted to take care of whole families over whole lifetimes, not organ systems in fifteen-minute slots. After years in larger systems, she opened ${esc(site.practice.name)} to build the kind of practice she would want for her own family: small, personal, unhurried, and available when you actually need it.</p>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap prose">
    <h2>How she practices</h2>
    <p>Every patient gets real time. New patient visits run an hour, follow-ups forty-five minutes, and nobody is rushed out the door. Dr. Caitlin combines conventional, evidence-based medicine with the things that quietly do most of the work in health: sleep, food, movement, stress, and relationships. As a Doctor of Osteopathic Medicine, she also brings hands-on osteopathic manipulative treatment to the visit when it helps.</p>
    <p>She holds time open every weekday for same-day needs, carries the after-hours line herself, and makes house calls throughout the valley. It is an old model of medicine, deliberately chosen.</p>

    <h2>Training and education</h2>
    <dl class="edu">
      ${site.doctor.education.map(e => `<div><dt>${esc(e.label)}</dt><dd>${esc(e.value)}</dd></div>`).join('')}
    </dl>

    <h2>Why Ojai</h2>
    <p>Ojai is a small valley where people still know their neighbors, and it deserves a doctor who does too. Dr. Caitlin chose to open here so she could care for families across generations, follow patients through the years, and be part of the community she serves.</p>
  </div>
</section>

<section class="band band-room">
  <div class="wrap band-inner band-reverse">
    <div class="band-art">${pic('waiting_room', { alt: 'Illustration of a cozy waiting room with plants, books and a lemon tree', sizes: '(min-width: 900px) 50vw, 100vw' })}</div>
    <div class="band-text">
      <p class="hand eyebrow">The office</p>
      <h2>A place that feels more like a home than a clinic</h2>
      <p>Plants in the windows, a basket of picture books, a pot of tea on. The office is small on purpose. You will not sit in a waiting room for forty minutes, and you will always see the same doctor.</p>
      <a class="btn btn-ghost" href="/contact">Find the office</a>
    </div>
  </div>
</section>

${ctaBand({
  title: 'Come say hello',
  text: 'Book a free meet-and-greet and see whether the practice feels right for you and your family.',
  primary: ['/schedule?type=meet', 'Book a free meet and greet'],
  secondary: ['/membership', 'How membership works'],
})}`;
  return { title: `About ${site.doctor.short}`, description: `Meet ${site.doctor.display}, a board-certified family physician practicing integrative family medicine in Ojai.`, body, path: '/about' };
}

/* ---------------- Services ---------------- */
function services() {
  const body = `
<section class="page-hero">
  <div class="wrap section-head left">
    <p class="hand eyebrow">Services</p>
    <h1>Everything a family doctor should do, with the time to do it well</h1>
    <p class="lede">Primary care for all ages, same-day access, house calls, and an integrative approach that treats the whole person rather than just the symptom.</p>
  </div>
</section>
<section class="section pt-0">
  <div class="wrap">
    <div class="grid-3">
      ${site.services.map(s => serviceCard(s)).join('')}
    </div>
  </div>
</section>

<section class="band band-home">
  <div class="wrap band-inner">
    <div class="band-art">${pic('home_visit', { alt: 'Illustration of the doctor walking up a garden path to a cottage at dusk', sizes: '(min-width: 900px) 50vw, 100vw' })}</div>
    <div class="band-text">
      <p class="hand eyebrow">House calls</p>
      <h2>Sometimes the best exam room is your kitchen table</h2>
      <p>${esc(site.contact.serviceArea)} Two home visits a year are included in every membership. They are especially loved by new parents, elders, and anyone recovering from surgery.</p>
      <a class="btn btn-ghost" href="/schedule?type=home">Request a home visit</a>
    </div>
  </div>
</section>

${ctaBand({
  title: 'Not sure where to start?',
  text: 'Book a same-day visit if something is wrong today, or a free meet-and-greet if you are exploring the practice. Either way, you will talk to Dr. Caitlin herself.',
  primary: ['/schedule?type=sameday', 'Book a same-day visit'],
  secondary: ['/schedule?type=meet', 'Free meet and greet'],
})}`;
  return { title: 'Services', description: 'Primary care for all ages, same-day visits, home and after-hours visits, integrative and lifestyle medicine, pediatrics, women\'s health and osteopathic treatment in Ojai.', body, path: '/services' };
}

/* ---------------- Membership ---------------- */
function membership() {
  const m = site.membership;
  const body = `
<section class="page-hero">
  <div class="wrap section-head left">
    <p class="hand eyebrow">Membership</p>
    <h1>Insurance for the visits. A small annual fee for everything else.</h1>
    <p class="lede">${esc(m.intro)}</p>
  </div>
</section>

<section class="section pt-0">
  <div class="wrap">
    <div class="tiers">
      ${m.tiers.map(t => `<div class="tier${t.featured ? ' featured' : ''}">
        ${t.note ? `<p class="tier-note hand">${esc(t.note)}</p>` : ''}
        <h2 class="h3">${esc(t.name)}</h2>
        <p class="price"><span class="amt">${esc(t.price)}</span> <span class="per">${esc(t.per)}</span></p>
        <p class="alt">${esc(t.alt)}</p>
        <p class="who">${esc(t.who)}</p>
        <a class="btn ${t.featured ? 'btn-primary' : 'btn-ghost'}" href="/schedule?type=meet">Get started</a>
      </div>`).join('')}
    </div>
    <p class="center small seniors">${esc(m.seniors)}</p>
  </div>
</section>

<section class="section includes">
  <div class="wrap split">
    <div>
      <p class="hand eyebrow">Every membership includes</p>
      <h2>What the fee actually buys</h2>
      <ul class="checklist">${m.includes.map(i => `<li>${esc(i)}</li>`).join('')}</ul>
    </div>
    <div class="side-stack">
      <div class="card">
        ${spot('spot_heart')}
        <h3>Insurance we accept</h3>
        <ul class="chips">${site.insurance.map(i => `<li>${esc(i)}</li>`).join('')}</ul>
        <p class="small">Do not see your plan? Ask us. Out-of-network and self-pay options are available.</p>
      </div>
      <div class="card">
        ${spot('spot_book')}
        <h3>The fine print</h3>
        <ul class="plain small fine">${m.fine.map(f => `<li>${esc(f)}</li>`).join('')}</ul>
      </div>
    </div>
  </div>
</section>

${ctaBand({
  title: 'Questions about membership?',
  text: 'The FAQ covers HSA and FSA payment, what counts as same-day, and how home visits work. Or just call and ask.',
  primary: ['/faq', 'Read the FAQ'],
  secondary: [site.contact.phoneHref, `Call ${site.contact.phone}`],
  image: 'waiting_room',
})}`;
  return { title: 'Membership and pricing', description: 'Simple annual membership pricing for individuals, children and families, alongside the insurance you already have.', body, path: '/membership' };
}

/* ---------------- FAQ ---------------- */
function faq() {
  const body = `
<section class="page-hero">
  <div class="wrap section-head left">
    <p class="hand eyebrow">FAQ</p>
    <h1>Questions families ask</h1>
    <p class="lede">If yours is not here, call or send a note. A real person answers.</p>
  </div>
</section>
<section class="section pt-0">
  <div class="wrap faq">
    ${site.faq.map((f, i) => `<details${i === 0 ? ' open' : ''}><summary>${esc(f.q)}</summary><div class="faq-a"><p>${esc(f.a)}</p></div></details>`).join('')}
  </div>
</section>
${ctaBand({
  title: 'Still wondering?',
  text: 'A free meet-and-greet is the best way to get your questions answered in person.',
  primary: ['/schedule?type=meet', 'Book a free meet and greet'],
  secondary: ['/contact', 'Contact us'],
})}`;
  return { title: 'FAQ', description: 'Answers about integrative family medicine, insurance, membership fees, same-day visits and home visits in Ojai.', body, path: '/faq' };
}

/* ---------------- Schedule ---------------- */
const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
const TIMES = [['morning', 'Morning'], ['midday', 'Midday'], ['afternoon', 'Afternoon'], ['after', 'After 5 pm']];

function field(label, name, input, { hint, error } = {}) {
  return `<div class="field${error ? ' has-error' : ''}">
    <label for="${name}">${label}</label>
    ${hint ? `<p class="hint" id="${name}-hint">${hint}</p>` : ''}
    ${input}
    ${error ? `<p class="error" id="${name}-error">${esc(error)}</p>` : ''}
  </div>`;
}

function schedule({ values = {}, errors = {} } = {}) {
  const v = (k) => esc(values[k] || '');
  const chk = (k, val) => (Array.isArray(values[k]) ? values[k] : [values[k]]).includes(val) ? ' checked' : '';
  const sel = (k, val) => values[k] === val ? ' selected' : '';
  const errKeys = Object.keys(errors);
  const body = `
<section class="page-hero">
  <div class="wrap section-head left">
    <p class="hand eyebrow">Schedule</p>
    <h1>Request a visit</h1>
    <p class="lede">Tell us a little about what you need and Dr. Caitlin's office will confirm a time, usually within the hour on weekdays. For same-day needs you can also just call <a href="${site.contact.phoneHref}">${esc(site.contact.phone)}</a>.</p>
  </div>
</section>
<section class="section pt-0">
  <div class="wrap schedule-grid">
    <form class="form card" method="post" action="/schedule" data-schedule-form data-cta-anchor novalidate>
      ${errKeys.length ? `<div class="form-alert" role="alert"><strong>Please check the highlighted fields.</strong></div>` : ''}
      <div class="hp"><label>Leave this field empty<input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>

      <fieldset>
        <legend>About you</legend>
        ${field('Your name', 'name', `<input id="name" name="name" type="text" autocomplete="name" required value="${v('name')}" ${errors.name ? 'aria-invalid="true" aria-describedby="name-error"' : ''}>`, { error: errors.name })}
        <div class="two">
          ${field('Email', 'email', `<input id="email" name="email" type="email" autocomplete="email" inputmode="email" required value="${v('email')}" ${errors.email ? 'aria-invalid="true" aria-describedby="email-error"' : ''}>`, { error: errors.email })}
          ${field('Phone', 'phone', `<input id="phone" name="phone" type="tel" autocomplete="tel" inputmode="tel" required value="${v('phone')}" ${errors.phone ? 'aria-invalid="true" aria-describedby="phone-error"' : ''}>`, { error: errors.phone })}
        </div>
        <div class="field">
          <span class="label">Are you a current patient?</span>
          <div class="radio-row">
            <label class="radio"><input type="radio" name="status" value="new"${chk('status', 'new') || (!values.status ? ' checked' : '')}> New to the practice</label>
            <label class="radio"><input type="radio" name="status" value="existing"${chk('status', 'existing')}> Current patient</label>
          </div>
        </div>
        <div class="field">
          <span class="label">Who is the visit for?</span>
          <div class="radio-row">
            <label class="radio"><input type="radio" name="who" value="me"${chk('who', 'me') || (!values.who ? ' checked' : '')}> Me</label>
            <label class="radio"><input type="radio" name="who" value="child"${chk('who', 'child')}> My child</label>
            <label class="radio"><input type="radio" name="who" value="family"${chk('who', 'family')}> Another family member</label>
          </div>
        </div>
      </fieldset>

      <fieldset>
        <legend>The visit</legend>
        ${field('Type of visit', 'visitType', `<select id="visitType" name="visitType" required ${errors.visitType ? 'aria-invalid="true"' : ''}>
          ${site.visitTypes.map(t => `<option value="${t.value}"${sel('visitType', t.value)}>${esc(t.label)}</option>`).join('')}
        </select>`, { error: errors.visitType })}
        <div data-home-only hidden>
          ${field('Home visit address', 'address', `<input id="address" name="address" type="text" autocomplete="street-address" value="${v('address')}" placeholder="Street address, Ojai">`, { hint: 'Home visits are available throughout the Ojai Valley.' })}
        </div>
        <div class="field">
          <span class="label">Preferred days <span class="opt">(pick any)</span></span>
          <div class="check-row">
            ${DAYS.map(d => `<label class="check"><input type="checkbox" name="days" value="${d}"${chk('days', d)}> ${d.slice(0, 3)}</label>`).join('')}
          </div>
        </div>
        <div class="field">
          <span class="label">Preferred time</span>
          <div class="radio-row">
            ${TIMES.map(([val, l]) => `<label class="radio"><input type="radio" name="time" value="${val}"${chk('time', val)}> ${l}</label>`).join('')}
          </div>
        </div>
        ${field('Anything we should know? <span class="opt">(optional)</span>', 'note', `<textarea id="note" name="note" rows="4" maxlength="600">${v('note')}</textarea>`, { hint: 'A sentence or two is plenty. Please do not include detailed medical information here; we will talk in person.' })}
      </fieldset>

      <div class="field consent${errors.consent ? ' has-error' : ''}">
        <label class="check"><input type="checkbox" name="consent" value="yes"${chk('consent', 'yes')} required> I understand this form is for scheduling only and is not for emergencies. In an emergency, call 911.</label>
        ${errors.consent ? `<p class="error">${esc(errors.consent)}</p>` : ''}
      </div>

      <button class="btn btn-primary btn-lg" type="submit">Send request</button>
      <p class="small muted">We reply by phone or email, usually within the hour on weekdays.</p>
    </form>

    <aside class="schedule-aside">
      <div class="card">
        ${spot('spot_phone')}
        <h3>Prefer to call?</h3>
        <p><a class="big-link" href="${site.contact.phoneHref}">${esc(site.contact.phone)}</a></p>
        <p class="small">${site.contact.hours.map(h => `<strong>${esc(h.day)}</strong>: ${esc(h.time)}`).join('<br>')}</p>
      </div>
      <div class="card">
        ${spot('spot_clock')}
        <h3>Need to be seen today?</h3>
        <p class="small">Choose "Same-day sick visit" and reach out before mid-afternoon. Members can also text Dr. Caitlin directly.</p>
      </div>
      <div class="card">
        ${spot('spot_teapot')}
        <h3>New here?</h3>
        <p class="small">Start with a free 20-minute meet-and-greet. No paperwork, no commitment.</p>
      </div>
    </aside>
  </div>
</section>`;
  return { title: 'Schedule a visit', description: `Request a same-day visit, home visit, or free meet-and-greet with ${site.doctor.display} in Ojai.`, body, path: '/schedule', bodyClass: 'page-schedule' };
}

function scheduleThanks(req) {
  const t = site.visitTypes.find(x => x.value === req.visitType);
  const rows = [
    ['Name', req.name], ['Email', req.email], ['Phone', req.phone],
    ['Patient', req.status === 'existing' ? 'Current patient' : 'New to the practice'],
    ['Visit for', { me: 'You', child: 'Your child', family: 'A family member' }[req.who] || 'You'],
    ['Visit type', t ? t.label : req.visitType],
    req.address ? ['Home visit address', req.address] : null,
    ['Preferred days', (req.days || []).join(', ') || 'Any'],
    ['Preferred time', (TIMES.find(x => x[0] === req.time) || [null, 'Any'])[1]],
    req.note ? ['Note', req.note] : null,
  ].filter(Boolean);
  const body = `
<section class="page-hero">
  <div class="wrap section-head left">
    <p class="hand eyebrow">Thank you</p>
    <h1>Your request is in, ${esc(req.name.split(' ')[0])}.</h1>
    <p class="lede">Dr. Caitlin's office will confirm a time by phone or email, usually within the hour on weekdays.</p>
  </div>
</section>
<section class="section pt-0">
  <div class="wrap split">
    <div class="card summary">
      <h2 class="h3">What you sent</h2>
      <dl class="summary-list">${rows.map(([k, val]) => `<div><dt>${esc(k)}</dt><dd>${esc(val)}</dd></div>`).join('')}</dl>
    </div>
    <div>
      <div class="proto-callout">
        <p class="hand">Prototype note</p>
        <p>On the live site, this request would be emailed to Dr. Caitlin's office and a confirmation sent to you at <strong>${esc(req.email)}</strong>. Requests can also be stored in a private dashboard or pushed straight into a scheduling system.</p>
      </div>
      <p class="small">Something wrong? <a href="/schedule">Send another request</a> or call <a href="${site.contact.phoneHref}">${esc(site.contact.phone)}</a>.</p>
      <div class="thanks-art">${pic('garden', { alt: '', sizes: '(min-width: 900px) 45vw, 90vw' })}</div>
    </div>
  </div>
</section>`;
  return { title: 'Request received', body, path: '/schedule' };
}

/* ---------------- Contact ---------------- */
function contact() {
  const c = site.contact;
  const body = `
<section class="page-hero">
  <div class="wrap section-head left">
    <p class="hand eyebrow">Contact</p>
    <h1>Come find us in the valley</h1>
    <p class="lede">A small office on Matilija Street, a phone that gets answered, and house calls when you cannot come to us.</p>
  </div>
</section>
<section class="section pt-0">
  <div class="wrap contact-grid">
    <div class="card contact-card">
      ${spot('spot_phone')}
      <h2 class="h3">Call or write</h2>
      <p><a class="big-link" href="${c.phoneHref}">${esc(c.phone)}</a></p>
      <p><a href="mailto:${esc(c.email)}">${esc(c.email)}</a></p>
      <p class="small muted">For non-urgent questions, current patients can also message through the <a href="${esc(c.portalUrl)}">patient portal</a>.</p>
    </div>
    <div class="card contact-card">
      ${spot('spot_house')}
      <h2 class="h3">Visit the office</h2>
      <address>${esc(c.address1)}<br>${esc(c.address2)}</address>
      <p class="small">Free parking behind the building. The office is on the ground floor and wheelchair accessible.</p>
      <p><a href="https://maps.google.com/?q=${encodeURIComponent(c.mapQuery)}" target="_blank" rel="noopener">Directions</a></p>
    </div>
    <div class="card contact-card">
      ${spot('spot_clock')}
      <h2 class="h3">Hours</h2>
      <ul class="plain hours">${c.hours.map(h => `<li><strong>${esc(h.day)}</strong><span>${esc(h.time)}</span></li>`).join('')}</ul>
    </div>
    <div class="card contact-card">
      ${spot('spot_moon')}
      <h2 class="h3">After hours</h2>
      <p class="small">Members have an after-hours line for urgent concerns on evenings and weekends. For emergencies, always call 911 or go to the nearest emergency room.</p>
    </div>
  </div>
</section>
<section class="section pt-0">
  <div class="wrap">
    <div class="map-frame">
      <iframe title="Map of the office location in Ojai" src="https://maps.google.com/maps?q=${encodeURIComponent(c.mapQuery)}&z=14&output=embed" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>
    </div>
    <p class="small center muted">${esc(c.serviceArea)}</p>
  </div>
</section>
${ctaBand({
  title: 'Ready to schedule?',
  text: 'Request a visit online and we will confirm a time, usually within the hour on weekdays.',
  primary: ['/schedule', 'Schedule a visit'],
  image: 'home_visit',
})}`;
  return { title: 'Contact', description: `Phone, address, hours and directions for ${site.practice.name} in Ojai, California.`, body, path: '/contact' };
}

/* ---------------- Small pages ---------------- */
function simple(title, paras, path) {
  return {
    title, path,
    body: `<section class="page-hero"><div class="wrap section-head left"><h1>${esc(title)}</h1></div></section>
<section class="section pt-0"><div class="wrap prose">${paras.map(p => `<p>${p}</p>`).join('')}</div></section>`,
  };
}
const privacy = () => simple('Privacy', [
  `${esc(site.practice.name)} takes your privacy seriously. Information submitted through this website is used only to schedule and coordinate your care and is never sold or shared for marketing.`,
  'Please do not send detailed medical information through the website. Once you are a patient, secure messaging is available through the patient portal.',
  'This is a prototype page. The final site will include the practice\'s full HIPAA Notice of Privacy Practices.',
], '/privacy');
const accessibility = () => simple('Accessibility', [
  `${esc(site.practice.name)} wants every patient to be able to use this website. It is built to work with screen readers, keyboard navigation and text zoom, and to meet WCAG 2.1 AA guidelines.`,
  `If anything on the site is hard to use, please call ${esc(site.contact.phone)} or email ${esc(site.contact.email)} and we will help right away.`,
], '/accessibility');
const notFound = () => ({
  title: 'Page not found', path: '',
  body: `<section class="page-hero"><div class="wrap section-head">
  ${spot('spot_moon', 'spot-lg')}
  <h1>We could not find that page</h1>
  <p class="lede">It may have moved. Try the <a href="/">home page</a> or <a href="/schedule">schedule a visit</a>.</p></div></section>`,
});

module.exports = { home, about, services, membership, faq, schedule, scheduleThanks, contact, privacy, accessibility, notFound };
