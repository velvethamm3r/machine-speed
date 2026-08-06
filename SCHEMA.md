# `data.json` — schema

One JSON object. Every page, the RSS feed and the newsletter draft render from it.
A daily run rewrites this file and nothing else.

```jsonc
{
  "updatedISO":     "2026-07-27T15:45:00-04:00",   // required. ISO 8601 with offset. Drives all date maths.
  "updatedDisplay": "2026-07-27, 3:45 PM ET",      // required. Shown in the "Last updated" stamp.
  "judgmentNote":   "…",                           // required. Every call you made by hand, in prose.
  "internalNote":   "…",                           // required. One sentence: what changed since the last run.
  "coverageStart":  "2026-07-01",                  // optional. First day the board claims to cover.
  "coverageEnd":    "2026-08-05",                  // optional. Last day. Omit either and it is derived
                                                   //   from the oldest / newest item, so the printed
                                                   //   label can never overstate what is on the board.
  "items":     [ /* see below */ ],                // required.
  "watchlist": [ /* see below */ ],                // required.
  "dossiers":  [ /* see below */ ],                // optional. Omit it and every thread page disappears.
  "archives":  [ /* see below */ ],                // required. Must contain an entry for today.
  "about":     [ "paragraph", "paragraph" ]        // paragraphs for the About page. Rarely changes.
}
```

## items[]

```jsonc
{
  "id":         "kimi-k3-joint-eval",   // required, unique, kebab-case. Stable across runs; used as the RSS guid and the #anchor.
  "lane":       "cap",                  // required. cap | pol | def | atk | mkt
  "date":       "2026-07-23",           // required. YYYY-MM-DD. Publication or event date, not the run date.
  "headline":   "…",                    // required. One line, bold on the card.
  "core":       "…",                    // required. 1–2 factual sentences. No opinion, no adjectives doing work.
  "confidence": "official",             // required. See tiers below.
  "outlet":     "UK AI Security Institute / CAISI",  // required. Who published it.
  "url":        "https://…",            // required. https only. A page you actually opened.
  "isNew":      true                    // optional. Forces into / out of the 48h strip. Omit for the date rule.
}
```

Ordering within a lane is handled by the generator (newest first) — array order does not matter.
`date` also decides which week page an item lands on: items are bucketed by the Monday of
their week, and each non-empty bucket becomes `/week/YYYY-MM-DD/`. Nothing else declares the
site's structure — change a date and the item moves pages on the next build.
Once a lane holds six or more items the generator also splits them under Monday–Sunday week
headings, clamped to `coverageStart` / `coverageEnd` so the first and last heading never claim
days outside the stated period. `date` must fall inside that period: outside is a warning,
in the future is a hard error.

### Lanes

`cap` — capability: what frontier models can now do. `pol` — policy: bills, rules, agency
action. `def` — defense: tooling, guidance and mitigations. `atk` — attacks: incidents and
intrusions. `mkt` — markets: how the money prices the risk, meaning cyber insurance,
underwriting, liability and the capital response.

The lane set lives in `LANES` in `build.py` and nothing else hardcodes its size — the stats
grid reflows, the lane bar generates itself, and prose that counts lanes derives the number.
Adding a sixth lane is a `LANES` entry, two CSS custom properties (`--x` and `--x-soft` in
both themes) and one `.lp-x` pill rule.

### Confidence tiers

`confirmed` means the affected organisation confirmed it. `claimed` means the attacker claims
it. `researchers` means security researchers reported it and the victim has not confirmed.
`press` means established press reported it with no primary source. `official` is a first-party
announcement — a government body, a lab, a bill sponsor. `vendor` is a vendor claim, typically
an unreproduced benchmark score, shown so it is flagged rather than endorsed.

Each tier needs a label in `CONF`, a colour in `CONF_VAR` (both in `build.py`) and a
`.c-<tier>` rule in `assets/style.css`.

## watchlist[]

```jsonc
{
  "thread":  "Tracked bills",   // required. Short, stable label — the same thread keeps the same name across runs.
  "status":  "…",               // required. Current state in one or two sentences.
  "changed": "2026-07-23"       // YYYY-MM-DD, or "" if it has never moved. Rendered as "—" when empty.
}
```

Threads persist. When nothing moved, carry the entry forward with its old `changed` date
rather than deleting it — the point of the panel is that it survives quiet days.

## dossiers[]

A lane card answers "what happened today". A dossier answers "how did this thing unfold" —
one incident laid out in dated stages, each stage carrying its own sources and its own
confidence label, so a reader can tell what the affected organisation confirmed on day one
from what the press reconstructed a week later.

```jsonc
{
  "slug":    "openai-hugging-face-eval-breach",  // required, unique, kebab-case. Becomes /thread/<slug>/.
  "title":   "…",                                // required. One line.
  "summary": "…",                                // required. 1–2 sentences; also the page description and the card blurb.
  "lane":    "atk",                              // optional. Colours the card and the timeline rail. Same values as items[].
  "status":  "Active",                           // optional. Free text — "Active", "Resolved", "Dormant".
  "opened":  "2026-07-09",                       // optional. First stage date, stated rather than derived.
  "updated": "2026-07-29",                       // optional. Sorts the index, newest first.
  "stages":  [ /* see below */ ]                 // required. At least one.
}
```

### stages[]

```jsonc
{
  "date":       "2026-07-16",           // required. YYYY-MM-DD. Cannot be later than updatedISO.
  "label":      "Hugging Face discloses",  // required. Short title for the stage.
  "what":       "…",                    // required. What happened, factually.
  "confidence": "confirmed",            // optional. Same tiers as items[]. Per stage, not per dossier.
  "sources":    [ {"url": "https://…", "outlet": "…"} ],  // required. At least one, https only, opened.
  "disputed":   "…",                    // optional. Prints as "Contested:" — a figure the sources disagree about.
  "note":       "…"                     // optional. Prints as "Note:" — a scope limit; what the source does not say.
}
```

Stages render in date order. `disputed` and `note` are deliberately separate: `disputed`
is for a number two sources give differently, where picking one quietly is the failure the
sourcing rules exist to prevent; `note` is for what a source does *not* claim, which matters
most where a stage sits next to another one it is easily read as explaining.

`validate()` holds dossiers to the same standard as items — every stage needs at least one
`https://` source with an outlet, no stage may be dated in the future, slugs must be unique
and kebab-case, and an unknown lane or confidence value is a hard error. Omit the whole key
and the build is byte-identical to one from before the feature existed: no Threads nav link,
no index page, no board rail, no sitemap entries.

## archives[]

```jsonc
{
  "date":  "2026-07-27",                              // required. Newest first.
  "file":  "archive/machine-speed-2026-07-27.html",   // required. Path relative to the repo root.
  "items": 16,                                        // item count in that snapshot.
  "note":  "…"                                        // one-line description of the day.
}
```

`build.py` fails the build if there is no entry for today, and also fails if an entry points at
a file that isn't in the repo — that combination is the cheapest guard against both a run that
forgets to snapshot itself and an archive page full of 404s.

## How the pieces connect

`data.json` is read by `build.py`, which pre-renders every page into `dist/` — all content is
in the HTML itself, so search engines, RSS readers, link previews, screen readers and no-JS
browsers see the full board. The only client-side JavaScript is the theme toggle in
`assets/theme.js`. `archive/` and `newsletter/` are written back into the repo (not `dist/`)
so history and drafts survive every rebuild. Nothing loads from a CDN.
