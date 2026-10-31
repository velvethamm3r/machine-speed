# Water · So What page

`health/body.html` is the Water page: seventeen US water failures, Flint to the
2026 cyberattacks, set against community income, the repair money, the policy
lag and what prevention would have cost. It builds to `/water/health/` and is
listed on `/so-what/` and the front page (build.py's `SO_WHAT_PAGES`).

## How it is built

Like the Gap Map: authored by hand, wrapped by `build.py` (`hand_page()`) in
the shared head, nav and footer where the `<!-- site-nav -->` and
`<!-- site-footer -->` markers are. Everything between the markers is the page.

- Every CSS selector is prefixed with `.water`, so the page cannot restyle the
  site chrome and the site's global rules do not reach into it.
- Its colour tokens live on `.water`; the dark set is keyed to
  `:root[data-theme="dark"]`, so the page follows the site's theme button.
- Its measure (`.water main`) copies `.wrap` breakpoint for breakpoint.
- d3, topojson-client and the Schibsted Grotesk face load from `WATER_HEAD` in
  `build.py`. The US state shapes come from jsDelivr at run time; drop
  `us-atlas@3.0.1`'s `states-10m.json` into `water/health/` and copy it to
  `dist/` in `build.py` if the site ever needs to work without that CDN.

## Editing

All incident data lives in the `EV` array inside the page's script; town
demographics in `DEM`, state incomes in `STINC`, lead bands in `LEAD`, the
policy timeline in `LAG`. The income chart and its side-panel figures recompute
from `EV` and `DEM`, so adding an incident updates them. The heading "All 17
incidents" in section 7 is typed by hand: bump it when you add one.

## Before publishing

- Median incomes for all 17 incidents are checked (Census QuickFacts; Braham
  via Census Reporter / Data USA). Poverty and race percentages for the eight
  small towns marked `incOnly:true` in `DEM` are still approximate and say so.
- Nine cyber incidents cite "Machine Speed water record" at `/water/`, which
  does not exist on the site. Replace those `src` entries with the original
  articles, or build that record page.
- Milwaukee's "about a week" boil-water advisory is not checked against a source.
