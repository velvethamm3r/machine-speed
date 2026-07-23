# Machine Speed — static site generator

A daily, source-verified intelligence board, built as a fully pre-rendered
static site. All content lives in one file — `data.json` — and `build.py`
turns it into HTML pages, an RSS feed, JSON-LD, and a dated archive snapshot.

Why pre-rendered: every headline, summary, and source is in the HTML itself,
so search engines, RSS readers, link previews, screen readers, and no-JS
browsers all see the full content. The only client-side JavaScript left is
the light/dark theme toggle.

## Layout

```
machine-speed-site/
├── data.json          ← single source of truth; the daily run edits ONLY this
├── build.py           ← generator (Python 3 stdlib only, no pip installs)
├── assets/
│   ├── style.css      ← shared stylesheet, cached across all pages
│   └── theme.js       ← theme toggle (progressive enhancement)
├── archive/           ← dated board snapshots, committed to the repo
└── dist/              ← build output (generated; don't edit, don't commit)
```

## Build locally

```bash
python3 build.py        # writes ./dist
```

Preview: `python3 -m http.server -d dist 8000` → http://localhost:8000

Before deploying, set `SITE_URL` at the top of `build.py` to your real domain
(it's used for canonical URLs, Open Graph tags, JSON-LD, and the RSS feed).

## Deploy: GitHub + Cloudflare Pages (recommended)

1. **Push this folder to a GitHub repo** (public or private).
2. In the Cloudflare dashboard: **Workers & Pages → Create → Pages →
   Connect to Git**, pick the repo.
3. Build settings:
   - **Build command:** `python3 build.py`
   - **Build output directory:** `dist`
   - Framework preset: None. No environment variables needed.
4. Deploy. Every future `git push` rebuilds and publishes automatically,
   usually in under a minute.

You get a free `*.pages.dev` URL immediately; add a custom domain under the
project's **Custom domains** tab.

**GitHub Pages alternative:** also works — add a GitHub Action that runs
`python3 build.py` and publishes `dist` with `actions/deploy-pages`.
Cloudflare Pages is less setup and gives you preview deploys per commit.

**Squarespace note:** Squarespace can't host this (it doesn't serve custom
static builds or run build steps). If your domain is registered there, keep
it and just point DNS at Cloudflare Pages: add the custom domain in
Cloudflare, then create the CNAME record Squarespace's DNS panel asks for.

## The daily publishing run (Cowork)

Each day, the job should:

1. **Edit `data.json` only** — update `updatedISO` / `updatedDisplay`,
   `judgmentNote`, `internalNote`; add/remove `items` (7-day window);
   update `watchlist`; append today's entry to `archives`, e.g.
   `{"date": "2026-07-24", "file": "archive/machine-speed-2026-07-24.html", "items": 9, "note": "…"}`.
2. **Run `python3 build.py`** — this validates the JSON renders cleanly and
   writes today's snapshot into `archive/` (source-controlled, so past days
   survive every rebuild).
3. **Commit and push** `data.json` + `archive/` (and nothing in `dist/`).
   Cloudflare Pages rebuilds and deploys on push.

That preserves the original design's property — one file drives the whole
site — while everything the reader sees is real, indexable HTML.

## Data format quick reference

- `items[].lane`: `cap` | `pol` | `def` | `atk`
- `items[].confidence`: `confirmed` | `claimed` | `researchers` | `press` |
  `official` | `vendor`
- `items[].date`: `YYYY-MM-DD` — items older than 7 days should be removed
  by the daily run; items ≤ 2 days old automatically get the New badge and
  appear in the 48-hour strip
- `about`: array of paragraphs for the About page

## What the generator emits

- `index.html` — full board with lanes, stats, pure-CSS charts (with
  screen-reader labels), watchlist, sources, and JSON-LD `ItemList`
- `capability.html`, `policy.html`, `defense.html`, `attacks.html` — lane pages
- `archive.html` + `archive/machine-speed-YYYY-MM-DD.html` — snapshot pages
- `about.html`
- `feed.xml` — RSS 2.0 with one entry per item
- Canonical URLs, Open Graph/Twitter meta on every page; flash-free theme
  init in `<head>`; `prefers-reduced-motion` respected
