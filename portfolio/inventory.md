# Portfolio inventory — everything vibe-coded, Sep 2025 → Sep 2026

Source of truth for what exists, where it lives, what assets we can pull, and a
first-pass recommendation on what goes in the portfolio. Edit the "Include?"
column and we'll build from this.

## The roundup

| # | Project | What it is | Repo | Stack | Live? | Assets on hand | Include? |
|---|---------|-----------|------|-------|-------|----------------|----------|
| 1 | **Fantasy Reality** | Prediction-market fantasy league: seasons, leagues, parlays, wallets, achievements, AI players, Discord nags, weekly digest, per-market pixel art, a mention scanner. Began life as "VibeBet" on Replit (Dec 2025). The flagship. | `Fantasy-Reality` (private) | React + Vite, Express, Drizzle/Neon Postgres, Auth0, Anthropic + Gemini SDKs, Docker | **Yes** — fantasy-reality.com | logo, wordmark, OG image, PWA icons, backdrop art, achievement art, character art, ~25 dev screenshots | ★ headliner |
| 2 | **Kalshi Mention Tracker** | Tracks "will X say Y" phrase markets on Kalshi; phrase search, timeline, event log. Started in Lovable, reworked into FR house style, embedded at `/tracker`. | `mention_tracker` (public) + `Fantasy-Reality/server/tracker*` | Vite + React + shadcn, Supabase (orig) | **Yes** — fantasy-reality.com/tracker | 1 image; will need screenshots | ★ yes |
| 3 | **DegenBench** | AI models paper-bet on real Kalshi markets daily in two rounds (independent → discussion); scored on Brier + PnL. Embedded at `/degenbench`. | `degen_bench` (private) + FR embed | Express, Drizzle, Anthropic/OpenAI/Google/xAI adapters, node-cron | **Yes** — fantasy-reality.com/degenbench | founding brief + tech spec docs; no images | ★ yes |
| 4 | **Fantasy Reality newsletter toolkit** | Chart-maker for the Substack: paste a Kalshi event URL → editorial or "meme" preset PNG with annotations + Nano Banana sprites. Web wizard on Railway + GitHub Action. Also a `video/` branch: Remotion-style Kalshi market video series (episode 1 pipeline built). | `fantasy-reality-newsletter` (public) | Python, matplotlib-style renderer, Railway | Substack yes (fantasyreality.substack.com); Railway URL unknown | 4 rendered charts (Balogun red card, editorial + meme), sprite art | yes |
| 5 | **Fate of the Fellowship (online)** | Real-time 2–5 player web implementation of the Leacock co-op board game; room codes, legal-move engine, hover-documented rules, dice resolution panel. 8.5K actions verified. Client title is **Emberfall** (renamed for IP distance). | `fakefellowship` (public) | TS monorepo: engine / server / client, Railway | Deployed on Railway, URL unknown | board.jpg, ~30 icon PNGs, rulebook page scans (`icontool/`) | ★ yes |
| 6 | **La Brea Madre** | Territory war game on a real hex map of LA, driven by real open data (oil wells → crude, parking citations → events). Occult-LA lore bible (Bell, Manly P. Hall, Hubbard, Didion…). Plus a **physical pulse-map installation** branch: LED neighborhood map, laser-engrave SVGs, wiring diagram, BOM. | `la-brea-madre` (public) | React 19, deck.gl H3 hexes over Mapbox, Express, Neon, Auth0, Docker | Railway URL unknown | design docs (design-doc, GAMEPLAY, COMBAT_DESIGN), engrave/wiring SVGs on `claude/zen-thompson-9w5f2m` | ★ yes (2 entries: game + installation) |
| 7 | **Sex House Island** | SCUMM-style point-and-click vertical slice: 9-verb bar, hotspots, inventory, dialogue tree, 3-step puzzle, procedural walk cycle drawn in code. ~600 lines. Also a promo site + sprite lab + level editor. | `sexhouseisland` (public) | TypeScript + Canvas, no framework; Express server, Railway | Railway URL unknown | none in repo (art is procedural) — need gif capture | yes |
| 8 | **Crucible** | Agent-governed 3D evolution sim: soft-body creatures with evolved neural nets; changes proposed/debated by a panel of AI agents (Naturalist, Chaos Agent, SFI Fellow…) under a Constitution, humans merge. | `crucible` (public) | Three.js, Vite, orchestrator | **Dead** — Vercel + GH Pages both 404 | Constitution, roadmap, agent roster; no images | yes, needs redeploy or a recorded clip |
| 9 | **Feed Unfucker** | Chrome extension + agent instructions: reads your own FB/IG feeds, drops ads/reshares/outrage, emails a calm digest of what actual friends are doing. v0, first digest already sent. | `feed-unfucker` (public) | Python, Chrome ext, Claude Code routine, Gmail/Drive connectors | n/a (local tool) | fake-feed fixture images; "Social Feedia v0 design" artifact | yes |
| 10 | **Gizzard Hours** | King Gizzard listening analysis from a 67 MB YouTube Takeout: streaming chunk parser, MusicBrainz discography matcher, album-share-over-time charts, heavy-vs-light scoring, Disney catalogue comparison. Fed a Substack essay. | `random_proj/kglw` (public) | stdlib Python, PNG export | Artifact: claude.ai/artifact/AhDcwmZPukvkLC24iZsAyk | charts renderable from repo; interactive artifact | yes |
| 11 | **Trump mention-market data stories** | Two interactive explainers: "Pre-Speech Odds vs Reality" and "How Much Do Trump's Mention Streaks Matter?" | artifacts only | HTML | claude.ai artifacts (PWCu3Evxt1r8BCKK1hyZTj, RcocWzbBcbWkJmyVjxdDuQ) | self-contained HTML | yes, as a pair under Fantasy Reality |
| 12 | **Kalshi fees tracker** | Concept session only: 5 implementation paths ranked; no code. | none | — | — | — | skip (or "ideas" footnote) |
| 13 | **Voice-activated night light** | Session in `fakefellowship` context; hardware idea for daughter, blocked on mic choice. Branch no longer exists. | none | — | — | — | skip |
| 14 | **C.U.L.T. / CULTY-CLICKER** | Jun 2025 Replit-era; C.U.L.T. is a README stub, CULTY-CLICKER repo is empty (code lived on Replit). | private, empty | Replit | replit.com/@skemmis/CULTY-CLICKER | none | skip unless you still have the Replit |
| 15 | **Izzy** | Empty repo (Jun 2026). | public, empty | — | — | — | skip |
| 16 | **Relocation research pages** | Two artifacts: "Where the kids grow up: Spain/NL/Denmark" and "North American options: Vashon/Victoria/CDMX". Personal research, not products. | artifacts | HTML | claude.ai artifacts | — | skip (personal) |

Claude Code session log covered: 24 sessions, Mar–Sep 2026, across 9 repos.
Everything above with a ★ is a shipped, multiplayer-or-live thing; the rest
are tools, experiments, and analyses.

## Recommended cut (11 entries)

**Tier 1 — big cards, live embeds or video**
1. Fantasy Reality
2. Fate of the Fellowship online
3. La Brea Madre (game)
4. DegenBench

**Tier 2 — standard cards with a screenshot/gif**
5. Kalshi Mention Tracker
6. Sex House Island (SCUMM slice)
7. Crucible (needs a redeploy; it's static Vite + Three.js so it can live inside the portfolio itself)
8. Feed Unfucker
9. Newsletter chart-maker + Kalshi video series

**Tier 3 — "notes & analyses" strip**
10. Gizzard Hours
11. Trump mention-market data stories (pair)
12. La Brea Madre physical pulse-map (hardware) — could also be a Tier 2 card if you have photos of the build

A natural grouping falls out of this: **Prediction markets** (1, 2, 4, 9, 11),
**Games** (2, 3, 6, 7), **Tools & experiments** (8, 10, hardware).

## Assets we can pull today

- Fantasy Reality: `client/public/{logo,logo-wordmark,opengraph,backdrop,scene-source}`, `achievements/`, `character/`, `images/`.
- Fellowship: `packages/client/public/board.jpg` + `icons/*.png`.
- Newsletter: `charts/balogun-red-card/*.png` (4 finished charts) and `fr_newsletter/assets/sprites/`.
- Feed Unfucker: `fixtures/fake-feed/*.png` (safe, fake data).
- Gizzard Hours: regenerate charts from `kglw/` (`tools/export_png.py`).
- Artifacts (Gizzard Hours + 2 Trump stories): self-contained HTML, embeddable via iframe or copied in.

## Assets we need to capture

- Screenshots/gifs for every live app (Playwright is available here; I can script this once URLs are confirmed).
- Crucible: a 10-second clip of the sim, or rebuild and host it under the portfolio.
- Sex House Island: gif of the walk cycle + puzzle solve.
- La Brea Madre: map screenshot; photos of the physical pulse map if it was built.

## Things only you can answer

1. Railway URLs for Fellowship, La Brea Madre, Sex House Island, and the newsletter wizard (the `*.up.railway.app` guesses all 404).
2. Is Crucible worth reviving? It's static, so it could be served from the portfolio at `/crucible`.
3. Do you want Fantasy Reality's private-repo work (DegenBench, achievements, AI players) described in detail, or kept at the level of the public site?
4. Was the pulse-map installation physically built? Photos would make it the most distinctive entry.
5. Name/handle for the site, and whether "vibe coded" is part of the framing (I'd lean yes — it's the story).
