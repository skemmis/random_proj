# samkemmis portfolio

A shelf of projects built with AI coding agents. Static site, no dependencies.

- `projects.json` is the only file you edit to add, reorder, or reword a project.
- `build.mjs` turns it into `dist/` (copies `public/`, generates the HTML, falls back to a monogram tile when a project has no screenshot).
- `server.mjs` serves `dist/` with long cache headers on media. Railway runs it.

## Run locally

```bash
npm run dev      # builds, then serves on http://localhost:3000
```

## Deploy on Railway

1. Railway → New → GitHub Repo → `skemmis/random_proj`.
2. In the service settings set **Root Directory** to `portfolio/site`. The `railway.json` there sets the build (`npm run build`) and start (`npm start`) commands.
3. Generate a domain. Every push to the connected branch redeploys.

## Adding a project

Add an object to `projects.json`. Fields: `slug`, `name`, `one` (one line), `group` (`play` | `bet` | `read` | `also`), `status` (`live` | `paused` | `retired` | `unlinked`), `year`, `url`, `repo`, `tools`, `stack`, `featured`, `description`, `notes`. Optional `sq` and `wide` override the screenshots.

Screenshots live in `public/shots/<slug>.webp` (16:9, 1600 wide) and `public/shots/<slug>-sq.webp` (800×800). Self-hosted pages go in `public/notes/` and are linked with a relative `url`.
