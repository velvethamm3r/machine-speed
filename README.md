# Machine Speed

A daily, source-verified intelligence board tracking frontier AI cyber
capability against the defense and policy lag.

Live at **https://machinespeed.techpointe.org**.

## How it works

All content lives in one file — `data.json` — and `build.py` turns it into a
fully pre-rendered static site: HTML pages, an RSS feed, JSON-LD, a sitemap,
and a dated archive snapshot. Every headline, summary and source is in the
HTML itself, so search engines, RSS readers, link previews, screen readers and
no-JS browsers all see the full content. The only client-side JavaScript is the
light/dark theme toggle. Nothing loads from a CDN.

```
├── data.json     ← single source of truth
├── build.py      ← generator (Python 3 stdlib only, no dependencies)
├── assets/       ← stylesheet + theme toggle
├── archive/      ← dated board snapshots
├── newsletter/   ← Markdown drafts of each day's board
└── dist/         ← build output (generated; not committed)
```

## Build

```bash
python3 build.py                        # validates data.json, then writes ./dist
python3 -m http.server -d dist 8000     # preview at http://localhost:8000
```

The build validates before it writes anything and exits non-zero on a
structural error, so a broken `data.json` fails the deploy instead of
publishing a bad board — the live site keeps serving the last good version.

`.github/workflows/deploy.yml` runs this on every push to `main` and publishes
`dist/` to GitHub Pages. Nothing to run by hand.

## Docs

`SCHEMA.md` documents every field of `data.json`. `RUNBOOK.md` is the daily
procedure and the editorial rules. `SETUP_GUIDE.md` is the one-time hosting and
DNS setup.

The newsletter side is draft-only by design: each build writes a Markdown draft
into `newsletter/`, and a human opens it, reads it, and decides whether to
publish. Nothing is posted, scheduled or emailed by any automated step.
