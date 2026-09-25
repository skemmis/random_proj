# Matilija Family Medicine (prototype)

A prototype website for a small integrative family medicine practice in Ojai, CA:
insurance-based care plus an annual membership for same-day access, unhurried
visits, and home and after-hours visits.

Warm picture-book look (gouache illustrations generated once with Gemini and
committed as static files), mobile-first, no build step, no database.

> Everything practice-specific (name, surname, address, phone, prices, insurance
> list, services, FAQ copy) is placeholder content and lives in **one file**:
> `src/site.js`. Edit that and the whole site updates.

## Run it

```bash
cd caitlin-site
npm install
npm start          # http://localhost:3000
npm run dev        # same, restarts on file changes
```

Node 20 or newer. The only runtime dependency is Express. You can also run
`npm install && npm start` from the repository root.

## What's here

| Route | What it does |
|---|---|
| `/` | Home: hero, three promises, meet the doctor, services, how it works, membership summary |
| `/about` | Bio, training and education, the office |
| `/services` | Nine service cards with detail, house-call section |
| `/membership` | Three pricing tiers, what's included, insurance accepted, fine print |
| `/faq` | Accordion FAQ |
| `/schedule` | Appointment request form (server-validated, honeypot, confirmation page) |
| `/contact` | Phone, address, hours, after-hours note, embedded map |
| `/privacy`, `/accessibility` | Short placeholder pages |
| `/healthz` | JSON health check for Railway |

The schedule form currently validates the request, logs it to the server console,
and shows a confirmation page that says what *would* happen on the live site
(email to the office and a confirmation to the patient). Wiring it to a real
mail provider such as Resend or Postmark is a ~20-line change in `src/server.js`.

Deep links preselect the visit type: `/schedule?type=sameday`, `?type=home`, `?type=meet`.

## Layout

```
src/site.js        all practice content and settings (edit this)
src/pages.js       page templates (plain template literals)
src/layout.js      shared <head>, header/nav, footer, sticky mobile CTA
src/server.js      Express app, routes, form validation
public/css/        site.css (design system) and fonts.css (self-hosted fonts)
public/img/        illustrations (webp) and the doctor's photo
public/js/site.js  mobile nav, sticky CTA, small form niceties
tools/             one-off scripts: image generation, optimisation, screenshots
```

## Deploy to Railway

The repo is set up so the site deploys whether or not you point Railway at the
subfolder:

1. New project → Deploy from GitHub repo → pick this repo and the branch.
2. Leave **Root Directory** blank (the root `package.json` declares `caitlin-site`
   as an npm workspace and starts the server), or set it to `caitlin-site`.
   Both work.
3. Nothing else is required. Railpack detects Node, runs `npm ci`, injects `PORT`,
   starts the server, and uses `/healthz` from `railway.json` as the health check.
4. Optional: set `NODE_ENV=production` to enable long cache headers on static files.

No environment variables or secrets are needed at runtime.

## Regenerating illustrations

The images were generated once with Gemini using the picture-book spreads as
style references, then converted to webp. The API key is only needed for that
step and is never used by the running site.

The scripts' dependencies (sharp, Playwright) live in `tools/package.json` so the
production install stays tiny. Install them once with `npm run tools:install`.

```bash
export GEMINI_API_KEY=...            # never commit this
export REF_DIR=/path/to/style/refs   # folder with 1.webp, 2.webp, 3.webp
node tools/gen-images.mjs            # or: node tools/gen-images.mjs hero spot_clock
node tools/optimize-images.mjs       # scenes -> name.webp + name-sm.webp
node tools/key-spots.mjs             # spot icons -> transparent background
```

Prompts and the style block live at the top of `tools/gen-images.mjs`.

## Fonts

Fraunces (headings), Nunito (body) and Delius (hand-lettered accents), all under
the SIL Open Font License, self-hosted from `public/fonts/` so the site makes no
third-party requests.
