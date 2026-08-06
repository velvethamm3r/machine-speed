# Machine Speed — daily run runbook

Everything the site shows comes from one file. A run edits `data.json`, commits, and
GitHub Actions does the rest. Live at **https://machinespeed.techpointe.org**.

## The 5-minute version

1. Check the clock: `date "+%Y-%m-%d"` and `TZ=America/New_York date "+%H:%M"`. Never trust a cached date.
2. Read `dashboard-memory.md`. Anything already listed there is not "new today."
3. Research the five lanes for everything since `coverageEnd` in `data.json`. Verify every item against a source you actually opened.
4. Edit `data.json` — the only file a normal run touches. Move `coverageEnd` to today, add the new items, and leave the older ones in place. Schema is in `SCHEMA.md`.
5. Run `python3 build.py`. It validates first and refuses to write if the data is broken.
6. Append this run to `dashboard-memory.md` and update the watchlist there.
7. Commit and push `data.json`, `archive/`, `newsletter/` and `dashboard-memory.md`. The site rebuilds and deploys in about a minute.

Preview before committing: `python3 -m http.server -d dist 8000` → http://localhost:8000

## What build.py produces

| Output | What it is |
|---|---|
| `dist/` | The whole pre-rendered site. Generated — never edit, never commit (it's in `.gitignore`). |
| `dist/week/YYYY-MM-DD/` | One page per Monday-to-Sunday week, every lane that has items that week, generated from the items themselves. A week with no items gets no page. |
| `dist/briefs.html`, `dist/brief/<slug>/` | The brief index and one page per brief. Only written when `data.json` has a `briefs[]` key; with none, every trace of the feature disappears from the nav, the board and the sitemap. |
| `dist/sitemap.xml`, `dist/robots.txt` | Crawl hints. The sitemap lists the board, the lanes, About and every week page; dated snapshots are deliberately left out so crawlers aren't pointed at copies of the board. |
| `dist/CNAME` | The custom domain, written on every build so a deploy can't silently drop it. |
| `archive/machine-speed-YYYY-MM-DD.html` | Today's snapshot, written back into the repo so history survives rebuilds. **Commit this.** |
| `newsletter/machine-speed-YYYY-MM-DD.md` | Paste-ready Substack draft of the same board, with the run's working notes below a marked CUT HERE line. Delete that block before posting. **Commit this.** Nothing is ever sent automatically. |
| `dist/feed.xml` | RSS 2.0, one entry per item, absolute URLs from `SITE_URL`. |

`build.py` exits non-zero on a validation error and writes nothing. A bad `data.json`
fails the Action instead of publishing — the live site keeps serving the last good deploy.

## What it validates

Errors (build stops): missing top-level keys; an item missing any required field; duplicate
item `id`; an unknown lane or confidence value; a non-`https://` URL; a malformed or
future-dated item; a watchlist entry with no status; an `archives[]` entry pointing at a file
that isn't in the repo; no `archives[]` entry for today. Briefs are held to the same bar —
a duplicate or non-kebab-case slug, a stage missing a date, label or text, a stage with no
sources, a source with no outlet or a non-`https://` URL, and a stage dated in the future.
Where a brief has an `acts[]` layout the build also refuses the ways that layout can fail
silently: a repeated act id, a stage pointing at an act that does not exist, a stage with no
`act` at all (it would vanish from the page), more than two acts sharing a row, and a folded
item id that is not in `items[]`. And because the key was renamed on 2026-08-06, a `data.json`
still carrying `dossiers` is a hard error rather than a build that succeeds with every brief
page missing.

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

## Briefs — how a run maintains one

A lane item is a day. A brief is a story that keeps moving, and most days it does not move,
so most runs touch `briefs[]` not at all. Open one only when a story has already produced
three or four separately-sourced developments and looks like it will produce more — a single
incident with one disclosure is a lane item, not a brief.

These pages were called threads, and the key was called `dossiers`, until 2026-08-06. The
watchlist still has threads and always did: there, "thread" means a running storyline the
board keeps an eye on, which is a different thing entirely. The collision is most of why the
brief pages are not called threads any more.

When a story a brief tracks moves, add a stage rather than rewriting an existing one:
stages are a record of what was known when, and editing yesterday's stage to match today's
better information destroys exactly the thing the format exists to show. Give the stage its
own sources and its own confidence — a first-party postmortem published a week after a press
reconstruction is `confirmed` sitting next to `press`, and that contrast is the point. Then
move the brief's `updated` to the stage date, which is what re-sorts the index.

Two things get flagged instead of silently resolved. If two sources give a figure differently,
put both in `disputed` with the date each was captured, rather than picking one. If a stage
could be read as explaining the stage above it and the source makes no such connection, say so
in `note` — a brief's ordering implies causation whether or not you intend it, so an
unsupported adjacency has to be labelled. A stage whose only justification is that it makes
the timeline feel complete does not belong on the timeline.

Retiring a brief means setting `status` to something honest — "Resolved", "Dormant" — not
deleting it. The page keeps its URL and the record survives.

### When to add an acts[] layout

A brief renders as a single timeline by default, which stays readable for about eight stages.
Past that everything looks equally important and the reader has to hold the shape in their
head, which is the point at which `acts[]` earns its keep: it groups the same stages into
numbered panels — what happened, how it was contained, what each company said — and lets two
panels sit side by side when they are two answers to one question rather than two consecutive
beats. Full field reference in `SCHEMA.md`.

Two rules govern writing one. **An act headline must not introduce a fact no bullet supports.**
Every bullet in a panel is one of the brief's own sourced stages or an existing `items[]` entry
folded in by id, rendered with its own wording and its own source link; the headline is the one
line the layout asserts on its own, so it can only summarise what is underneath it. If you want
to say something the sources do not, the answer is a new stage with a source, not a headline.
**And a panel of folded items is an adjacency, not a causal claim** — the same problem `note`
exists for on a stage, one level up. A Markets or Government panel next to an incident panel
reads as a response to it whether or not anyone said so, so if no source makes that connection,
put a `note` on the act saying which sources do not.

Numbering is derived from the rows, never written down, so reordering `acts[]` renumbers the
page and nothing else. Deleting `acts[]` entirely drops the brief back to a plain timeline with
no sourced claim moved.

## Sourcing rules the build cannot check

These are the rules that matter most and no script can enforce them: every item needs a real
source URL you opened; if you cannot verify it, omit it — fewer real items beats more shaky
ones, and padding is never acceptable; never invent a CVE number, statistic, date, quote or
attribution; when a figure appears in press coverage but not the primary source, use the
primary and note the discrepancy in `judgmentNote`; label confidence honestly, using
`self-reported` for unreproduced benchmark claims; and watch for content-farm embellishment,
which usually shows up as an oddly precise number attached to a real story.

Confidence is about the shape of the claim, not the identity of the publisher — the tier
definitions are in `SCHEMA.md` and the trap is always the same one. A lab, a company and an
agency can each produce `on-record` items and `self-reported` items on the same day.
`on-record` is for statements that constitute the fact and that only the speaker could make,
which in practice means they cost the speaker something; `self-reported` is for testable claims
where the party measuring is the party being measured and nobody independent has checked. When
an announcement carries a benchmark inside it, ask which half the `core` sentence rests on — if
a reader's takeaway is the score, the item is `self-reported` no matter who published it.

These two tiers were called `official` and `vendor` until 2026-08-06. If you are reading an
older snapshot in `archive/`, or an old run's notes, that is the same distinction under the
previous names.

The Markets lane needs one rule of its own. It covers how the money prices the risk — cyber
insurance, underwriting, liability and the capital response — and that beat runs heavily on
carrier and broker marketing, where a product launch is written to read as a market finding.
A new policy wording is a `self-reported` item unless a regulator, a court or a loss report says
otherwise, and a carrier's own claims data is `on-record` rather than `confirmed`. Material
that predates `coverageStart` belongs in the watchlist, not backdated onto the board.

## Configuration

All at the top of `build.py`:

| Constant | Purpose |
|---|---|
| `SITE_URL` | `https://machinespeed.techpointe.org`. Drives canonical URLs, Open Graph, JSON-LD, RSS, and `dist/CNAME`. |
| `SUBSTACK_URL` | Set to `https://velvethamm3r.substack.com`, which puts the newsletter link in the nav on every page and a subscribe block on the board. Empty it and every Substack element disappears. Point it at a subdomain of this site rather than `*.substack.com` and the links stop being treated as outbound — same tab, no ↗ — because `same_site()` compares the registrable domain. |
| `SUBSTACK_NAV` | The nav label. `"Subscribe"` by default; `"Newsletter"` reads as a section of the site rather than an ask, which is the better label once the newsletter lives on your own subdomain. |
| `SUBSTACK_CTA` | Heading text on the subscribe block. |
| `NEW_WINDOW_DAYS` / `STRIP_MAX` | 48-hour rule and the six-item cap on the strip. |
| `COVERAGE_SLACK_DAYS` | How far outside `coverageStart` / `coverageEnd` an item may fall before `validate()` warns. `0` means the stated period must contain every item exactly. |
| `NOTE_PLACEMENT` | Where the editorial note prints on the board: `"none"` (the default — off), `"footer"` (a collapsed disclosure below the sources), or `"header"` (under the hero, the old position). The dated snapshot copies the board and follows this setting; `data.json` and the newsletter draft always keep the note, so the record survives either way. |
| `FOOTER_NOTE` | Optional tagline in the footer between the site name and the copyright. Empty by default, which leaves the footer as just the site name and the year. |
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
(`/week/YYYY-MM-DD/`, dated by its Monday) carries that week's full cards across every
lane that has items that week, with previous/next links. The **lane pages** are unchanged:
each still holds the whole period for its lane, week-headed. **Briefs** (`/briefs.html`)
indexes them, each at its own `/brief/<slug>/`; those sit outside the period
entirely, since a brief's whole purpose is to reach back past it. The **archive** leads
with the week index and keeps the dated run snapshots below it.

Week pages are regenerated from `data.json` on every build, so an item corrected today
is corrected on its week page too. The dated snapshots in `archive/` are the opposite
by design — frozen, never rewritten. That is the distinction the archive page explains
to readers, and it is worth keeping straight: weeks are the living board, snapshots are
the record of what it said on a given day.

## The Substack side

The newsletter is a **draft-only** pipeline by design: the build writes
`newsletter/machine-speed-YYYY-MM-DD.md`, and a human opens it, reads it, and publishes it.
Nothing is posted, scheduled or emailed by any automated step.

To publish a day: open the draft, copy everything **above** the `CUT HERE` line, and paste
into a new Substack post (Substack's editor accepts pasted Markdown and keeps the links).
The publishable part leads with the 48-hour strip, then each lane with confidence labels and
source links, then the watchlist.

Below the cut are the run's working notes — the calls it made, what it de-duplicated, what it
left off and why, and what changed since the previous run. That is the generator's account of
its own decisions, not the editor's judgment, so it is deliberately kept off the site, off the
dated snapshot and out of the published post. Read it, rewrite in your own words anything
worth keeping, and delete the block before posting.

For the other direction — a newsletter link on the site — set `SUBSTACK_URL` and rebuild.

Substack can serve the publication from a subdomain of this site, which is what makes the
newsletter read as part of the property rather than a link off it. Substack charges a one-time
$50 fee, requires a subdomain rather than a bare root domain, and issues the CNAME target from
Settings → Domain once you enter the hostname; allow up to 36 hours to configure. Pick a host
that is not `machinespeed` — `newsletter.techpointe.org` — because that name already has a
`CNAME` pointing at GitHub Pages and one hostname cannot serve two sites. Then set
`SUBSTACK_URL` to the new host and rebuild: the nav link and the subscribe button drop their
`target="_blank"` automatically. Note the limit of the approach — Substack renders Substack's
design at that address. The shared domain makes it one property; it does not make it one theme.

## Changing the design

`assets/style.css`, `assets/theme.js` and `assets/icon.svg` are shared by every page. A daily
run should not need to touch any of them. If you add a confidence tier, add it in three places:
`CONF` and `CONF_VAR` in `build.py`, and a `.c-<name>` rule in `assets/style.css`.

Adding a lane is a `LANES` entry in `build.py`, a `--x` / `--x-soft` pair in both themes, and a
`.lp-x` pill rule. Nothing else counts lanes by hand: the stats grid reflows on `auto-fit`, the
lane bar generates itself from `LANES`, and prose that says "five lanes" derives the word. The
nav is deliberately two rows — the site nav carries the destinations, the lane bar below it
carries the taxonomy — because one row stopped fitting at five lanes and would only get worse.

## Hosting

GitHub Actions builds and deploys to GitHub Pages on every push to `main`
(`.github/workflows/deploy.yml`). Settings → Pages → Source must be set to **GitHub Actions**.
DNS: a `CNAME` record for host `machinespeed` pointing at `<your-username>.github.io`.
