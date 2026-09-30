# Machine Speed

A daily, source-verified intelligence board tracking AI cyber
capability against the defense and policy lag.

Live at **https://machinespeed.techpointe.org**.

Five lanes — capability, policy, defense, attacks and markets — plus *briefs*:
pages that lay a single incident out in dated stages, each stage separately
sourced, so what an organisation confirmed on day one stays visibly distinct
from what the press reconstructed a week later. A long brief can group those
stages into numbered panels, two abreast where two panels answer one question.

## How it works

All content lives in one file — `data.json` — and `build.py` turns it into a
fully pre-rendered static site: HTML pages, an RSS feed, JSON-LD, a sitemap,
and a dated archive snapshot. Every headline, summary and source is in the
HTML itself, so search engines, RSS readers, link previews, screen readers and
no-JS browsers all see the full content. The client-side JavaScript is the
light/dark theme toggle, the Explore board's search and filtering, and a
Cloudflare Web Analytics beacon. Two requests leave the page — the display face
from Google Fonts and the analytics beacon — and nothing else is fetched from a
CDN; empty `DISPLAY_FONT_URL` and `WEB_ANALYTICS_TOKEN` in `build.py` and even
those two stop.

```
├── data.json     ← single source of truth
├── entered.json  ← ledger: item id → the run date it entered the board (build-written, committed)
├── forecasts.json       ← the analyst's forecasts and resolutions (hand-written; see FORECASTS.md)
├── forecasts.lock.json  ← forecasts integrity ledger (written and committed by the Action only)
├── forecasts.py         ← forecast validation, scoring and the /forecasts/ page
├── layers.py            ← the front page (This week banner, topics, search, a card per week) and topic pages
├── topics.json          ← the six topics readers browse by, each with a one-line definition
├── insights.py          ← findings, entities, open data, methodology, corrections, digest drafts
├── entities.json        ← entity registry: names and aliases the build tags items with
├── CITATION.cff         ← how to cite the dataset (GitHub shows a "Cite this repository" button)
├── .zenodo.json         ← metadata Zenodo uses when it archives a release and issues a DOI
├── build.py      ← generator (Python 3 stdlib only, no dependencies)
├── assets/       ← stylesheet, theme toggle, favicon, Explore board (board.css/js), This week banner (home.js)
├── archive/      ← dated board snapshots
├── newsletter/   ← Markdown drafts of each day's board
└── dist/         ← build output (generated; not committed)
    ├── index.html          the board — filterable, story-clustered (needs JS)
    ├── <lane>/             one page per lane, holding the whole period
    ├── week/YYYY-MM-DD/    one page per week
    ├── briefs/             brief index
    ├── brief/<slug>/       one brief, in dated stages
    ├── archive/            week index (snapshots listed only if SHOW_RUN_SNAPSHOTS)
    ├── about/
    ├── <lane>.html …       redirect stubs at the old flat paths
    ├── feed.xml            RSS 2.0 — the whole board, in event order
    └── new.xml             RSS 2.0 — only items as they enter the board
```

**Two feeds, and a carousel.** `feed.xml` is the whole board in event order —
when things happened. `new.xml` is the delta in *entry* order — when the board
learned them, capped at the last 40, `pubDate` set to the entry date. The
carousel at the top of the landing page reads the same order and shows the
current day's arrivals, so an item rotates out once it stops being new.

An incident dated three weeks ago that the board picks up today enters today.
That distinction is why entry dates live in `entered.json` rather than being
inferred from `data.json`, and why a reader who checks once a week still
receives every item that entered in between.

## Build

```bash
python3 build.py                        # validates data.json, then writes ./dist
python3 -m http.server -d dist 8000     # preview at http://localhost:8000
```

Every page except the landing page is a directory holding `index.html`, so URLs
carry no `.html` — GitHub Pages serves files literally and will not strip an
extension. The old flat paths stay behind as redirect stubs permanently, because
the frozen snapshots in `archive/` link to them and are never rewritten.

Explore (`/explore.html`, "Search" in the navigation) is the interactive board: search, a lane and week filter, related items
collapsed into running stories, and an unread mark per visitor held in
`localStorage`. It is the only page that needs JavaScript. Every item is also
pre-rendered on the lane and week pages, which need none, and that pre-rendered
markup is still what each dated snapshot is a copy of. `LANDING` and `BOARD_PAGE`
at the top of `build.py` control the arrangement.

The build validates before it writes anything and exits non-zero on a
structural error, so a broken `data.json` fails the deploy instead of
publishing a bad board — the live site keeps serving the last good version.

`.github/workflows/deploy.yml` runs this on every push to `main` and publishes
`dist/` to GitHub Pages. Nothing to run by hand.

**Front page.** The board is the record; the front page is the way in. It opens with This
week — the editor's picks (`weekly[]` in data.json), or the week's newest items until they are
chosen — then the six topics (`topics.json`) and one card per week linking to that week's page.
The front page is "The Board" in the navigation. `/watchlist/` ("Watchlist") shows the six topics,
each with its newest watchlist status line (`watchlist[].topic` in data.json), and the threads no
topic covers; `/topic/<id>/` pages list a topic's watchlist threads and then its items week by
week. Every page has a search box in its header that leads to `/search/`, which searches
`data/items.json` in the browser (`assets/search.js`). Explore was retired on 2026-09-30;
`/explore.html` redirects (a `?q=` goes on to Search), and `EXPLORE_PAGE` in build.py brings it back.

`SHOW_FINDINGS` and `SHOW_FORECASTS` at the top of build.py hold those two pages back from the
live site while they are reviewed; the code and data behind them are unchanged. Each `/topic/<id>/` page lists its items
week by week, one line each.

**Findings and open data.** `/findings/` counts the board instead of reading it: the
response lag from each topic's first capability or attack item to its first policy, defense
and markets item (from the optional `topics` field on items), weekly trends by lane, the
confidence mix, and how fast items reach the board. `/entities/` indexes every organisation,
model family and platform the items name (from `entities.json`). `/data/` publishes the whole
board as CSV and JSON under CC BY 4.0. `/methodology/` and `/corrections/` put the sourcing
rules and the corrections log in public. Each build also drafts a weekly one-pager and a
quarterly report into `newsletter/`, like the daily newsletter draft — never published.

**Forecasts.** The board reports and does not forecast. `/forecasts/` is kept apart
from it: probabilistic calls written by hand in `forecasts.json`, fingerprinted when
first published so they cannot be edited afterwards, resolved against sources (or, for
questions about the board's own counts, by the build), and scored with the Brier score.
`FORECASTS.md` has the detail.

## Docs

`SCHEMA.md` documents every field of `data.json`. `RUNBOOK.md` is the daily
procedure and the editorial rules. `SETUP_GUIDE.md` is the one-time hosting and
DNS setup.

The newsletter side is draft-only by design: each build writes a Markdown draft
into `newsletter/`, and a human opens it, reads it, and decides whether to
publish. Nothing is posted, scheduled or emailed by any automated step.
