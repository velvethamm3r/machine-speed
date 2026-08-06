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
├── data.json            ← single source of truth; the daily run edits ONLY this
├── build.py             ← generator (Python 3 stdlib only, no pip installs)
├── SCHEMA.md            ← every field of data.json, explained
├── RUNBOOK.md           ← the daily procedure
├── dashboard-memory.md  ← cross-run dedup + watchlist state; commit it or the next run repeats itself
├── assets/
│   ├── style.css        ← shared stylesheet, cached across all pages
│   └── theme.js         ← theme toggle (progressive enhancement)
├── archive/             ← dated board snapshots, committed to the repo
├── newsletter/          ← paste-ready Substack drafts, committed to the repo
└── dist/                ← build output (generated; don't edit, don't commit)
    └── week/            ← one folder per Monday-to-Sunday week, generated from item dates
```

Live at **https://machinespeed.techpointe.org**.

## Build locally

```bash
python3 build.py        # validates data.json, then writes ./dist
```

Preview: `python3 -m http.server -d dist 8000` → http://localhost:8000

The build validates before it writes anything and exits non-zero on a structural
error, so a broken `data.json` fails the deploy instead of publishing a bad board —
the live site simply keeps serving the last good version. `RUNBOOK.md` lists exactly
what is an error and what is only a warning.

Configuration lives at the top of `build.py`: `SITE_URL` (drives canonical URLs, Open
Graph, JSON-LD, RSS and `dist/CNAME`) and `SUBSTACK_URL` (empty by default; set it to
the publication home to turn on the Subscribe links).

## Deploy — GitHub Pages (how this repo is set up)

`.github/workflows/deploy.yml` runs on every push to `main`: it builds the site,
commits today's archive snapshot and newsletter draft back into the repo, and
publishes `dist/` to GitHub Pages. Nothing to run by hand.

Two settings make it work, both one-time:

- **Settings → Pages → Source: GitHub Actions** (not "Deploy from a branch").
- **DNS on `techpointe.org`:** a `CNAME` record, host `machinespeed`, pointing at
  `YOUR-USERNAME.github.io`. A subdomain needs only that one record — the four
  `185.199.x.x` A records are for bare apex domains and are not needed here.

`build.py` writes `dist/CNAME` on every build, so the custom domain is reasserted
by each deploy rather than living only in a settings field that can be cleared.
Tick **Enforce HTTPS** in Settings → Pages once the domain check goes green.

Full click-by-click walkthrough: `SETUP_GUIDE.md`.

**Cloudflare Pages** also works unchanged if you ever want per-commit previews:
build command `python3 build.py`, output directory `dist`, framework preset None.

## The Substack newsletter

Every build writes `newsletter/machine-speed-YYYY-MM-DD.md` — the same board as a
paste-ready Markdown post. It is a **draft only**: nothing is posted, scheduled or
emailed by any automated step. A human opens it, reads it, and publishes it.

Setting `SUBSTACK_URL` at the top of `build.py` adds a Subscribe link to the nav on
every page and a subscribe block on the board. It's a plain link, not Substack's
iframe embed, so the site stays dependency-free and loads no third-party tracking.

## The daily publishing run (Cowork)

Each day, the job should:

1. **Read `dashboard-memory.md` first** — anything already listed there is not
   "new today". Update it at the end of the run.
2. **Edit `data.json` only** — update `updatedISO` / `updatedDisplay`,
   `judgmentNote`, `internalNote`; move `coverageEnd` forward and add `items`
   inside the stated period;
   update `watchlist`; append today's entry to `archives`, e.g.
   `{"date": "2026-07-28", "file": "archive/machine-speed-2026-07-28.html", "items": 9, "note": "…"}`.
3. **Run `python3 build.py`** — validates first, then writes today's snapshot into
   `archive/` and the newsletter draft into `newsletter/` (both source-controlled,
   so they survive every rebuild).
4. **Commit and push** `data.json`, `archive/`, `newsletter/` and
   `dashboard-memory.md` — and nothing in `dist/`. The Action rebuilds and deploys.

That preserves the original design's property — one file drives the whole
site — while everything the reader sees is real, indexable HTML.

The sourcing rules that no script can enforce are in `RUNBOOK.md`; the field-level
reference is in `SCHEMA.md`.

## Data format quick reference

- `items[].lane`: `cap` | `pol` | `def` | `atk`
- `items[].confidence`: `confirmed` | `claimed` | `researchers` | `press` |
  `official` | `vendor`
- `coverageStart` / `coverageEnd`: `YYYY-MM-DD` — the period the board claims to
  cover, printed in the header and on every lane page. Optional: if either is
  omitted it falls back to the oldest / newest item on the board, so the stated
  period can never advertise days the board does not actually cover
- `items[].date`: `YYYY-MM-DD` — must fall inside the coverage period (anything
  outside it is a build warning, not a silent drop); items ≤ 2 days old
  automatically get the New badge and appear in the 48-hour strip
- Inside each lane, items are grouped under Monday–Sunday week headings once a
  lane holds six or more. Set `GROUP_BY_WEEK = False` in `build.py` for one flat
  list per lane
- `about`: array of paragraphs for the About page

## What the generator emits

- `index.html` — the board: the most recent `FRONT_WEEKS` weeks as full cards,
  then every older item indexed one line at a time, plus stats, pure-CSS charts
  (with screen-reader labels), watchlist, sources, and JSON-LD `ItemList`
- `week/YYYY-MM-DD/` — one page per Monday-to-Sunday week, all four lanes, with
  previous/next links. Generated from the item dates, so weeks appear and
  disappear on their own; a week with no items gets no page
- `capability.html`, `policy.html`, `defense.html`, `attacks.html` — lane pages,
  each holding the whole coverage period for its lane
- `archive.html` — the week index first, dated run snapshots below it
- `archive/machine-speed-YYYY-MM-DD.html` — frozen snapshot pages. Weeks are
  regenerated every build and reflect corrections; snapshots never are
- `about.html`
- `feed.xml` — RSS 2.0 with one entry per item
- `sitemap.xml` and `robots.txt` — canonical routes only; snapshots are left out
  so crawlers aren't pointed at copies of the board
- Canonical URLs, Open Graph/Twitter meta on every page; flash-free theme
  init in `<head>`; `prefers-reduced-motion` respected
