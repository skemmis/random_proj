# Portfolio inspiration — what great many-small-projects sites do

Research pass, 2026-09-25. Every URL was fetched and loads today.
Companion to `inventory.md`. Pick a direction (or mix) and we iterate.

## Sites worth stealing from

| Site | Who | The trick | Format | How each project appears |
|------|-----|-----------|--------|--------------------------|
| [neal.fun](https://neal.fun/) | Neal Agarwal | ~40 web toys, zero pretension; the name is the pitch | Uniform grid of hand-drawn icon tiles | Icon + title → full-page live project |
| [lynnandtonic.com/work](https://lynnandtonic.com/work/) | Lynn Fisher | Side projects are first-class "Work"; the archive of old site versions is itself a project | Vertical list, illustrated thumbnails | Illustration + title + domain |
| [levels.io/projects](https://levels.io/projects/) | Pieter Levels | Every project since 1991 tagged Success / Okay / Failed, with a pie chart. "Most things I made never succeeded." | Chronological table, status filters | Row: year, name, status pill, one line |
| [thesephist.com/projects](https://thesephist.com/projects/) | Linus Lee | ~200 projects under Highlights / Released / Retired / Experiments / Unfinished | Dense categorized text list | Title + 1–2 sentences + stat |
| [rauno.me](https://rauno.me/) | Rauno Freiberg | Splits `/craft` (dozens of looping interaction studies) from `/projects` (9 shipped things) | Dark grid of dated video loops | Loop thumbnail + title + month |
| [henryheffernan.com](https://henryheffernan.com/) | Henry Heffernan | Zoom into a CRT on a desk; the portfolio is a working Win95 OS with Doom | Desktop metaphor, draggable windows | A window per project; games run in-window |
| [martingauer.com](https://martingauer.com/) | Martin Gauer | Whole site is a Game Boy in HTML/CSS; each section is a cartridge with its own DMG code | Cartridge shelf + keyboard controls | Cartridge label → in-screen page |
| [terminal.satnaing.dev](https://terminal.satnaing.dev/) | Sat Naing | The site is a shell: `help`, `projects`, `themes` | Full-screen terminal | Numbered text list |
| [tholman.com](https://tholman.com/) | Tim Holman | 100+ toys carried by pure text because the grouping ("Optical Toys", "Ant Toys") is good | Text-only index | Link only |
| [hakim.se](https://hakim.se/) | Hakim El Hattab | Grouped by type: Apps / Experiments & Games / UI concepts / Physics sims; ends with a Q&A | Single column, grouped | Title + 2 sentences → live demo |
| [ncase.me](https://ncase.me/) | Nicky Case | Sorted by what the visitor does: PLAY / READ / WATCH | Horizontal card rows | Illustrated thumb + blurb |
| [100r.co](https://100r.co/site/home.html) | Hundred Rabbits | Wiki-style monthly log; projects, travel, and reading interleaved; hand-drawn nav | Text wiki, ASCII dividers | Own page with drawing + links |
| [everest-pipkin.com](https://everest-pipkin.com/) | Everest Pipkin | Deliberate HTML frameset in Inconsolata; museum-archive feel | Three-column frames | Image + text page |
| [xem.github.io](https://xem.github.io/) | Maxime Euzière | Plain thumbnail gallery that feels like a homepage, not a brand | Grid of screenshots | Screenshot → project page |
| [sairakhan.design](https://sairakhan.design/) | Saira Khan | Built with Claude Code; restrained macOS-desktop aesthetic that still reads as a portfolio | Hero + cards + dock | Card with thumb, tags, outcome line |
| [vibefolio.link](https://vibefolio.link/) | (platform) | Built in a weekend with Claude for vibe-coded projects; defines a minimal card schema | Cards grouped by category | emoji · name · url · blurb · tags · date |
| [bruno-simon.com](https://bruno-simon.com/) | Bruno Simon | Drive a car through a 3D world to reach projects; achievements | Game world + HUD | 3D billboards |
| [jesse-zhou.com](https://jesse-zhou.com/) | Jesse Zhou | 3D ramen shop; projects in a vending machine, videos on the TV | Diorama with hotspots | Vending item → modal |

Simpler honorable mentions: [paco.me](https://paco.me), [emilkowal.ski](https://emilkowal.ski),
[brittanychiang.com](https://brittanychiang.com) (tech tags + "100k installs" stats),
[samuelkraft.com](https://samuelkraft.com), [tyler.cafe](https://tyler.cafe),
[spencer.place](https://spencer.place), [nan.fyi](https://nan.fyi),
[wattenberger.com](https://wattenberger.com) (inline category tags), [ciechanow.ski](https://ciechanow.ski)
(long-form with embedded sims, a model for the Gizzard Hours writeup).

## Six patterns to steal

1. **Group by what the visitor does, not by tech.** ncase, hakim, tholman. For your set: **Play** (Fellowship, La Brea Madre, Sex House Island, Crucible), **Bet** (Fantasy Reality, Mention Tracker, DegenBench), **Read** (newsletter, Gizzard Hours, Trump data stories), **Use/Build** (Feed Unfucker, pulse map).
2. **Metadata as design.** levels.io status pills, vibefolio's tags + launch date, thesephist's Retired/Unfinished. A consistent row of `year · type · status · stack · model` makes 12 items feel like a system and lets you be honest about Crucible (dead) and Feed Unfucker (v0).
3. **Icon tile, not screenshot, for the index.** neal.fun, lynnandtonic. Screenshots of small web apps all look alike; one 1:1 icon per project does the work. Fantasy Reality already generates pixel art per market; that style could be the icon language for the whole site.
4. **Separate experiments from projects.** rauno's `/craft` vs `/projects`. Keeps a one-session concept from sitting next to a multiplayer game as equals.
5. **One looping preview per item; the index stays static.** rauno, nan.fyi. Don't iframe 12 live apps into the index.
6. **Playful frame, plain fallback.** heffernan, gauer, satnaing wrap a simple content model in a metaphor, and the ones that age well keep a boring HTML list underneath. Build the list first, the metaphor second.

## Three directions

### 1. The Shelf (cartridge / toy box)
- **Vibe:** neal.fun meets Martin Gauer. A shelf of small playable things, each with its own box art. Fits you unusually well: Sex House Island is literally a LucasArts homage, Fellowship is a board game, Fantasy Reality has pixel art, and Crucible is a creature sim.
- **Layout:** Single page, uniform grid of 1:1 tiles (4-up desktop, 2-up phone) under short group headers (Play / Bet / Read / Build). Hover flips a tile to a 3-second muted loop. One filter row by tag.
- **Type/color:** Bricolage Grotesque or Space Grotesk titles, warm off-white page, one saturated accent per group, chunky rounded tiles with a hard 2px shadow (cartridge-label feel). Pixel font on labels only.
- **Each project:** custom icon tile + title + year → full-screen live project, or a short page with photos/embed for newsletter and hardware.
- **References:** neal.fun, martingauer.com, lynnandtonic.com/work.

### 2. The Ledger (index card / table)
- **Vibe:** levels.io crossed with thesephist. Quiet, dense, honest, fast to scan. Reads as "someone who ships a lot," and "vibe coded" is part of the story rather than hidden.
- **Layout:** Header paragraph ("I built 14 things this year with Claude Code. Here are all of them, including the ones that didn't work."), then a table: `# · icon · name · one line · type · model/tool · status · year · ↗`. Click a row to expand an inline card with a screenshot/loop and 3–4 sentences (what, why, what the AI did well and badly). Optional levels-style status pie in the header.
- **Type/color:** JetBrains Mono or Berkeley Mono for the table, a humanist serif for prose, near-white/near-black with status colors only. Light and dark.
- **Each project:** a row; expanded card with one 16:9 capture and a live link. Newsletter row pulls the last 3 Substack issues from RSS; hardware row expands to photo + short video.
- **References:** levels.io/projects, thesephist.com/projects, vibefolio.link for the field schema.

### 3. The Workshop (desktop OS / diorama with a real fallback)
- **Vibe:** Heffernan's OS or Jesse Zhou's ramen shop, scaled down. A single desk scene with your real stuff: a monitor (the apps), the LA pulse map on the wall, a newsletter on the notepad, a Fellowship board on the table.
- **Layout:** Landing is an illustrated 2D desk (SVG; Three.js optional). Objects are hotspots that open draggable windows. A dock or start menu lists every project plainly; a terminal window accepts `ls projects` and `open fellowship`. A `/list` route renders the same data as plain HTML for mobile and SEO.
- **Type/color:** Win95 or Mac-classic chrome, IBM Plex Mono for UI, one accent pulled from the pulse map, CRT grain on the scene only.
- **Each project:** opens in a window with capture + description + Launch button. Games can run inside the window via iframe because everything is on Railway under your control.
- **References:** henryheffernan.com, jesse-zhou.com, sairakhan.design, terminal.satnaing.dev.

**My recommendation:** build Direction 2's data model and plain list first (a single `projects.json` is the source of truth for every site above), then skin it as Direction 1. The Shelf is the one that turns your specific mix (games, pixel art, a board game, a hardware map) into a coherent identity, and it stays cheap to extend every time you ship something new. Direction 3 is the most fun but the most work per project added.

## Capturing assets

- **Screenshots:** Playwright at 1440×900, device scale 2, same framing for every app. Full-page only for tools, never games. Add padding in the site's CSS rather than baking chrome into images.
- **Loops over GIFs:** record 3–6 s, then `ffmpeg -vf "scale=800:-2,fps=24" -an -c:v libvpx-vp9 -crf 33` plus an H.264 fallback; `<video autoplay muted loop playsinline>`. If a GIF is really needed, `gifski --fps 15 --width 640`.
- **Icon tiles:** one 512×512 per project. Cheap version is a monogram on a flat category color; better is a consistent AI-illustrated single object per project. Or lean on Fantasy Reality's existing pixel-art pipeline.
- **Live embeds:** iframe only your own apps, lazy-mount on click, give each app an `?embed=1` mode that hides nav. One iframe per viewport max.
- **Newsletter:** three or four issue cards from the Substack RSS at build time, one issue screenshot, link to archive.
- **Hardware:** a 6–10 s stabilized landscape phone video, one hero photo, the wiring SVG already in the repo, and a museum-style caption (materials, dimensions, year).
- **Data tools:** one "money chart" per tool as static SVG/PNG; the live tool sits behind the link.
- **Fantasy Reality:** screenshot the leaderboard with real or anonymized data; an empty state kills it.
- **OG images:** generate one per project page with satori or a Playwright render of an HTML template.
- **Railway:** static site or tiny Node server, media in the repo with long cache headers, each project on its own service and subdomain so the portfolio can link or iframe them uniformly.
