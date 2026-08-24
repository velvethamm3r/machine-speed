# Machine Speed — DAILY_RUN

**This file is the authoritative instruction for a daily run.** Read it end to end
before touching anything. It sits on top of four references and does not replace them:

- `RUNBOOK.md` — how the build works, what it validates, every config knob.
- `SCHEMA.md` — the exact shape of every field in `data.json`.
- `dashboard-memory.md` — what has already been shown, and the running watchlist.
- `SOURCES.md` — the scan list: the labs, big-tech security arms, cyber vendors, open-weight
  developers, research institutions and government/advisory channels each run sweeps.

A run reads those three, edits **one data file**, rebuilds, and hands the changed
files back to a human. It never publishes and never pushes. Live board:
**https://machinespeed.techpointe.org**.

---

## The three guarantees this run must keep

Everything below expands on these. If a step ever seems to conflict with one of them,
stop and keep the guarantee.

1. **Do not break the layout, formatting or presentation.** The only file a run edits
   for content is `data.json` (plus an append to `dashboard-memory.md`). The look of the
   site is generated from that data by `build.py` and the shared files in `assets/`. Leave
   the generator and the assets alone and the presentation cannot drift.
2. **Preserve the archive.** Every past dated snapshot in `archive/` is a frozen record of
   what the board said on that day. A run only ever **adds** to `archive/`; it never edits
   or deletes a file that is already there.
3. **Keep the alerts on a rolling "last month or so" window, building on the run before.**
   The board is not rebuilt from scratch each day and it is not allowed to grow without
   limit. It carries the previous run's items forward, adds what is genuinely new, and lets
   items older than roughly five weeks roll off the live board — while their frozen
   snapshots keep them forever.

---

## Guarantee 1 — do not break the layout

The site is fully generated. `build.py` reads `data.json` and pre-renders every page,
the RSS feed and the newsletter draft. The design lives in `assets/style.css`,
`assets/theme.js` and `assets/icon.svg`, and the HTML structure lives in `build.py`.
**A daily run touches none of these.** Correct data in, correct layout out.

Concretely:

- **Edit `data.json` only** (and append to `dashboard-memory.md`). Do not edit `build.py`,
  anything under `assets/`, `README.md`, `RUNBOOK.md`, `SCHEMA.md`, or any file in `dist/`.
- **Do not hand-edit anything in `dist/`.** It is generated and git-ignored; edits there are
  overwritten on the next build and never committed.
- **Let the build be the gate.** `python3 build.py` validates first and, on any error, writes
  nothing and exits non-zero — the live site keeps serving the last good deploy. A run is only
  finished when the build exits 0. Read the one-line summary it prints (`N items … in the 48h
  strip … watchlist threads`) and confirm the counts match what you intended.
- **Respect the fields that drive presentation.** Confidence must be one of the known tiers
  (`on-record`, `self-reported`, `confirmed`, `claimed`, `researchers`, `press`); lane must be
  one of `cap | pol | def | atk | mkt`. An unknown value is a hard error, not a silent
  mis-render. New tiers or lanes are a design change, not a daily run (see RUNBOOK →
  "Changing the design"), so do not introduce one to fit an awkward item — pick the closest
  existing tier and note the call.
- **Do not restyle by smuggling markup into text.** Headlines and `core` are plain text. Do
  not add HTML, emoji, or ASCII decoration to make something stand out; the card styling is the
  generator's job.
- **Preview if in doubt.** `python3 -m http.server -d dist 8000` → http://localhost:8000 shows
  the built board before anything leaves the workspace.

If the presentation genuinely needs to change, that is a separate, deliberate task against
`build.py`/`assets/` with its own review — never a side effect of a daily run.

---

## Guarantee 2 — preserve the archive

Two different things both get called "archive"; keep them straight.

- **Frozen dated snapshots** — `archive/machine-speed-YYYY-MM-DD.html`. One per run day, a copy
  of the board exactly as it read that day. **These are permanent and never change.** A run adds
  today's snapshot (the build writes it) and never rewrites or removes an existing one.
- **Live week pages** — `/week/YYYY-MM-DD/`. Regenerated from `data.json` on every build, so they
  always reflect the current items. These track the rolling window and will shrink as items roll
  off; that is expected. The permanent record of a rolled-off item is its dated snapshot, not its
  week page.

The run's obligations, which the build enforces:

- Add exactly one new entry at the **top** of `archives[]` for today: `date` (today), `file`
  (`archive/machine-speed-YYYY-MM-DD.html`), `items` (the new total), and a one-line `note`.
- `build.py` **fails the build** if there is no `archives[]` entry for today, and also fails if any
  entry points at a file that is not in the repo (today's is exempt because the build itself
  writes it). So a run cannot forget to snapshot itself and cannot leave a dangling link.
- Never delete or edit older `archive/*.html`, and never remove their `archives[]` entries.
- When you deliver the run, the new `archive/machine-speed-YYYY-MM-DD.html` is one of the files
  Daria uploads. It must go into `archive/` alongside the others — never replacing one.

`SHOW_RUN_SNAPSHOTS` is `False`, so the snapshots are not linked from the site's navigation. They
are still built, still committed, still reachable by URL, and still validated — deliberately kept
as a provenance trail rather than a second front door. Leave that setting as it is.

---

## Guarantee 3 — a rolling "last month or so" of alerts, built on the last run

The board states the exact span of days it covers (`coverageStart` … `coverageEnd` in
`data.json`) and shows every item inside that span on one page. The intent is that the span stays
at **roughly the last five weeks** — "the last month or so" — so the board is always a current
picture, not an ever-growing scroll and not a blank slate.

Each run does four things, in this order of care:

1. **Build on the previous run.** Start from the existing `data.json`. Read `dashboard-memory.md`
   first: anything already listed there is *not* "new today." Carry every in-window item forward
   unchanged unless you have a sourced correction. Do not re-add or re-describe something already
   on the board.

2. **Advance the window.**
   - Set `coverageEnd` to **today**.
   - Advance `coverageStart` so the span is about five weeks: use the **Monday on or before
     `today − 35 days`**. Anchoring to a Monday keeps the week headings clean (items are bucketed
     by the Monday of their week).
   - This is the one change from a naive "just add items" run: the window *moves*, it does not
     only grow.

3. **Roll off what aged out — but preserve it.** Remove from `items[]` any item now dated before
   the new `coverageStart`. Those items do not disappear from history: their **frozen snapshots**
   in `archive/` still show them. Two exemptions:
   - **Never drop an item that a brief folds in by id** (`acts[].items` or a stage referencing it).
     `validate()` hard-errors on a folded id that is not in `items[]`. If an aged-out item is
     referenced by a live brief, keep it in `items[]`.
   - **Briefs are outside the window entirely.** A brief's whole purpose is to reach back past the
     coverage period, so never trim a brief or its stages to fit the window.

4. **Refresh and carry the alert layer.**
   - **The "New to the board" strip** is the top-of-board alert. (It was headed "New in the last
     48 hours" until 2026-08-10; the label was changed because the strip is really "what this run
     added," and forcing days-old-but-new items under a "48 hours" banner was inaccurate.) Items
     dated within `NEW_WINDOW_DAYS` (2) of today land in it automatically; **set `isNew: true` on
     everything this run adds** so the run's additions all surface here, and set `isNew: false` to
     hold an item out. The strip is capped at `STRIP_MAX` (6) — if more than six qualify, only the
     newest six show and the build warns, so on a heavy run keep `isNew` to the six that matter
     most. On a genuinely quiet day nothing qualifies, and an empty strip ("Nothing new to report")
     is the correct, honest outcome — do not manufacture one. **Clear the previous run's `isNew`
     flags** so the strip reflects *this* run only.
   - **The watchlist** (`watchlist[]`, "Still watching") is the slower alert layer and it persists.
     Carry every thread forward. When a thread moved, update its `status` and set `changed` to the
     date it moved; when it did not move, leave it and its old `changed` date exactly as they are —
     the panel's value is that it survives quiet days. Open a new thread when a genuinely new
     running storyline appears; retire one by setting an honest `status` ("Resolved", "Dormant"),
     never by deleting it.

**If you would rather the board keep everything and grow instead of rolling** — one continuous
period with nothing ever leaving the live board — the switch is: leave `coverageStart` fixed and
skip step 3. Everything else is identical. That is the only knob; the layout and archive guarantees
are unaffected either way. (The board ran this way from 2026-08-05 to 2026-08-06.) Confirm with
Daria which behaviour she wants before changing it mid-stream, because it changes what rolls off the
live board.

> **Legacy note.** `RUNBOOK.md` still contains a line from the board's original design that says to
> "delete items now older than seven days." That was the old rolling-**7-day** window and is
> superseded by this rolling **~5-week** window. Follow this file. (Worth reconciling that line in
> `RUNBOOK.md` in a separate docs edit so the two cannot be read against each other.)

---

## The procedure, step by step

1. **Clock.** `date "+%Y-%m-%d"` and `TZ=America/New_York date "+%Y-%m-%d %H:%M"`. Never trust a
   cached or context-supplied date — a wrong run date fails the build's own checks.
2. **Read** `dashboard-memory.md`, then `RUNBOOK.md` and `SCHEMA.md`. Note the current
   `coverageStart` / `coverageEnd` and what is already shown.
3. **Research the five lanes** — `cap`, `pol`, `def`, `atk`, `mkt` — for everything since the last
   `coverageEnd`, plus anything new-to-the-board that still falls inside the new window. Work from
   `SOURCES.md`, the canonical scan list, as the **floor, not the ceiling** — sweep every source on
   it and follow any lead it hands you past its edge. Open and read every source; see "Sourcing" below.
4. **Edit `data.json`:**
   - `updatedISO` and `updatedDisplay` → now (ISO 8601 with the ET offset; display in `YYYY-MM-DD,
     h:MM AM/PM ET`).
   - `coverageEnd` → today; advance `coverageStart` per Guarantee 3 (or leave it, if running in
     grow mode).
   - Add new items to `items[]`; remove items now before `coverageStart` (respecting the two
     exemptions); set/clear `isNew`.
   - Update `watchlist[]` statuses and `changed` dates; carry quiet threads unchanged.
   - Rewrite `judgmentNote` (every call you made by hand — corrections, unverifiable details
     dropped, thin or empty lanes, why an item was omitted) and `internalNote` (one sentence: what
     changed since the last run).
   - Prepend today's `archives[]` entry.
   - Touch `about` only if it is actually wrong; it rarely changes.
5. **Build.** `python3 build.py`. It must exit 0. Read the summary line and the warnings. Expected,
   harmless warnings: "nothing qualifies for the strip" on a quiet day. Investigate any item-age or
   coverage warning — with the window advanced correctly there should be none.
6. **Append to `dashboard-memory.md`:** a dated run section listing what was added, what was
   deduped or omitted and why, what rolled off, and every hand call; then re-sync the watchlist
   section to match `data.json`. Prune shown-item log entries older than ~5–6 weeks.
7. **Deliver** (below). Do not commit, push, open a PR, post, email or schedule anything.

---

## Sourcing — the rules no script can enforce

These matter more than volume. **Fewer real items beats more shaky ones. Never pad a lane; an empty
lane is a fine outcome.**

`SOURCES.md` is the scan list these rules apply to — the frontier labs, big-tech security arms,
cyber and AI-security vendors, open-weight developers, universities and think tanks, and the
government and joint-advisory channels. It is a research checklist, not something the build reads;
treat it as the floor and add to it whenever a new source proves worth keeping.

- Every item needs a real source URL **you actually opened and read**. If you could not open it,
  either find one you can or omit the item.
- **Emphasise primary sources.** Cite the party that produced the finding — the lab's own report,
  the agency's own page, the vendor's own advisory — not an outlet reporting on it, whenever the
  primary can be opened. Press is a fallback for when the primary genuinely cannot be reached, not
  the default. If a run had to carry an item on press because a primary was unreachable (it happens
  in unattended runs, where a fetch can't be approved), note it, and **on a later run re-open the
  primary and upgrade the item** — swap the URL to the primary, set the outlet to the originator,
  and set confidence from the claim's shape. When you upgrade, re-check the primary's own date and
  figures against the press ones; they sometimes differ, and the primary wins.
- **Never invent or guess a CVE number, statistic, date, quote or attribution.** If a detail cannot
  be verified, drop the detail — not the caveat. (Example from 2026-08-10: a CVE the primary claimed
  was omitted because it was not yet in CVE.org/NVD; only the fact of the flaw was stated.)
- When a figure appears in press but not in the primary, use the primary and note the discrepancy in
  `judgmentNote`.
- If only press could be opened for a first-party claim, carry it at `press` confidence with a
  "… (via <outlet>)" attribution rather than asserting it as on-record. This is the established
  convention on this board.
- **Confidence is about the shape of the claim, not the publisher.** A testable claim measured by the
  party being measured is `self-reported`; a disclosure only the speaker could make, that costs them
  something, is `on-record`. Read the exact tier definitions in `SCHEMA.md`/`RUNBOOK.md` and apply the
  Markets-lane rule (carrier/broker marketing is `self-reported` unless a regulator, court or loss
  report says otherwise).
- **Research and display only.** Report what happened. Do not recommend, advocate or forecast, on the
  board or in the notes.
- De-duplicate hard: the same event arriving from three lanes is one item, filed once. Record the call
  in the notes and in `dashboard-memory.md`.

---

## Deliver — never publish, never push

The newsletter and the site are both **draft-only from a run's point of view.** A human reviews and
publishes; automation does not.

- **Do not** `git commit`, `git push`, open a pull request, post to Substack, send email, or create a
  scheduled task. The `newsletter/machine-speed-YYYY-MM-DD.md` the build writes is an **unpublished
  draft**; everything below its `CUT HERE` line is working notes to be rewritten or deleted by the
  human before any post — never published as-is.
- **Hand back four files** and say plainly where each goes:
  1. `data.json` → repo **root** (replaces the existing one).
  2. `dashboard-memory.md` → repo **root** (replaces the existing one).
  3. `archive/machine-speed-YYYY-MM-DD.html` → **`archive/`** (new file, added alongside the others —
     never replacing one).
  4. `newsletter/machine-speed-YYYY-MM-DD.md` → **`newsletter/`** (new file; unpublished draft).
- Close with **one sentence on what changed since the previous run**, and name anything notable you
  omitted or held.
- If the research turned up nothing worth adding, **say so and deliver nothing** rather than
  manufacturing a thin day. On such a day it is still fine to advance the window and re-snapshot if a
  human asks; absent that, silence is the honest result.

Uploading those files to `main` is what triggers GitHub Actions to rebuild and deploy (about a
minute). That upload is a human step, on purpose.

---

## Quick reference — the values a run relies on (all set in `build.py`; do not change in a run)

| Constant | Value | Meaning for a run |
|---|---|---|
| `NEW_WINDOW_DAYS` | `2` | Items this recent auto-enter the "New to the board" strip; `isNew` overrides. |
| `STRIP_MAX` | `6` | The "New to the board" strip is capped at six; excess warns. |
| `COVERAGE_SLACK_DAYS` | `0` | The stated period must contain every item exactly, or the build warns. |
| `FRONT_WEEKS` | `2` | The two most recent weeks show as full cards; older in-window weeks index one line each. |
| `GROUP_BY_WEEK` | `True` | A lane with six or more items splits under Monday–Sunday week headings. |
| `SHOW_RUN_SNAPSHOTS` | `False` | Snapshots are built and validated but not linked in nav. |
| `SHOW_INTERNAL_NOTE` | `False` | `internalNote` stays in the data, off the page. |
| `NOTE_PLACEMENT` | `"none"` | `judgmentNote` is kept in the data and newsletter, off the board face. |
| `SITE_MARK` | `"™"` | Common-law mark; leave as-is (`®` is only lawful once registered). |

Validation lines that most often catch a run (build stops on all of these): an item missing a
required field; a duplicate `id`; an unknown lane or confidence; a non-`https://` URL; a
future-dated item; a watchlist entry with no status; an `archives[]` entry pointing at a missing
file; **no `archives[]` entry for today**; or a lingering `dossiers` key (renamed to `briefs` on
2026-08-06). Required item fields: `id, lane, date, headline, core, confidence, outlet, url`.
