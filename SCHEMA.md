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
  "briefs":    [ /* see below */ ],                // optional. Omit it and every brief page disappears.
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
  "confidence": "on-record",            // required. See tiers below.
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

The tier describes **the kind of claim, not the identity of the publisher**. The same company
on the same blog can land in two different tiers depending on what it is asserting, and reading
these as a list of publisher types is the mistake that produces a misfiled item.

`confirmed` — the organisation that was affected says it happened to them. `claimed` — the
attacker says they did it, and nobody else has stood behind it. `researchers` — security
researchers reported it and the victim has not confirmed. `press` — established press reported
it and no primary source is available.

`on-record` and `self-reported` are the pair that gets confused, and the line between them is
whether the announcement *constitutes* the fact or merely *asserts* one.

`on-record` is for statements the speaker has formally put in its own name, where it is the only
possible authority and the statement itself is the event: a bill is introduced, a rule takes
effect, an agency issues an alert, a lab discloses that its own model did something. Nobody else
could report these, and they generally cut against the speaker's interest — an organisation
saying something costly about itself is not a claim anyone needs to reproduce.

`self-reported` is for testable claims where the party doing the measuring is the party being
measured, and no independent party has checked. Benchmark scores, head-to-head comparisons,
capability assertions, launches written to read as findings. The label exists so these appear on
the board flagged rather than endorsed. It is not a demotion, it is not about having something to
sell, and it applies to a university lab or a government agency publishing numbers on its own
tooling exactly as it applies to a company.

So a lab saying "our evaluation model escaped its sandbox" is `on-record`. The same lab saying
"our model scores 92% on a cyber benchmark" is `self-reported`. Same speaker, same post,
different tier — because the first is a disclosure only they can make and the second is a
measurement anyone could check and nobody has.

When an item mixes the two — a first-party announcement that carries a competitive benchmark
inside it — the tier follows whatever the item's `core` actually leans on. If the sentence a
reader takes away is the score, it is `self-reported`.

These two were called `official` and `vendor` until 2026-08-06. Both names described who was
speaking rather than what was being claimed, which is the distinction the tiers exist to draw,
and both smuggled in a verdict: `official` conferred the authority of a public record on a lab's
own announcement, and `vendor` read as a judgement about commerce. Snapshots in `archive/`
predating the rename still carry the old values, and the retired `.c-official` / `.c-vendor`
rules are kept in `assets/style.css` so those pages keep rendering as written.

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

Watchlist threads persist. When nothing moved, carry the entry forward with its old `changed`
date rather than deleting it — the point of the panel is that it survives quiet days.

The word "thread" here means a running storyline the board keeps an eye on, and it is
unrelated to `briefs[]` below. The two were easy to confuse while the brief pages were also
called threads, which is part of why they are not any more.

## briefs[]

A lane card answers "what happened today". A brief answers "how did this thing unfold" —
one incident laid out in dated stages, each stage carrying its own sources and its own
confidence label, so a reader can tell what the affected organisation confirmed on day one
from what the press reconstructed a week later.

```jsonc
{
  "slug":    "openai-hugging-face-eval-breach",  // required, unique, kebab-case. Becomes /brief/<slug>/.
  "title":   "…",                                // required. One line.
  "summary": "…",                                // required. 1–2 sentences; also the page description and the card blurb.
  "lane":    "atk",                              // optional. Colours the card and the timeline rail. Same values as items[].
  "status":  "Active",                           // optional. Free text — "Active", "Resolved", "Dormant".
  "opened":  "2026-07-09",                       // optional. First stage date, stated rather than derived.
  "updated": "2026-08-05",                       // optional. Sorts the index, newest first.
  "acts":    [ /* see below */ ],                // optional. The panel layout. Omit for a plain timeline.
  "stages":  [ /* see below */ ]                 // required. At least one.
}
```

This key was called `dossiers` until 2026-08-06, and the pages it produced were called
threads. Nothing inside an entry changed in the rename. `validate()` hard-errors if the old
key is still present rather than building a site with every brief silently missing.

### stages[]

```jsonc
{
  "date":       "2026-07-16",           // required. YYYY-MM-DD. Cannot be later than updatedISO.
  "act":        "containment",          // required *if* the brief has acts[]; forbidden-in-practice otherwise (ignored).
  "label":      "Hugging Face discloses",  // required. Short title for the stage.
  "what":       "…",                    // required. What happened, factually.
  "confidence": "confirmed",            // optional. Same tiers as items[]. Per stage, not per brief.
  "sources":    [ {"url": "https://…", "outlet": "…"} ],  // required. At least one, https only, opened.
  "disputed":   "…",                    // optional. Prints as "Contested:" — a figure the sources disagree about.
  "note":       "…"                     // optional. Prints as "Note:" — a scope limit; what the source does not say.
}
```

Stages render in date order. `disputed` and `note` are deliberately separate: `disputed`
is for a number two sources give differently, where picking one quietly is the failure the
sourcing rules exist to prevent; `note` is for what a source does *not* claim, which matters
most where a stage sits next to another one it is easily read as explaining.

`validate()` holds briefs to the same standard as items — every stage needs at least one
`https://` source with an outlet, no stage may be dated in the future, slugs must be unique
and kebab-case, and an unknown lane or confidence value is a hard error. Omit the whole key
and the build is byte-identical to one from before the feature existed: no Briefs nav link,
no index page, no board rail, no sitemap entries.

### acts[]

Optional. Without it a brief renders as one timeline, twelve stages deep, which is accurate
and hard to read: everything looks equally important and the reader has to hold the shape in
their head. `acts[]` groups the same stages into numbered panels — what happened, how it was
contained, how the market reacted, what each company said — and lets two panels sit side by
side when they are two answers to one question rather than two consecutive beats.

```jsonc
{
  "id":       "containment",            // required, unique within the brief, kebab-case.
  "kind":     "Containment & disclosure",  // optional. Small label above the headline. Defaults to the lane name.
  "lane":     "atk",                    // optional. Colours the panel. Defaults to the brief's lane.
  "when":     "Jul 16 – 29",            // optional. Free text, right-aligned in the panel header. Not parsed.
  "row":      3,                        // optional. Acts sharing a row sit side by side. Max 2 (ACT_ROW_MAX).
  "headline": "…",                      // required. One sentence naming what this stretch of time amounts to.
  "note":     "…",                      // optional. Prints as "Note:" above the bullets — a scope limit on the panel.
  "items":    ["ai-kill-switch-act"]    // optional. Board item ids folded in as extra bullets.
}
```

**An act carries no facts of its own.** Every bullet in a panel is either one of the brief's
own stages or an existing `items[]` entry folded in by id, rendered with its own wording, its
own confidence label and its own source link. That is the property that makes the layout safe
to rearrange: you can add an act, merge two, or delete `acts[]` entirely and no sourced claim
moves. The one thing an act does assert is its `headline`, which is a summary of the bullets
underneath it — so a headline must not introduce a fact that no bullet supports. If you want
to say something the sources do not, the answer is a new stage with a source, not a headline.

Numbering is derived, never written down: panels are numbered by row in the order they appear,
and two acts sharing a row become 3A and 3B. Stages and folded items interleave by date inside
a panel rather than sitting in two blocks, and a folded item is marked with a hollow bullet
and a link back to the lane page it was filed on.

`validate()` refuses the silent failures specifically: an act id that repeats, a stage
pointing at an act that does not exist, a stage with no `act` at all in a brief that has
`acts[]` (it would vanish from the page), more than two acts on one row, and a folded item id
that is not in `items[]`. An act with neither stages nor items is a warning, not an error —
its headline would be standing on nothing.

`row` is a grouping key, not a position: the value itself is arbitrary, only sameness matters,
and rows render in the order their first act appears in `acts[]`.

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
