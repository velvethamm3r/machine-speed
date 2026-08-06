# Machine Speed — daily run runbook

Everything the site shows comes from one file. A run edits `data.json`, commits, and
GitHub Actions does the rest. Live at **https://machinespeed.techpointe.org**.

## The 5-minute version

1. Check the clock: `date "+%Y-%m-%d"` and `TZ=America/New_York date "+%H:%M"`. Never trust a cached date.
2. Read `dashboard-memory.md`. Anything already listed there is not "new today."
3. Research the four lanes for everything since `coverageEnd` in `data.json`. Verify every item against a source you actually opened.
4. Edit `data.json` — the only file a normal run touches. Move `coverageEnd` to today, add the new items, and leave the older ones in place. Schema is in `SCHEMA.md`.
5. Run `python3 build.py`. It validates first and refuses to write if the data is broken.
6. Append this run to `dashboard-memory.md` and update the watchlist there.
7. Commit and push `data.json`, `archive/`, `newsletter/` and `dashboard-memory.md`. The site rebuilds and deploys in about a minute.

Preview before committing: `python3 -m http.server -d dist 8000` → http://localhost:8000

## What build.py produces

| Output | What it is |
|---|---|
| `dist/` | The whole pre-rendered site. Generated — never edit, never commit (it's in `.gitignore`). |
| `dist/week/YYYY-MM-DD/` | One page per Monday-to-Sunday week, all four lanes, generated from the items themselves. A week with no items gets no page. |
| `dist/sitemap.xml`, `dist/robots.txt` | Crawl hints. The sitemap lists the board, the lanes, About and every week page; dated snapshots are deliberately left out so crawlers aren't pointed at copies of the board. |
| `dist/CNAME` | The custom domain, written on every build so a deploy can't silently drop it. |
| `archive/machine-speed-YYYY-MM-DD.html` | Today's snapshot, written back into the repo so history survives rebuilds. **Commit this.** |
| `newsletter/machine-speed-YYYY-MM-DD.md` | Paste-ready Substack draft of the same board. **Commit this.** Nothing is ever sent automatically. |
| `dist/feed.xml` | RSS 2.0, one entry per item, absolute URLs from `SITE_URL`. |

`build.py` exits non-zero on a validation error and writes nothing. A bad `data.json`
fails the Action instead of publishing — the live site keeps serving the last good deploy.

## What it validates

Errors (build stops): missing top-level keys; an item missing any required field; duplicate
item `id`; an unknown lane or confidence value; a non-`https://` URL; a malformed or
future-dated item; a watchlist entry with no status; an `archives[]` entry pointing at a file
that isn't in the repo; no `archives[]` entry for today.

Warnings (build continues, message printed): the run stamp is not today; an item is more than
seven days old — allowed, but `judgmentNote` should say why; more than six items qualify for
the 48-hour strip, so only the newest six will show; nothing qualifies for the strip at all,
which is the correct outcome on a genuinely quiet day.

## Editing data.json for a run

Change `updatedISO` and `updatedDisplay` to now. Rewrite `judgmentNote` (what you had to call
by hand — corrections, unverifiable details dropped, thin lanes) and `internalNote` (one
sentence on what changed since the last run). Add new items to `items[]`, delete items now
older than seven days, and update `watchlist[]` statuses — carry threads forward unchanged
rather than deleting them when nothing moved. Add a new entry at the top of `archives[]` with
today's date and file path.

To force an item into the "New in the last 48 hours" strip when it is new to the board but a
few days old in the world, set `isNew: true`. To keep a genuinely recent item out, set
`isNew: false`. Omit the field and the 48-hour date rule applies.

## Sourcing rules the build cannot check

These are the rules that matter most and no script can enforce them: every item needs a real
source URL you opened; if you cannot verify it, omit it — fewer real items beats more shaky
ones, and padding is never acceptable; never invent a CVE number, statistic, date, quote or
attribution; when a figure appears in press coverage but not the primary source, use the
primary and note the discrepancy in `judgmentNote`; label confidence honestly, using `vendor`
for unreproduced benchmark claims; and watch for content-farm embellishment, which usually
shows up as an oddly precise number attached to a real story.

## Configuration

All at the top of `build.py`:

| Constant | Purpose |
|---|---|
| `SITE_URL` | `https://machinespeed.techpointe.org`. Drives canonical URLs, Open Graph, JSON-LD, RSS, and `dist/CNAME`. |
| `SUBSTACK_URL` | Empty by default. Set it to the publication home and the Subscribe link appears in the nav on every page plus a subscribe block on the board. Leave empty and every Substack element disappears. |
| `SUBSTACK_CTA` | Heading text on the subscribe block. |
| `NEW_WINDOW_DAYS` / `STRIP_MAX` | 48-hour rule and the six-item cap on the strip. |
| `COVERAGE_SLACK_DAYS` | How far outside `coverageStart` / `coverageEnd` an item may fall before `validate()` warns. `0` means the stated period must contain every item exactly. |
| `NOTE_PLACEMENT` | Where the editorial note prints on the board: `"footer"` (a collapsed disclosure below the sources), `"header"` (under the hero, the old position), or `"none"`. The note still goes into `data.json`, the archive snapshot and the newsletter draft either way — this only controls the board. |
| `SHOW_INTERNAL_NOTE` | Whether `internalNote` prints in the site footer. `False` by default — it is a working note, so it stays in `data.json` and git history rather than on the page. |
| `GROUP_BY_WEEK` | Week headings inside each lane. `False` gives one flat newest-first list per lane. Headings only appear once a lane holds six or more items. |
| `FRONT_WEEKS` | How many recent weeks the board prints as full cards. Older weeks stay on the page as a one-line-per-item index linking into their own week pages. Raise it to push more onto the front page, lower it to keep the front page short. |

## The coverage period

The board states the span of days it covers rather than a rolling window. Set
`coverageStart` and `coverageEnd` in `data.json`; a normal run moves `coverageEnd`
to today and leaves `coverageStart` alone, so the period grows and the board keeps
its history on one page. If either key is missing the build derives it from the
oldest and newest item, which means the printed label can never claim days the
board does not actually show. To restart the period — a new quarter, say — set both
keys and drop the items that fall outside.

Items dated outside the period produce warnings, not errors: the build still ships,
and the fix is either to widen `coverageStart` or to drop the item. An item dated in
the future is a hard error.

## How the period is split across pages

A run adds items; the page structure follows from their dates, so there is nothing
extra to maintain.

The **board** (`/`) prints the most recent `FRONT_WEEKS` weeks as full cards, then
indexes every older item one line at a time under "Earlier in this period" — nothing
scrolls off, but the front page stops growing without limit. Each **week page**
(`/week/YYYY-MM-DD/`, dated by its Monday) carries that week's full cards across all
four lanes with previous/next links. The **lane pages** are unchanged: each still holds
the whole period for its lane, week-headed. The **archive** leads with the week index
and keeps the dated run snapshots below it.

Week pages are regenerated from `data.json` on every build, so an item corrected today
is corrected on its week page too. The dated snapshots in `archive/` are the opposite
by design — frozen, never rewritten. That is the distinction the archive page explains
to readers, and it is worth keeping straight: weeks are the living board, snapshots are
the record of what it said on a given day.

## The Substack side

The newsletter is a **draft-only** pipeline by design: the build writes
`newsletter/machine-speed-YYYY-MM-DD.md`, and a human opens it, reads it, and publishes it.
Nothing is posted, scheduled or emailed by any automated step.

To publish a day: open the draft, copy it, and paste into a new Substack post
(Substack's editor accepts pasted Markdown and keeps the links). The draft leads with the
48-hour strip, then each lane with confidence labels and source links, then the watchlist and
the editorial note.

For the other direction — a Subscribe link on the site — set `SUBSTACK_URL` and rebuild.

## Changing the design

`assets/style.css` and `assets/theme.js` are shared by every page. A daily run should not need
to touch either. If you add a confidence tier, add it in three places: `CONF` and `CONF_VAR` in
`build.py`, and a `.c-<name>` rule in `assets/style.css`.

## Hosting

GitHub Actions builds and deploys to GitHub Pages on every push to `main`
(`.github/workflows/deploy.yml`). Settings → Pages → Source must be set to **GitHub Actions**.
DNS: a `CNAME` record for host `machinespeed` pointing at `<your-username>.github.io`.
