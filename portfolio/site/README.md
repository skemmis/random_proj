# samkemmis portfolio

A fullscreen retro OS ("SKOS") that boots and shows my projects as cartridges on a desktop. Static site, no dependencies.

- `projects.json` is the only file you edit to add, reorder, or reword a project.
- `build.mjs` turns it into `dist/`: copies `public/`, generates the boot text, the desktop icons, one window per project, the All-projects table, README.txt and Trash.
- `src/app.js` is the window manager: boot sequence (plays on every load, skippable), drag, minimize, zoom, taskbar, start menu, `#slug` deep links, draggable icons with positions saved in localStorage.
- Drop a pixel-art portrait at `public/art/avatar.png` and it appears in README.txt and the start button.
- `server.mjs` serves `dist/` with long cache headers on media. Railway runs it.

## Run locally

```bash
npm run dev      # builds, then serves on http://localhost:3000
```

## Deploy on Railway

1. Railway → New → GitHub Repo → `skemmis/random_proj`, and pick the branch.
2. Nothing else. The repo root has a shim `package.json` and `railway.json` that build and start the site from `portfolio/site`, so the Root Directory setting can stay blank. (Setting it to `portfolio/site` also works; that folder has its own copies.)
3. Generate a domain under Settings → Networking. Every push to the connected branch redeploys.

## Adding a project

Add an object to `projects.json`. Fields: `slug`, `name`, `one` (one line), `group` (`play` | `bet` | `read` | `also`), `status` (`live` | `paused` | `retired` | `unlinked`), `year`, `url`, `repo`, `tools`, `stack`, `featured`, `description`, `notes`. Optional `sq` and `wide` override the screenshots.

Screenshots live in `public/shots/<slug>.webp` (16:9, 1600 wide) and `public/shots/<slug>-sq.webp` (800×800). Self-hosted pages go in `public/notes/` and are linked with a relative `url`.
