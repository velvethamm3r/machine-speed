# Forecasts

The board reports; it does not forecast. `/forecasts/` is the one page where the
analyst does, and it is kept apart from the board so a forecast can never be
read as a sourced item. The page and its nav link appear only once
`forecasts.json` holds at least one forecast.

| File | Written by | Purpose |
|---|---|---|
| `forecasts.json` | Daria, by hand | The forecasts and their resolutions. A daily run never touches it. |
| `forecasts.lock.json` | The GitHub Action | Integrity ledger. Never edit it by hand, never upload it. |
| `forecasts.starter.json` | — | Candidate questions with no probabilities. The build ignores it. |
| `forecasts.py` | — | Validation, locking, scoring and the page. |

## Adding a forecast

Add an entry to `forecasts.forecasts` in `forecasts.json`, set `made` to today,
and upload the file. The deploy logs it in the lock that day.

```jsonc
{
  "id":        "caisi-second-cyber-eval-2026",  // required, unique, kebab-case
  "made":      "2026-09-29",                     // required. The day you add it — see "Backdating"
  "question":  "Will CAISI publish …?",          // required
  "p":         0.35,                             // required. 0.01–0.99
  "resolveBy": "2026-12-31",                     // required for judgment forecasts
  "criteria":  "Resolves YES if …",              // required. Precise enough that a stranger would resolve it the same way
  "lane":      "pol",                            // optional. Colours the card
  "rationale": "…",                              // optional. Shown under the question
  "items":     ["board-item-id"],                // optional. Board items that prompted it
  "supersedes": "older-forecast-id"              // optional. See "Changing your mind"
}
```

**Board forecasts** are about the board's own counts and resolve themselves.
Add `"kind": "board"` and a `metric` instead of `resolveBy`:

```jsonc
"kind": "board",
"metric": { "lane": "atk", "from": "2026-10-01", "to": "2026-12-31", "atLeast": 125 }
```

`metric.from` must be after `made`. The build counts items in that lane dated inside the
window **seven days after it closes** (so late-arriving items are counted), then freezes
the answer in the lock. Each board forecast also gets a **trend baseline** when it is
logged: the probability the lane's last eight weeks of weekly counts alone (Poisson)
would give, using only items the board had logged by `made`. The page scores you against
it. Counts measure what the board tracked, and the board's coverage has grown since July,
so the baseline leans low when coverage is still expanding.

## Resolving a judgment forecast

Append to `forecasts.resolutions`:

```jsonc
{ "id": "caisi-second-cyber-eval-2026", "outcome": "yes", "date": "2026-11-14",
  "source": { "url": "https://…", "outlet": "NIST / CAISI" } }
```

`outcome` is `yes`, `no` or `void`. Yes and no need a source under the board's sourcing
rules; `void` (the question stopped making sense) needs a `note` instead and is not
scored. Board forecasts cannot be resolved by hand except as `void`. The build warns
about any judgment forecast past its `resolveBy` date with no resolution.

## What the build refuses

A build that fails here does not deploy, and the live site keeps its last good version.

- **Editing a logged forecast or resolution.** Every entry is fingerprinted when first
  logged. Change any field — including a typo fix — and the build stops.
- **Deleting a logged forecast.** A call that went badly stays on the record.
- **Backdating.** In the GitHub Action, a new forecast whose `made` is more than two days
  before the day it is first logged is refused. Upload forecasts the day you make them.
- `p` of 0 or 1, a board window that has already started, a resolution for an id that
  does not exist, a yes/no resolution without a source.

## Changing your mind

Add a new forecast with `"supersedes": "<old id>"` and the new probability. Both stay on
the page, linked to each other, and both are scored — that is how the record shows you
updated rather than rewrote.

## Scoring

Brier score: (p − outcome)², outcome 1 or 0, averaged over resolved forecasts. 0 is
perfect, 0.25 is what always answering 50% earns. The page also shows a calibration table
and, for board forecasts, your Brier score next to the baseline's on the same questions.

## The lock

Only the GitHub Action writes `forecasts.lock.json`, and it commits it along with the
archive snapshot. A local build — a daily run, a preview — holds lock changes in memory
and leaves the file alone. So the committed lock only ever records what the published
site saw, on the day it saw it, and git history records the same thing independently.
