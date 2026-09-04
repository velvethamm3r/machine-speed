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
3. **Build on the run before, and do not roll anything off.** The board is not rebuilt from
   scratch each day. It carries every previous item forward and adds what is genuinely new.
   **The board has been in grow mode since 2026-08-05:** `coverageStart` is pinned at
   `2026-07-01` and nothing ages off the live board. Guarantee 3 below has the detail and
   the alternative; the one thing a run must not do is quietly start rolling.

---

## Guarantee 1 — do not break the layout

The site is fully generated. `build.py` reads `data.json` and pre-renders every page,
the RSS feed and the newsletter draft. The design lives in `assets/style.css`,
`assets/theme.js`, `assets/icon.svg`, `assets/board.css` and `assets/board.js`, and the
HTML structure lives in `build.py`. **A daily run touches none of these.** Correct data
in, correct layout out.

Since the 2026-09 redesign the bare domain answers with the **Explore** view — an interactive,
filterable, searchable board rendered in the browser from data inlined into the page
(`LANDING = "explore"`). This changes nothing about what a run does: a run still edits
`data.json` and lets `build.py` render. It does mean the run's prose is now read in two places
rather than one, which is what the next section is for.

Concretely:

- **Edit `data.json` only** (and append to `dashboard-memory.md`). Do not edit `build.py`,
  anything under `assets/` — including `board.css` and `board.js`, which render the
     landing page — `README.md`, `RUNBOOK.md`, `SCHEMA.md`, or any file in `dist/`.
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

### What Explore renders

`explore_payload()` in `build.py` inlines a **projection** of `data.json` into the landing page.
Per item it carries exactly nine fields — `id`, `lane`, `date`, `headline`, `core`, `confidence`,
`outlet`, `url`, and the lane page the row links back to. It also carries every watchlist entry's
`thread`, `status` and `changed`. Nothing else reaches the interactive view: `isNew`, `briefs`,
`archives`, `about`, `judgmentNote` and `internalNote` are not in the payload.

What follows for a run:

- **You do not need to sanitise or escape anything.** The payload serialiser already escapes
  every `<`, so no headline, `core` or watchlist `status` can close the script element early no
  matter what characters it contains. Write plain text as always and do not invent workarounds.
- **The lane path is generated, never authored.** Each row carries the lane page it links back
  to, taken from `LANES` in `build.py`. Those paths became directories (`capability/`, not
  `capability.html`) in the 2026-09 clean-URL change, with the flat paths kept permanently as
  redirect stubs. A run writes `lane` and nothing else; it never writes a URL for a lane page.
- **`core` is read while scanning and filtering, not only on a card.** Keep each one
  self-contained and legible out of context — no "as above", no reliance on a neighbouring item.
- **The strip is a pre-rendered concept, not an Explore one.** `isNew` is not in the payload, so
  the "New to the board" strip exists on the pre-rendered pages and in the newsletter, not in the
  interactive view. Keep setting it per Guarantee 3 — it still drives the newsletter and the
  snapshot — but do not expect it to change what Explore shows.
- **Dated snapshots are unaffected.** `BOARD_PAGE` is empty, so the full pre-rendered board is not
  published as a page, but the renderer still runs and each `archive/machine-speed-YYYY-MM-DD.html`
  is still a complete frozen copy of that markup. Guarantee 2 is intact.

### Watchlist length — rewrite, do not append

Watchlist `status` strings are inlined into the landing page and rendered in an Explore panel.
Runs had been **appending** a clause per development rather than rewriting the thread, which by
2026-09-03 had produced 46,235 characters across twenty threads — about a fifth of the whole
inlined payload. They were compressed to 20,794 characters that day.

When a thread moves: **rewrite the status so the newest development leads**, then compress what is
behind it. A status answers "where does this stand today"; it is not a changelog. The changelog is
`dashboard-memory.md`, where the full history belongs and costs nothing. Retire rather than
accumulate — a storyline that stopped moving gets an honest closing status ("Resolved", "Dormant"),
not another appended clause.

**Keep each status under about 1,200 characters and the twenty together under about 25 KB.** Those
numbers come from doing the compression rather than guessing: the threads carrying the most
material land at 1,150–1,200 without losing a load-bearing figure, and squeezing below about 900
starts costing real facts. Past 1,500 a thread needs a hard trim or a split. When material
genuinely will not compress, move the enumeration to `dashboard-memory.md` and say so in the status
("Full route-by-route list in dashboard-memory.md").

Trimming prose is **not** a thread moving: leave `changed` at the date the storyline last actually
moved, and do not restamp it because you rewrote the wording.

### Where the board stands

A dated snapshot of state, so a run knows what it is inheriting. **Live numbers always come from
`data.json`** — these are the values as of the last run and will be stale the moment one lands.

| | As of 2026-09-03 |
|---|---|
| Coverage | `2026-07-01` → `2026-09-03`, **grow mode**, `coverageStart` pinned |
| Items | 213 — cap 54 · pol 33 · def 58 · atk 54 · mkt 14 |
| Watchlist | 20 threads, 20,794 characters total |
| Briefs | 2 — `openai-hugging-face-eval-breach` (27 stages, 9 acts), `ai-assisted-water-ot-intrusions` (6 stages, no acts) |
| Archives | 22 entries, newest `2026-09-03` |
| Landing page | Explore, 272 KB, of which ~215 KB is the inlined payload |
| Social card | `assets/og.png`, 1200×630, emitted on every page as `summary_large_image` |
| Newsletter | `newsletter.techpointe.org` (Substack, custom domain, live 2026-09-03) — same-tab link |
| Analytics | Cloudflare Web Analytics beacon on all 22 live pages; a floor, not a count |

Standing context worth carrying into a run: Markets is the thinnest lane and moved for the first
time in three runs on 2026-09-03. The open-weight question — whether GLM-5.3's weights shipped and
whether its safety review concluded — has been unresolved for four runs because no Z.ai primary can
be opened. cisa.gov, nvd.nist.gov and cve.org are unreachable to automated fetchers, so CVEs are
carried as their primaries state them. Check Point post bodies and the Google Cloud/Mandiant blog
could not be opened on 2026-09-03 and are unverified rather than quiet for that window.

### Standing note — landing-page weight (decide later, not on a daily run)

Because the payload is inlined, every item a run adds also adds to the landing page's download.
Measured 2026-09-03 at 213 items: 272 KB page, ~215 KB payload, about 1.0 KB per item — of which
`core` is the largest term. In grow mode at twenty to thirty items a day this grows by roughly
25–35 KB a day without limit.

Two levers exist and **both are design tasks, not daily-run decisions**: tighten the projection
further (dropping or truncating `core`, letting the lane pages carry the full text), or cap the
window so items age off. The watchlist discipline above is the one part a run controls directly.
Record the numbers in `dashboard-memory.md` if they move sharply; otherwise leave this alone.

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

## Guarantee 3 — carry everything forward, built on the last run

The board states the exact span of days it covers (`coverageStart` … `coverageEnd` in
`data.json`) and covers every item inside that span — in Explore through filtering and search,
and on the lane and week pages as pre-rendered cards.

> ### ⚠ The board is in GROW mode. Do not roll items off.
>
> `coverageStart` has been pinned at **`2026-07-01`** since 2026-08-05 and every run since has
> operated this way — twelve archive entries say "grow mode" in their own note. **A run advances
> `coverageEnd` only.** It never advances `coverageStart` and never deletes an item for being old.
>
> This matters because the original design was a rolling five-week window, and the instructions
> below used to lead with it. If a run applied that rule on 2026-09-04 it would set
> `coverageStart` to 2026-07-27 and **delete 47 of the board's 213 items** — 22% of it, across
> all five lanes, with only 6 protected by brief folding. That is a silent, hard-to-notice
> amputation, which is why grow mode is now stated first and in a box.

Each run does four things, in this order of care:

1. **Build on the previous run.** Start from the existing `data.json`. Read `dashboard-memory.md`
   first: anything already listed there is *not* "new today." Carry every in-window item forward
   unchanged unless you have a sourced correction. Do not re-add or re-describe something already
   on the board.

2. **Extend the window at the near end only.**
   - Set `coverageEnd` to **today**.
   - **Leave `coverageStart` at `2026-07-01`.** Do not compute a new one.

3. **Nothing rolls off.** Every item stays in `items[]`. Do not remove an item because it is old;
   the only reasons to remove one are a sourced correction or a de-duplication, and both get
   written down in `dashboard-memory.md`.

   *If the board is ever switched back to a rolling window* — Daria's call, not a run's — the
   rule was: advance `coverageStart` to the Monday on or before `today − 35 days`, then remove
   items dated before it, with two exemptions. **Never drop an item a brief folds in by id**
   (`acts[].items` or a stage referencing it); `validate()` hard-errors on a folded id missing
   from `items[]`. And **briefs sit outside the window entirely** — a brief's whole purpose is to
   reach back past the coverage period, so never trim one to fit.

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

**Switching back to a rolling window is a deliberate decision, not a run's.** The only knob is
`coverageStart`: pin it and the board grows, advance it and items roll off. The layout and archive
guarantees hold either way, and the frozen snapshots in `archive/` keep every rolled-off item
forever. But it changes what a reader sees on the live board, so confirm with Daria before
changing it mid-stream — and if it is ever changed, update this section in the same edit so the
instruction and the behaviour cannot drift apart again.

> **Legacy note — resolved 2026-09-03.** The board has had three retention rules: a rolling
> **7-day** window at launch, then a rolling **~5-week** window, and since 2026-08-05 **grow mode**.
> `RUNBOOK.md` carried the seven-day line until 2026-09-03, when it was corrected to point here;
> its "The coverage period" section already described grow mode, so that file had been
> contradicting itself. All three documents now say the same thing. If retention ever changes
> again, change it in `DAILY_RUN.md` Guarantee 3 and `RUNBOOK.md` in the same edit.

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
   **If a lab, big-tech or vendor primary is provenance-blocked (a common `PROVENANCE_REQUIRED` result in
   an unattended run), run the site-scoped search fallback in "Sourcing" before treating that source's
   lane as quiet — a blocked primary is not an empty one.**
4. **Edit `data.json`:**
   - `updatedISO` and `updatedDisplay` → now (ISO 8601 with the ET offset; display in `YYYY-MM-DD,
     h:MM AM/PM ET`).
   - `coverageEnd` → today. **Leave `coverageStart` at `2026-07-01`** — the board is in grow
     mode (Guarantee 3).
   - Add new items to `items[]`; set/clear `isNew`. **Remove nothing for being old.**
   - Update `watchlist[]` statuses and `changed` dates; carry quiet threads unchanged, and
     **rewrite rather than append** on a thread that moved (see "Watchlist length" above).
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
- **A provenance-blocked primary is not a quiet lane — run the search fallback before concluding a
  source published nothing.** In an unattended run the lab, big-tech and vendor primaries (openai.com,
  anthropic.com and the other §1–§3 sources in `SOURCES.md`) frequently return `PROVENANCE_REQUIRED`,
  because opening them needs a fetch approval no one is there to give. That block tells you nothing about
  whether the source published — so never treat "couldn't open the primary" as "the source was quiet."
  Before declaring a blocked lab or vendor's lane empty, run a **site-scoped search for its last ~48
  hours of posts** — e.g. `site:openai.com <window + lane keyword>`, or the lab's name plus the date
  window and a cyber keyword — and open whatever it surfaces (a syndicating outlet if the primary itself
  still won't open). Carry anything real on `press` with a "(via <outlet>)" attribution and flag it for a
  primary-source upgrade on a later attended run. Broad topical queries are not a substitute for this
  per-source pass: they surface aggregators and older look-alike stories and bury the day's actual post.
  (Cautionary case, 2026-08-28: OpenAI's Aug 27 collective-cyber-defense open letter sat on openai.com
  behind a provenance block; the morning pass's topical searches surfaced the older July "pace" letter
  instead and the item was missed until a tighter `site:`-scoped query found it. The letter was reachable
  the whole time — the run just never ran the per-source fallback.)
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
| `FRONT_WEEKS` | `2` | The two most recent weeks show as full cards on the pre-rendered board; older in-window weeks index one line each. Does not affect Explore, which filters the whole period. |
| `LANDING` | `"explore"` | The bare domain answers with the interactive Explore view. A run never changes this. |
| `EXPLORE_PAGE` | `"explore.html"` | Where Explore lives when it is *not* the landing page. Empty removes the feature entirely, including `board.css` / `board.js`. |
| `BOARD_PAGE` | `""` (empty) | The full pre-rendered board is not published as a page — the lane and week pages carry every item, and each dated snapshot in `archive/` is still a complete copy of that markup. |
| `GROUP_BY_WEEK` | `True` | A lane with six or more items splits under Monday–Sunday week headings. |
| `OG_IMAGE` | `"og.png"` | Social preview image, read from `assets/`. Present, and every page emits `og:image` / `twitter:image` and the card becomes `summary_large_image`; missing, and the tags are simply not emitted. A run never touches it. |
| `OG_IMAGE_W` / `OG_IMAGE_H` | `1200` / `630` | Declared dimensions. They must match the real file — platforms trust the tag, and a mismatch crops the card wrong. |
| `OG_IMAGE_ALT` | text | Alt text on the card. Describes the image, not the site. |
| `WEB_ANALYTICS_TOKEN` | set | Cloudflare Web Analytics beacon, injected before `</body>` on every generated page. The token is a public site identifier, not a secret. Empty it and the beacon and its request vanish. Redirect stubs are excluded (they would double-count their destination) and frozen snapshots already in `archive/` are never rewritten, so each keeps whatever the site carried on its own day. A run never touches this. |
| `SUBSTACK_URL` | `https://newsletter.techpointe.org` | The newsletter moved to its own subdomain on 2026-09-03. It sits in the nav's destinations group, between Briefs and Archive. |
| `SUBSTACK_NEW_TAB` | `True` | Forces the newsletter link and subscribe button to open in a new tab even though the URL is now same-site. Without it `same_site()` would keep them in the same tab, which is right for a page of this site but wrong for a subscription flow — a reader part-way down the board should not lose their place. Set `False` to let `same_site()` decide again. |
| `SHOW_RUN_SNAPSHOTS` | `False` | Snapshots are built and validated but not linked in nav. |
| `SHOW_INTERNAL_NOTE` | `False` | `internalNote` stays in the data, off the page. |
| `NOTE_PLACEMENT` | `"none"` | `judgmentNote` is kept in the data and newsletter, off the board face. |
| `SITE_MARK` | `"™"` | Common-law mark; leave as-is (`®` is only lawful once registered). |

Validation lines that most often catch a run (build stops on all of these): an item missing a
required field; a duplicate `id`; an unknown lane or confidence; a non-`https://` URL; a
future-dated item; a watchlist entry with no status; an `archives[]` entry pointing at a missing
file; **no `archives[]` entry for today**; or a lingering `dossiers` key (renamed to `briefs` on
2026-08-06). Required item fields: `id, lane, date, headline, core, confidence, outlet, url`.
