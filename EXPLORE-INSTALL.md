# Explore board — install

Four files. Nothing else in the repo changes, and your daily run does not change at all.

## What to commit

| File | Action |
| --- | --- |
| `build.py` | Replace the existing one. |
| `assets/style.css` | Replace the existing one. |
| `assets/board.css` | New file. |
| `assets/board.js` | New file. |

`style.css` changed because the headline face is now site-wide, not an Explore
special case: Newsreader on headline text only — page titles, item headlines, the
compressed week index, brief and act headings — with every label, count, table
header and paragraph left on the UI sans. It loads from Google Fonts on every
page, including the archive snapshots, so past boards match the live one.

To undo just the font: set `DISPLAY_FONT_URL = ""` at the top of `build.py` and
`--display:inherit` in `style.css`. Everything falls back to the sans and no
request is made.

Commit those three. The Action rebuilds and `/explore.html` is live, linked from the
nav on every page as **Explore**, right after Board.

## What it does

`build.py` gains one page and one config pair:

    EXPLORE_PAGE = "explore.html"   # set to "" and the page, its nav link,
    EXPLORE_NAV  = "Explore"        # its assets and its sitemap entry vanish

The page carries the same `data.json` items, inlined at build time as JSON — no
fetch, no second request, nothing to keep in sync. Three things it adds over the
pre-rendered board:

1. **A lane x week matrix as the navigator.** Every cell is a two-axis filter
   (that lane, that week); a lane name filters the lane, a week label scopes the
   week, and the gutter carries each lane's ten-week trend and its distance from
   its own average. The matrix ignores the lane filter on purpose, so it stays
   the way you jump to another lane's busy week.
2. **Running stories.** Related items collapse into one thread that can span
   weeks. Your `watchlist[]` threads are the primary keys — they are the
   editorial judgement already made — and two-word proper-noun phrases from
   headlines are the fallback. Threads longer than three items open as one item
   plus a date timeline and a clickable thread index; shorter ones just list.
   Everything not in a story falls through to a by-week, by-lane ledger.
3. **Unread per visitor.** Held in `localStorage`, seeded from the previous
   run's date in `archives[]` on a first visit, with a "Mark all read" control.
   No build-time date, no cookie, nothing stored server side.

Filter state is written to the query string (`?lane=atk&week=2026-08-24`), so a
scoped view is a link you can send.

## Design notes

- `board.css` reads your existing tokens (`--ink`, `--panel`, `--cap` …) and
  falls back to its own values only if one is missing, so the theme toggle drives
  this page like every other one and there is no second palette to maintain.
  `--x-display` is the one hook worth knowing: point it at a display face and
  every headline in the view picks it up.
- `board.js` is the only JavaScript on the site that does real work. It is
  dependency-free, ~500 lines, and reads colours from the stylesheet rather than
  holding a copy of the palette.
- With JavaScript off, the page shows a plain list of week links instead of an
  empty box — the same content the pre-rendered pages already serve.

## What the daily run should know

Nothing. It keeps editing `data.json`, `archive/` and `newsletter/`. The Explore
page regenerates from `data.json` like every other page, so new items, new lanes
and new watchlist threads appear there without a code change. Two small things
worth noting in `DAILY_RUN.md` if you want them written down:

- A new watchlist thread becomes a story key on the next build. Naming threads
  the way you'd want the story titled is now a small editorial lever.
- `archives[]` is what seeds a first-time visitor's unread mark, which is one
  more reason the entry for today matters.
