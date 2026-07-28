# `data.json` — schema

One JSON object. Every page, the RSS feed and the newsletter draft render from it.
A daily run rewrites this file and nothing else.

```jsonc
{
  "updatedISO":     "2026-07-27T15:45:00-04:00",   // required. ISO 8601 with offset. Drives all date maths.
  "updatedDisplay": "2026-07-27, 3:45 PM ET",      // required. Shown in the "Last updated" stamp.
  "judgmentNote":   "…",                           // required. Every call you made by hand, in prose.
  "internalNote":   "…",                           // required. One sentence: what changed since the last run.
  "items":     [ /* see below */ ],                // required.
  "watchlist": [ /* see below */ ],                // required.
  "archives":  [ /* see below */ ],                // required. Must contain an entry for today.
  "about":     [ "paragraph", "paragraph" ]        // paragraphs for the About page. Rarely changes.
}
```

## items[]

```jsonc
{
  "id":         "kimi-k3-joint-eval",   // required, unique, kebab-case. Stable across runs; used as the RSS guid and the #anchor.
  "lane":       "cap",                  // required. cap | pol | def | atk
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
