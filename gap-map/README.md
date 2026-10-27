# Machine Speed · Gap Map: handoff (v2, redesign)

An interactive page that measures whether defenses and policy keep pace with AI attacks and capability jumps. It is meant to live on machinespeed.techpointe.org, and the suggested path is `/gap-map/`.

## Files

| File | What it is |
|---|---|
| `gap-map.dc.html` | The page. It holds the markup, which uses inline styles, and the logic class (`class Component extends DCLogic`). |
| `support.js` | The runtime the page needs. Keep it next to the HTML. At load it pulls React 18.3.1 and Babel standalone 7.29.0 from unpkg.com, so that host must be reachable. To avoid the CDN, self-host those three files and change the URLs inside `support.js`. |
| `data/items-snapshot.json` | Offline fallback copy of `items.json` (Oct 26, 2026). |
| `data/topic-tag-suggestions.csv` | Suggested topic tags for the 76 untagged Defense and Policy items. These need editorial review before they are applied. |

## Deploy

1. Copy the folder to the site, for example to `/gap-map/`. Rename `gap-map.dc.html` to `index.html` if the server needs it. After renaming, load the page and confirm it renders. The runtime re-fetches its own URL at load, so the server must return the same HTML at `/gap-map/` and at `/gap-map/index.html`.
2. Data loading:
   - The page fetches `/data/items.json`, a same-origin path that already exists on the site.
   - If that request fails, it falls back to `./data/items-snapshot.json`.
   - The source pill under the header shows which one loaded ("Live" or "Snapshot").
3. Navigation:
   - The site nav links to `https://machinespeed.techpointe.org/gap-map/` as the current page (marked with `aria-current`). Update that link if the page lives elsewhere.
   - Add "Gap Map" to the site-wide nav if you want it reachable from other pages.
4. Fonts: the page uses Geist and Geist Mono from Google Fonts. Both are loaded in the page's `<helmet>`.
5. Head tags: canonical, Open Graph and Twitter tags point to `/gap-map/` and the site's `og.png`. Update them if the path changes.
6. Known differences from the site's shared layout. These are intentional for now, but the site agent can align them:
   - The page nav has no "AI-Cyber Intel" subtitle and no RSS link.
   - The footer has no lane links and no "Machine Speed™ · © 2026" line.
   - The site's other pages don't link to Gap Map yet.
   - If the site uses a shared layout template, swap the page's nav and footer for the shared partials and keep the content between them.

### Pre-merge checklist

- [ ] The page loads at `/gap-map/`, and the source pill says **Live** with today's item count.
- [ ] The browser console shows no errors.
- [ ] Topic rows, the chart, the response map and the popovers all work. Popover links open `/{lane}/#{id}` on the board.
- [ ] The layout reflows at 375px wide, and the control bar is not sticky there.
- [ ] Blocking `/data/items.json` (for example in DevTools) switches the pill to **Snapshot**.
- [ ] unpkg.com and fonts.googleapis.com are allowed by the site's CSP, or the React and Babel files are self-hosted (see `support.js`).

## Page structure (top to bottom)

1. **Site nav:** the same links as the live site (Board, Watchlist, Briefs, Newsletter, About), plus Gap Map.
2. **Header:** title, intro, and a pill showing the data source.
3. **Summary strip:** four numbers:
   - topics falling behind (out of 6)
   - the widest pace gap
   - cases still open across the six topics (an item can count in more than one topic)
   - the share answered within a month
4. **Control bar:** sticky on desktop. Below 760px it scrolls with the page instead (CSS class `.ctl` in `<helmet>`). Timeline sits on its own full-width row; the three setting switches share one row beneath it (they wrap on narrow screens). Each has a label, the control, and a line of help text:
   - **Timeline:** Play button and week slider.
   - **Link rule:** Same topic / Same actor.
   - **Answers that count:** Any response / Binding only.
   - **Sourcing:** Weighted / Unweighted.
5. **Pace chart and topic table:**
   - **Chart:** a scatter of new problems per week against answers per week, with one bubble per topic.
   - **Table:** Cases, Pace gap and Median wait, sorted widest gap first, with a legend below that defines each column and the color key.
6. **Topic detail:** spans the full width.
   - **Left:** the verdict and "How sure is this?", which shows all 8 setting combinations.
   - **Right:** four numbers: Pace gap, Still unanswered, Median wait, Answered within a month.
7. **Response map:** cases on the left and responses on the right, joined by link lines. Click a row to trace its links. Window: last 6 weeks or since Jul 1.
8. **Method:** the four method notes.
9. **Footer:** site tagline, data citation, and footer links.

The cumulative opened/closed chart and the Kaplan–Meier curve from v1 were removed on purpose.

## Terms used on the page

- **Cases:** attacks and capability jumps reported since Jul 1, 2026.
- **Pace gap:** new problems for every one answered, as a 4-week trailing mean. Above 1 : 1 means falling behind.
- **Median wait:** days until half of cases got a first public response. This is a Kaplan–Meier median; open cases are treated as censored.

## Design tokens

| Token | Value |
|---|---|
| Ink | `#0a0a0b` |
| Secondary text | `#52525b` |
| Tertiary text | `#6b6b73` |
| Hairline borders | `#e7e7ea`, `#f0f0f2` |
| Falling behind (fill / text) | `#ea580c` / `#c2410c` |
| Keeping up (fill / text) | `#2563eb` / `#1d4ed8` |
| Policy (binding and bills / proposals) | `#7c3aed` / `#a78bfa` |
| Statements | `#a1a1aa` |

## Method (implemented in the logic class, unchanged from v1)

- **Problem (case):** every `atk` or `cap` item tagged with one of the six topics.
- **Answer:** a `def` or `pol` item in the same topic, dated on or after the case.
  - **Same topic:** the first such item closes the case.
  - **Same actor:** the item must also share an entity tag. Up to 3 matches are drawn, and the first one closes the case.
  - **Binding only:** counts only policy classed as Binding.
- **Policy class:** a keyword rule on the headline (`STMT`, `PROPOSED`, `BILLRX`, `BINDING`). A `stage` field overrides it and marks the item as a Bill.
- **Weights:**

  | Source | Weight |
  |---|---|
  | Confirmed, On the record | 1.0 |
  | Researchers | 0.8 |
  | Press | 0.6 |
  | Attacker claim | 0.5 |
  | Self-reported | 0.4 |

  Weights apply to rates and backlog only.
- **Rates:** 4-week trailing mean per week, starting Jun 29, 2026.
- **Median wait 95% interval:** from 200 bootstrap resamples with a fixed seed.
- **Answered within a month:** counts only cases at least 30 days old.
- **How sure is this?:** the same metric recomputed under all 8 combinations of the 3 switches.

Fields used from `items.json`: `id, lane, date, headline, confidence, topics, entities`, plus `stage` if present. `topics` and `entities` can be arrays or `;`-separated strings.

## Recommended data changes for the board

1. **Apply reviewed topic tags.** Start from the CSV.
2. **Add `stage` to bills:** introduced, committee, passed-chamber or enacted.
3. **Add `responds_to: [item ids]` to Defense and Policy items.** This replaces the inferred links with editorial ones.
4. **Optionally backfill pre-July 2026 items** with `backfill: true`, so cases opened earlier are counted in the backlog.

## Keeping it updated

**Data updates itself.** The page reads `/data/items.json` on every load. Nothing needs rebuilding when the board publishes new items. The timeline extends by one step for each new week.

**Routine tasks:**

| When | Task |
|---|---|
| Monthly, or when the board's schema changes | Refresh the fallback snapshot: copy `/data/items.json` to `gap-map/data/items-snapshot.json`. It only needs `updated` and `items`. |
| After each tagging pass | Regenerate the untagged list (below), then review and apply the tags in the board's source data, not in the snapshot. |
| When a bill moves | Set its `stage`. |

**Regenerating the tag-suggestion CSV:**

- **Which rows:** every `def` or `pol` item whose `topics` is empty.
- **Columns:** `id, date, lane, headline, suggested_topics, strength, why, url`.
- **How suggestions are made:** a headline keyword or a shared entity with existing items in a topic. `why` records the keyword or entities.
- **Strength:**
  - `strong`: keyword and entity agree.
  - `check`: only one of them matched.
  - `none`: no match.
- The CSV is a review aid. Never apply it automatically.

**Code changes are needed only for:**

| If you change… | Edit this in `gap-map.dc.html` |
|---|---|
| The six topics (add, rename or remove) | `TOPICS` in the logic class (id, full name, short chart label), plus the hard-coded "/ 6" and "six topics" in the summary strip. Topic IDs must match the board's `topics` values and `/topic/{id}/` URLs. |
| The coverage start date | `START` (the Monday on or before the first item) and the "since Jul 1" / "Jun 29" copy in the template, legend and method notes. |
| Confidence levels | `WT` (weights) and `CONF` (labels), plus the weights table above and the method note. |
| Lanes | `LANE` maps the lane code to the board path used for item links. |
| Adding `responds_to` | In `base()`, use `r.responds_to` when present instead of the topic/entity match, then update the "Known limits" method note. |

**Reproducing the numbers.** Every figure is computed in the browser from `items.json` alone, with no hidden inputs. The bootstrap uses a fixed seed. To check that a figure reproduces:

1. Open the page with the Snapshot file, using the same settings and week.
2. Compare the result with an independent run of `base()`, `km()` and `cov()` in Node. Paste the methods into a plain object, and set `state.items` the way `componentDidMount` does.

The board's own `/data/topics.json` also publishes response lags. Its numbers use a different method, so don't expect them to match the Gap Map's Median wait.

## Porting

If the site uses a framework, port the logic class's `base()`, `km()`, `bootCI()` and `cov()` methods as they are. They are pure functions over the items array. The markup is plain HTML with inline styles.

Data: Bahrami, D. (2026). Machine Speed: a source-verified AI-cyber intelligence board [Data set]. https://machinespeed.techpointe.org/data/, CC BY 4.0. Framework: Bahrami, Chang et al., "The End of the Gray Zone?" (2026), §3.4 Va/Vr.
