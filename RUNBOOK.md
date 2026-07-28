# Machine Speed — daily run runbook

Everything the site shows comes from one file. A run edits `data.json`, commits, and
GitHub Actions does the rest. Live at **https://machinespeed.techpointe.org**.

## The 5-minute version

1. Check the clock: `date "+%Y-%m-%d"` and `TZ=America/New_York date "+%H:%M"`. Never trust a cached date.
2. Read `dashboard-memory.md`. Anything already listed there is not "new today."
3. Research the four lanes for the last 7 days. Verify every item against a source you actually opened.
4. Edit `data.json` — the only file a normal run touches. Schema is in `SCHEMA.md`.
5. Run `python3 build.py`. It validates first and refuses to write if the data is broken.
6. Append this run to `dashboard-memory.md` and update the watchlist there.
7. Commit and push `data.json`, `archive/`, `newsletter/` and `dashboard-memory.md`. The site rebuilds and deploys in about a minute.

Prefer a human checkpoint? Push the run to a branch and open a pull request instead of
committing to `main`. The workflow builds and validates the PR automatically (green check =
data is well-formed; no deploy happens). Review the diff — headlines, notes, the newsletter
draft — then merge, and only the merge publishes. This is the recommended shape for the
morning review: the run prepares everything overnight, a human approves with one tap.

Preview before committing: `python3 -m http.server -d dist 8000` → http://localhost:8000

## What build.py produces

| Output | What it is |
|---|---|
| `dist/` | The whole pre-rendered site. Generated — never edit, never commit (it's in `.gitignore`). |
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
