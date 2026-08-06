#!/usr/bin/env python3
"""
Machine Speed — static site generator.

Reads data.json (single source of truth, rewritten by the daily run) and
writes a fully pre-rendered site into dist/:

    dist/
      index.html            home board (all content in the HTML, no JS needed)
      capability.html       lane pages
      policy.html
      defense.html
      attacks.html
      archive.html          archive index
      archive/…​.html        dated snapshot of today's board
      about.html
      feed.xml              RSS 2.0
      style.css             shared stylesheet (cached across pages)
      theme.js              theme toggle only (site works fine without it)

Usage:
    python3 build.py            # build into ./dist
    python3 build.py --out X    # build into X

No dependencies beyond the Python 3 standard library, so it runs unmodified
on Cloudflare Pages' build image, GitHub Actions, or your laptop.
"""

import argparse
import json
import shutil
import sys
from datetime import datetime, timedelta
from html import escape
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration — edit these for your deployment
# ---------------------------------------------------------------------------

SITE_URL = "https://machinespeed.techpointe.org"   # no trailing slash
SITE_NAME = "Machine Speed"
SITE_TAGLINE = "AI-Cyber Intel"
SITE_DESCRIPTION = ("A daily, source-verified intelligence board on frontier AI "
                    "cyber capability and the defense & policy lag around it.")
NEW_WINDOW_DAYS = 2   # items this recent get the "New" badge / 48h strip
STRIP_MAX = 6         # spec caps the "New in the last 48 hours" strip at six

# Coverage period. The board shows a stated span of days rather than a rolling
# window. data.json may set "coverageStart"/"coverageEnd" explicitly; if it does
# not, the span is derived from the oldest and newest item on the board, so the
# label can never drift out of step with what is actually shown.
#
# COVERAGE_SLACK_DAYS is how far outside an explicit coverage period an item may
# fall before validate() complains. It only bites when the period is declared by
# hand — a derived period always fits its own items exactly.
COVERAGE_SLACK_DAYS = 0

# Items inside a lane are grouped under week headings so a long period stays
# navigable. Set to False for one flat list per lane.
GROUP_BY_WEEK = True

# How many recent weeks the home page prints in full. Everything older is still
# on the home page, but as a one-line-per-item index that links into that week's
# own page — the running list survives without the board becoming a wall.
# Weeks are Monday-to-Sunday, so 2 means "this week and last week".
FRONT_WEEKS = 2
# Where the editorial note (data.json's "judgmentNote") appears on the board:
# "footer" tucks it into a collapsed disclosure below the sources, "header" puts
# it under the hero as it used to sit, "none" keeps it off the board entirely.
# The note is written to the archive snapshot and the newsletter draft either way,
# so the record survives whichever placement is chosen.
NOTE_PLACEMENT = "footer"

# Custom domain. Written to dist/CNAME on every build so a GitHub Pages deploy
# can never silently drop the domain setting.
CNAME = SITE_URL.split("//", 1)[1]

# Substack. Set SUBSTACK_URL to the publication home (no trailing slash) to turn
# on the subscribe links; leave it empty and every Substack element disappears.
SUBSTACK_URL = ""                       # e.g. "https://machinespeed.substack.com"
SUBSTACK_CTA = "Get the board in your inbox"

LANES = {
    "cap": {"name": "Capability", "var": "--cap", "pill": "lp-cap", "page": "capability.html",
            "desc": "What frontier AI systems can now do in the cyber domain."},
    "pol": {"name": "Policy", "var": "--pol", "pill": "lp-pol", "page": "policy.html",
            "desc": "Government, standards and governance responses."},
    "def": {"name": "Defense", "var": "--def", "pill": "lp-def", "page": "defense.html",
            "desc": "Defensive tooling, patching and mitigation."},
    "atk": {"name": "Attacks", "var": "--atk", "pill": "lp-atk", "page": "attacks.html",
            "desc": "Real-world incidents and offensive use."},
}

CONF = {
    "confirmed": "Confirmed by org", "claimed": "Claimed by attacker",
    "researchers": "Reported by researchers", "press": "Reported by press",
    "official": "Official announcement", "vendor": "Vendor claim — unverified",
}
CONF_VAR = {"confirmed": "--cap", "claimed": "--atk", "researchers": "--def",
            "press": "--ink-3", "official": "--pol", "vendor": "--atk"}

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fmt_date(iso: str) -> str:
    """2026-07-21 -> Jul 21, 2026"""
    if not iso:
        return ""
    y, m, d = iso.split("-")
    return f"{MONTHS[int(m) - 1]} {int(d)}, {y}"


def rfc822(iso_date: str) -> str:
    """Date-only ISO -> RFC 822 pubDate for RSS."""
    dt = datetime.strptime(iso_date, "%Y-%m-%d")
    return dt.strftime("%a, %d %b %Y 12:00:00 GMT")


def days_ago(item_date: str, as_of: str) -> int:
    d = datetime.strptime(item_date, "%Y-%m-%d")
    now = datetime.strptime(as_of[:10], "%Y-%m-%d")
    return (now - d).days


def fmt_span(start: str, end: str) -> str:
    """2026-07-01, 2026-08-05 -> 'Jul 1 – Aug 5, 2026' (year shown once when shared)."""
    if not start or not end:
        return ""
    sy, sm, sd = start.split("-")
    ey, em, ed = end.split("-")
    left = f"{MONTHS[int(sm) - 1]} {int(sd)}" + ("" if sy == ey else f", {sy}")
    right = f"{MONTHS[int(em) - 1]} {int(ed)}, {ey}"
    return left + " – " + right


def note_paras(text: str) -> str:
    """Blank-line-separated prose -> paragraphs. A single block stays one <p>."""
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    return "".join(f"<p>{escape(' '.join(b.split()))}</p>" for b in blocks)


def coverage_span(d: dict):
    """(start, end) of the period the board covers, as YYYY-MM-DD strings.

    Explicit "coverageStart"/"coverageEnd" in data.json win; otherwise the span
    is derived from the items themselves so the stated period and the shown
    items can never disagree.
    """
    dates = sorted(i["date"] for i in d.get("items", []) if i.get("date"))
    start = d.get("coverageStart") or (dates[0] if dates else "")
    end = d.get("coverageEnd") or (dates[-1] if dates else "")
    return start, end


def week_start(iso: str) -> str:
    """Monday of the week containing this date."""
    dt = datetime.strptime(iso, "%Y-%m-%d")
    return (dt - timedelta(days=dt.weekday())).strftime("%Y-%m-%d")


def week_end(monday: str) -> str:
    """Sunday closing the week that opens on this Monday."""
    return (datetime.strptime(monday, "%Y-%m-%d") + timedelta(days=6)).strftime("%Y-%m-%d")


def week_buckets(items, span_start: str, span_end: str):
    """[{monday, lo, hi, label, path, items}, ...], newest week first.

    Week boundaries are Monday-to-Sunday, but the first and last labels are
    trimmed to the coverage period so the board never advertises days it does
    not cover. Only weeks that actually hold items appear, so a quiet week
    never produces an empty page.
    """
    buckets = {}
    for it in items:
        buckets.setdefault(week_start(it["date"]), []).append(it)
    out = []
    for mon in sorted(buckets, reverse=True):
        sun = week_end(mon)
        lo = max(mon, span_start) if span_start else mon
        hi = min(sun, span_end) if span_end else sun
        out.append({
            "monday": mon, "lo": lo, "hi": hi, "label": fmt_span(lo, hi),
            "path": f"week/{mon}/index.html",
            "items": sorted(buckets[mon], key=lambda i: i["date"], reverse=True),
        })
    return out


def group_by_week(items, span_start: str, span_end: str):
    """[(label, [item, ...]), ...] — the week headings used inside a lane."""
    return [(w["label"], w["items"]) for w in week_buckets(items, span_start, span_end)]


REQUIRED_ITEM_FIELDS = ["id", "lane", "date", "headline", "core", "confidence", "outlet", "url"]


def validate(d: dict):
    """Structural checks run before anything is written.

    A failed check aborts the build with a non-zero exit, so a bad data.json
    fails the GitHub Action instead of publishing a broken board — the live
    site simply keeps serving the last good deploy.
    """
    errors, warnings = [], []

    for key in ("updatedISO", "updatedDisplay", "judgmentNote", "internalNote",
                "items", "watchlist", "archives"):
        if not d.get(key):
            errors.append(f"missing or empty top-level key: {key}")
    if errors:
        return errors, warnings

    try:
        run_day = datetime.strptime(d["updatedISO"][:10], "%Y-%m-%d").date()
    except ValueError:
        return [f"updatedISO is not a valid ISO timestamp: {d['updatedISO']!r}"], warnings

    cov_start, cov_end = coverage_span(d)
    if cov_start and cov_end and cov_start > cov_end:
        errors.append(f"coverage period runs backwards: {cov_start} → {cov_end}")

    seen = set()
    for n, it in enumerate(d["items"]):
        where = f"item[{n}] {it.get('id', '<no id>')}"
        for f in REQUIRED_ITEM_FIELDS:
            if not it.get(f):
                errors.append(f"{where}: missing field '{f}'")
        if it.get("id") in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(it.get("id"))
        if it.get("lane") not in LANES:
            errors.append(f"{where}: lane must be one of {', '.join(LANES)}")
        if it.get("confidence") not in CONF:
            errors.append(f"{where}: confidence must be one of {', '.join(CONF)}")
        if not str(it.get("url", "")).startswith("https://"):
            errors.append(f"{where}: url must be an https:// link")
        try:
            age = days_ago(it["date"], d["updatedISO"])
            if age < 0:
                errors.append(f"{where}: dated in the future ({it['date']})")
            elif cov_start and days_ago(it["date"], cov_start) > COVERAGE_SLACK_DAYS:
                warnings.append(f"{where}: dated {it['date']}, before the stated coverage "
                                f"period ({fmt_span(cov_start, cov_end)}) — widen "
                                f"coverageStart or drop the item")
            elif cov_end and days_ago(cov_end, it["date"]) > COVERAGE_SLACK_DAYS:
                warnings.append(f"{where}: dated {it['date']}, after the stated coverage "
                                f"period ({fmt_span(cov_start, cov_end)})")
        except (KeyError, ValueError):
            errors.append(f"{where}: date must be YYYY-MM-DD")

    for w in d["watchlist"]:
        if not w.get("thread") or not w.get("status"):
            errors.append(f"watchlist entry missing thread or status: {w!r}")

    root = Path(__file__).parent
    for a in d["archives"]:
        if not a.get("date") or not a.get("file"):
            errors.append(f"archive entry missing date or file: {a!r}")
        # Today's snapshot is written by this build, so it is allowed not to exist yet.
        elif a["date"] != run_day.isoformat() and not (root / a["file"]).exists():
            errors.append(f"archives[] points at {a['file']}, which is not in the repo "
                          f"— that link would 404")
    if not any(a.get("date") == run_day.isoformat() for a in d["archives"]):
        errors.append(f"archives[] has no entry for today ({run_day}) — add one before building")

    strip = [i for i in d["items"]
             if i.get("isNew") is True
             or (i.get("isNew") is not False and days_ago(i["date"], d["updatedISO"]) <= NEW_WINDOW_DAYS)]
    if not strip:
        warnings.append("nothing qualifies for the 48-hour strip — the board will say so "
                        "plainly, which is the correct outcome on a quiet day")
    elif len(strip) > STRIP_MAX:
        warnings.append(f"{len(strip)} items qualify for the 48-hour strip; "
                        f"only the newest {STRIP_MAX} will show")

    # Tolerate one day of slack: updatedISO carries an ET offset while a CI
    # runner's clock is usually UTC, so an evening run legitimately straddles
    # midnight. Anything further out is genuinely stale.
    drift = abs((datetime.now().date() - run_day).days)
    if drift > 1:
        warnings.append(f"updatedISO date ({run_day}) is {drift} days from today "
                        f"({datetime.now().date()})")

    return errors, warnings


class Site:
    def __init__(self, data: dict):
        self.d = data
        self.as_of = data.get("updatedISO", "")
        self.prefix = ""  # set to "../" while rendering pages inside /archive
        self.cov_start, self.cov_end = coverage_span(data)
        self.coverage = fmt_span(self.cov_start, self.cov_end)
        self.coverage_days = (
            days_ago(self.cov_start, self.cov_end) + 1 if self.cov_start and self.cov_end else 0)
        # Every week that holds at least one item, newest first. The home page,
        # the week pages and the archive index all read from this one list.
        self.weeks = week_buckets(data.get("items", []), self.cov_start, self.cov_end)
        # Items on or after this Monday are printed in full on the home page;
        # everything older is indexed one line per item. Empty means the board
        # is short enough that the whole period fits on the front page.
        self.front_cutoff = (self.weeks[FRONT_WEEKS - 1]["monday"]
                             if len(self.weeks) > FRONT_WEEKS else "")

    def lane_sections(self, key: str, items=None, group=None) -> str:
        """Item cards for a lane, optionally split under week headings."""
        items = self.lane_items(key) if items is None else items
        group = GROUP_BY_WEEK if group is None else group
        if not group or len(items) < 6:
            return "".join(self.item_card(i) for i in items)
        out = []
        for label, rows in group_by_week(items, self.cov_start, self.cov_end):
            out.append(f'<h4 class="weekhead">{escape(label)}'
                       f'<span>{len(rows)}</span></h4>')
            out += [self.item_card(i) for i in rows]
        return "".join(out)

    # -- item queries -------------------------------------------------------
    def lane_items(self, key: str, pool=None):
        items = [i for i in (self.d["items"] if pool is None else pool) if i["lane"] == key]
        return sorted(items, key=lambda i: i["date"], reverse=True)

    def front_items(self, key: str):
        """A lane's items from the weeks the home page prints in full."""
        items = self.lane_items(key)
        if not self.front_cutoff:
            return items
        return [i for i in items if i["date"] >= self.front_cutoff]

    def fresh_items(self):
        fresh = [i for i in self.d["items"] if self.is_new(i)]
        fresh.sort(key=lambda i: i["date"], reverse=True)
        return fresh[:STRIP_MAX]

    def is_new(self, item) -> bool:
        """A run can override the date rule with isNew.

        `isNew: true` forces an item into the 48-hour strip — used when a story
        is new to the board but a few days old in the world. `isNew: false`
        keeps a genuinely recent item out. Omit the field for the date rule.
        """
        if "isNew" in item:
            return bool(item["isNew"])
        return days_ago(item["date"], self.as_of) <= NEW_WINDOW_DAYS

    # -- shared fragments ---------------------------------------------------
    def nav(self, active: str) -> str:
        links = [("index.html", "Board"), ("capability.html", "Capability"),
                 ("policy.html", "Policy"), ("defense.html", "Defense"),
                 ("attacks.html", "Attacks"), ("archive.html", "Archive"),
                 ("about.html", "About")]
        out = ['<nav class="nav" aria-label="Site">',
               f'<a class="logo" href="{self.prefix}index.html"><b>Machine&nbsp;Speed</b>'
               f'<span>{escape(SITE_TAGLINE)}</span></a>']
        for href, label in links:
            cls = "link active" if href == active else "link"
            aria = ' aria-current="page"' if href == active else ""
            out.append(f'<a class="{cls}" href="{self.prefix}{href}"{aria}>{label}</a>')
        out.append('<span class="spacer"></span>')
        if SUBSTACK_URL:
            out.append(f'<a class="link sub-link" href="{escape(SUBSTACK_URL, quote=True)}" '
                       f'target="_blank" rel="noopener">Subscribe</a>')
        out.append(f'<a class="link" href="{self.prefix}feed.xml">RSS</a>')
        out.append('<button class="themebtn" type="button" data-theme-toggle hidden>'
                   '<span class="ico">☀</span> <span class="lbl">Light</span></button>')
        out.append('</nav>')
        return "\n    ".join(out)

    def item_card(self, it) -> str:
        badge = '<span class="badge-new">New</span> ' if self.is_new(it) else ""
        conf = it["confidence"]
        return (
            f'<article class="item" id="{escape(it["id"])}">'
            f'<h4>{badge}{escape(it["headline"])}</h4>'
            f'<p>{escape(it["core"])}</p>'
            f'<div class="meta">'
            f'<span class="conf c-{conf}">{CONF.get(conf, conf)}</span>'
            f'<span class="src"><a href="{escape(it["url"], quote=True)}" target="_blank" '
            f'rel="noopener">{escape(it["outlet"])}</a> · '
            f'<time datetime="{it["date"]}">{fmt_date(it["date"])}</time></span>'
            f'</div></article>')

    def sources_block(self, pool=None, heading: str = "Sources") -> str:
        seen, rows = set(), []
        for i in (self.d["items"] if pool is None else pool):
            if i["url"] in seen:
                continue
            seen.add(i["url"])
            host = i["url"].split("/")[2].removeprefix("www.")
            rows.append(
                f'<li>{escape(i["headline"])} — <span class="outlet">{escape(i["outlet"])}, '
                f'{fmt_date(i["date"])}.</span> '
                f'<a href="{escape(i["url"], quote=True)}" target="_blank" rel="noopener">{escape(host)} ↗</a></li>')
        return (f'<section class="block"><h2 class="blockhead">{escape(heading)}</h2>'
                '<ol class="sources">' + "\n".join(rows) + "</ol></section>")

    def watchlist_block(self) -> str:
        rows = []
        for w in self.d["watchlist"]:
            changed = (f'<time datetime="{w["changed"]}">{fmt_date(w["changed"])}</time>'
                       if w.get("changed") else "—")
            rows.append(f'<tr><td class="thread">{escape(w["thread"])}</td>'
                        f'<td class="status">{escape(w["status"])}</td>'
                        f'<td class="when">{changed}</td></tr>')
        return ('<section class="block"><h2 class="blockhead">Still watching</h2>'
                '<table class="watch"><thead><tr><th scope="col">Thread</th>'
                '<th scope="col">Current status</th>'
                '<th scope="col">Last changed</th></tr></thead><tbody>'
                + "\n".join(rows) + "</tbody></table></section>")

    def note_block(self, where: str) -> str:
        """The editorial note, rendered wherever NOTE_PLACEMENT says — or nowhere.

        The note still ships in data.json, the archive snapshot and the newsletter
        draft regardless; this only controls whether the board itself prints it.
        """
        text = self.d.get("judgmentNote", "")
        if not text or NOTE_PLACEMENT != where:
            return ""
        if where == "header":
            return f'<div class="note">{note_paras(text)}</div>'
        return ('<details class="notebox"><summary>Editorial note — sourcing and '
                'judgment calls behind this board</summary>'
                f'<div class="note">{note_paras(text)}</div></details>')

    def subscribe_block(self) -> str:
        """Substack call-to-action. Renders nothing at all if SUBSTACK_URL is unset.

        A plain link rather than Substack's iframe embed: it keeps the site
        dependency-free and loads no third-party tracking, and it works
        identically on the archived snapshots.
        """
        if not SUBSTACK_URL:
            return ""
        return (f'<section class="block subscribe">'
                f'<h2 class="blockhead">{escape(SUBSTACK_CTA)}</h2>'
                f'<p>The board updates daily on the web. The newsletter is the same '
                f'reporting, written up and sent to your inbox — same sourcing rules, '
                f'same corrections policy.</p>'
                f'<p><a class="subbtn" href="{escape(SUBSTACK_URL, quote=True)}" '
                f'target="_blank" rel="noopener">Subscribe on Substack ↗</a></p>'
                f'</section>')

    def footer(self) -> str:
        legend = "".join(
            f'<span><i style="background:var({v["var"]})"></i>{v["name"]}</span>'
            for v in LANES.values())
        year = (self.as_of or "2026")[:4]
        internal = escape(self.d.get("internalNote", ""))
        return (f'<footer><div class="legend">{legend}</div>'
                f'<p style="margin-top:12px">{internal}</p>'
                f'<p style="margin-top:8px">{SITE_NAME} · Research and display only — nothing here '
                f'is published or sent on anyone\'s behalf. © {year}</p></footer>')

    # -- charts (pure HTML/CSS, computed at build time) ---------------------
    def chart_lane(self) -> str:
        counts = {k: len(self.lane_items(k)) for k in LANES}
        mx = max(counts.values()) or 1
        bars, summary = [], []
        for k, v in LANES.items():
            n = counts[k]
            w = round(n / mx * 100)
            summary.append(f"{v['name']} {n}")
            bars.append(
                f'<div class="hbar"><span class="hlabel">{v["name"]}</span>'
                f'<span class="htrack"><span class="hfill" '
                f'style="width:{w}%;background:var({v["var"]})"></span></span>'
                f'<span class="hval">{n}</span></div>')
        return (f'<div class="chartcard"><h3>Coverage by lane · {escape(self.coverage)}</h3>'
                f'<div class="hbars" role="img" aria-label="Items per lane: {", ".join(summary)}">'
                + "".join(bars) + "</div></div>")

    def chart_conf(self) -> str:
        counts = {}
        for i in self.d["items"]:
            counts[i["confidence"]] = counts.get(i["confidence"], 0) + 1
        total = sum(counts.values()) or 1
        order = sorted(counts, key=lambda k: -counts[k])
        acc, segs, legend, summary = 0.0, [], [], []
        for k in order:
            start = acc / total * 100
            acc += counts[k]
            end = acc / total * 100
            var = CONF_VAR.get(k, "--accent")
            segs.append(f"var({var}) {start:.1f}% {end:.1f}%")
            legend.append(f'<div class="row"><i style="background:var({var})"></i>'
                          f'{CONF.get(k, k)} <b>{counts[k]}</b></div>')
            summary.append(f"{CONF.get(k, k)}: {counts[k]}")
        return (f'<div class="chartcard"><h3>Confidence mix</h3>'
                f'<div class="donutwrap" role="img" aria-label="Confidence mix of {total} items — '
                f'{escape("; ".join(summary))}">'
                f'<div class="donut" aria-hidden="true" style="background:conic-gradient({",".join(segs)})">'
                f'<div class="center"><b>{total}</b><span>items</span></div></div>'
                f'<div class="dlegend" aria-hidden="true">{"".join(legend)}</div>'
                f'</div></div>')

    # -- page shell ---------------------------------------------------------
    def page(self, *, path: str, title: str, description: str, body: str,
             extra_head: str = "", asset_prefix: str = "") -> str:
        # Directory-style pages (week/YYYY-MM-DD/index.html) are canonically the
        # directory URL — the server serves the same bytes either way, and one
        # canonical keeps search engines and shared links from splitting.
        rel = "" if path == "index.html" else path
        if rel.endswith("/index.html"):
            rel = rel[: -len("index.html")]
        canonical = f"{SITE_URL}/{rel}"
        return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title>
<meta name="description" content="{escape(description, quote=True)}">
<link rel="canonical" href="{canonical}">
<link rel="alternate" type="application/rss+xml" title="{escape(SITE_NAME)}" href="{SITE_URL}/feed.xml">
<meta property="og:site_name" content="{escape(SITE_NAME)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{escape(title, quote=True)}">
<meta property="og:description" content="{escape(description, quote=True)}">
<meta property="og:url" content="{canonical}">
<meta name="twitter:card" content="summary">
<script>
/* Set theme before first paint to avoid a flash. Falls back to system preference. */
(function(){{try{{var t=localStorage.getItem("ms-theme");
if(!t)t=matchMedia("(prefers-color-scheme: light)").matches?"light":"dark";
document.documentElement.setAttribute("data-theme",t);}}catch(e){{}}}})();
</script>
<link rel="stylesheet" href="{asset_prefix}style.css">
{extra_head}</head>
<body>
<div class="wrap">

  {body}

</div>
<script src="{asset_prefix}theme.js" defer></script>
</body>
</html>
"""

    # -- home ---------------------------------------------------------------
    def home_body(self) -> str:
        d = self.d
        fresh = self.fresh_items()
        if fresh:
            lis = []
            for it in fresh:
                lane = LANES[it["lane"]]
                lis.append(
                    f'<li><span class="lanepill {lane["pill"]}">{lane["name"]}</span>'
                    f'<span>{escape(it["headline"])}. '
                    f'<a href="#{escape(it["id"])}">details ↓</a> · '
                    f'<a href="{escape(it["url"], quote=True)}" target="_blank" rel="noopener">source ↗</a>'
                    f'</span></li>')
            strip_inner = "<ul>" + "".join(lis) + "</ul>"
        else:
            strip_inner = ('<p class="empty"><strong style="color:var(--ink)">Nothing new to report '
                           'since the last run.</strong> A fresh sweep across all four lanes surfaced '
                           "no verified, in-window items that weren't already shown. No items were "
                           'invented to fill this space.</p>')

        stats = "".join(
            f'<div class="stat"><div class="n">{len(self.lane_items(k))}</div>'
            f'<div class="l">{v["name"]}</div>'
            f'<div class="bar" style="background:var({v["var"]})"></div></div>'
            for k, v in LANES.items())

        lanes_html = []
        for k, v in LANES.items():
            items = self.front_items(k)
            total = len(self.lane_items(k))
            count = f"{len(items)} of {total} items" if self.front_cutoff else f"{total} items"
            lanes_html.append(
                f'<section class="lane"><h3><span class="barv" style="background:var({v["var"]})"></span>'
                f'{v["name"]}<span class="count">{count}</span>'
                f'<a class="more" href="{self.prefix}{v["page"]}">view lane ↗</a></h3>'
                + self.lane_sections(k, items) + "</section>")

        if self.front_cutoff:
            shown = fmt_span(self.front_cutoff, self.cov_end)
            sub = (f'Frontier AI cyber capability against the defense &amp; policy lag. '
                   f'The last two weeks in full — <strong>{escape(shown)}</strong> — then every '
                   f'earlier item from {escape(self.coverage)} indexed by week below.')
        else:
            sub = ('Frontier AI cyber capability against the defense &amp; policy lag — '
                   f'every verified item from <strong>{escape(self.coverage)}</strong>, '
                   'grouped by lane and by week.')

        return f"""{self.nav("index.html")}

  <header class="pagehead">
    <h1>The capability-vs-defense gap, tracked daily</h1>
    <div class="sub wide">{sub}</div>
    <div class="stamprow">
      <div class="stamp"><span class="dot"></span>Last updated:
        <time datetime="{d.get("updatedISO", "")}">{escape(d.get("updatedDisplay", ""))}</time></div>
      <div class="stamp cov">Covering <time datetime="{self.cov_start}">{escape(self.coverage)}</time>
        · {len(d["items"])} items · {self.coverage_days} days</div>
    </div>
    {self.note_block("header")}
  </header>

  <section class="newstrip">
    <h2>⚡ New in the last 48 hours</h2>
    {strip_inner}
  </section>

  <div class="stats">{stats}</div>

  <div class="charts">
    {self.chart_lane()}
    {self.chart_conf()}
  </div>

  <div class="lanes">
    {"".join(lanes_html)}
  </div>

  {self.older_index()}

  {self.watchlist_block()}

  {self.sources_block()}

  {self.note_block("footer")}

  {self.subscribe_block()}

  {self.footer()}"""

    def home_jsonld(self) -> str:
        items = sorted(self.d["items"], key=lambda i: i["date"], reverse=True)
        graph = {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": f"{SITE_NAME} — daily AI-cyber intelligence board",
            "dateModified": self.as_of,
            "url": SITE_URL + "/",
            "itemListElement": [
                {"@type": "ListItem", "position": n + 1,
                 "url": f"{SITE_URL}/{LANES[i['lane']]['page']}#{i['id']}",
                 "name": i["headline"]}
                for n, i in enumerate(items)],
        }
        return ('<script type="application/ld+json">'
                + json.dumps(graph, ensure_ascii=False) + "</script>\n")

    # -- the running list, compressed --------------------------------------
    def older_index(self) -> str:
        """One line per item for every week older than the front page's window.

        The point of the board is that nothing scrolls off it. Printing every
        card for a period that keeps growing is what made the page heavy, so the
        older weeks stay present as an index and each headline links into the
        full card on that week's own page.
        """
        older = self.weeks[FRONT_WEEKS:] if self.front_cutoff else []
        if not older:
            return ""
        blocks = []
        for w in older:
            rows = []
            for it in w["items"]:
                lane = LANES[it["lane"]]
                rows.append(
                    f'<li><span class="lanepill {lane["pill"]}">{lane["name"]}</span>'
                    f'<a class="h" href="{self.prefix}week/{w["monday"]}/#{escape(it["id"])}">'
                    f'{escape(it["headline"])}</a>'
                    f'<span class="m"><a href="{escape(it["url"], quote=True)}" target="_blank" '
                    f'rel="noopener">{escape(it["outlet"])} ↗</a> · '
                    f'<time datetime="{it["date"]}">{fmt_date(it["date"])}</time></span></li>')
            blocks.append(
                f'<div class="wkgroup"><h3><a href="{self.prefix}week/{w["monday"]}/">'
                f'{escape(w["label"])} ↗</a><span>{len(w["items"])} items</span></h3>'
                f'<ul class="mini">{"".join(rows)}</ul></div>')
        return ('<section class="block older"><h2 class="blockhead">Earlier in this period</h2>'
                '<p class="lede">Every item still on the board, oldest weeks compressed to one '
                'line each. Open a week for the full cards, sourcing and confidence labels.</p>'
                + "".join(blocks) + '</section>')

    # -- week pages ---------------------------------------------------------
    def week_body(self, idx: int) -> str:
        """One Monday-to-Sunday week, all four lanes, at its own URL."""
        w = self.weeks[idx]
        newer = self.weeks[idx - 1] if idx > 0 else None
        older = self.weeks[idx + 1] if idx + 1 < len(self.weeks) else None

        lanes_html = []
        for k, v in LANES.items():
            items = self.lane_items(k, w["items"])
            if not items:
                continue
            lanes_html.append(
                f'<section class="lane"><h3><span class="barv" style="background:var({v["var"]})"></span>'
                f'{v["name"]}<span class="count">{len(items)} items</span>'
                f'<a class="more" href="{self.prefix}{v["page"]}">full lane ↗</a></h3>'
                + self.lane_sections(k, items, group=False) + "</section>")

        pager = ['<nav class="pager" aria-label="Weeks">']
        pager.append(f'<a class="prev" href="{self.prefix}week/{older["monday"]}/">'
                     f'← {escape(older["label"])}</a>' if older else '<span class="prev"></span>')
        pager.append(f'<a class="idx" href="{self.prefix}archive.html">All weeks</a>')
        pager.append(f'<a class="next" href="{self.prefix}week/{newer["monday"]}/">'
                     f'{escape(newer["label"])} →</a>' if newer else '<span class="next"></span>')
        pager.append('</nav>')
        pager_html = "".join(pager)

        return f"""{self.nav("archive.html")}

  <header class="pagehead">
    <h1>{escape(w["label"])}</h1>
    <div class="sub">{len(w["items"])} verified items across all four lanes, from the week of
      {escape(fmt_date(w["monday"]))}. Part of the {escape(self.coverage)} board.</div>
    <div class="stamprow">
      <div class="stamp"><a href="{self.prefix}index.html">← Back to the live board</a></div>
      <div class="stamp cov">Week of <time datetime="{w["monday"]}">{escape(fmt_date(w["monday"]))}</time></div>
    </div>
  </header>

  {pager_html}

  <div class="lanes">
    {"".join(lanes_html)}
  </div>

  {self.sources_block(w["items"], "Sources cited this week")}

  {pager_html}

  {self.footer()}"""

    # -- lane pages ---------------------------------------------------------
    def lane_body(self, key: str) -> str:
        v = LANES[key]
        items = self.lane_items(key)
        return f"""{self.nav(v["page"])}

  <header class="pagehead">
    <h1>{v["name"]}<span class="lanerule" style="background:var({v["var"]})"></span></h1>
    <div class="sub">{escape(v["desc"])} {escape(self.coverage)} · {len(items)} items.</div>
    <div class="stamp"><span class="dot"></span>Last updated:
      <time datetime="{self.as_of}">{escape(self.d.get("updatedDisplay", ""))}</time></div>
  </header>

  <div class="lanes lanes-single">
    <section class="lane"><h3><span class="barv" style="background:var({v["var"]})"></span>
      {v["name"]}<span class="count">{len(items)} items · {escape(self.coverage)}</span></h3>
      {self.lane_sections(key)}
    </section>
  </div>

  {self.sources_block()}

  {self.footer()}"""

    # -- archive index ------------------------------------------------------
    def archive_body(self) -> str:
        weeks = []
        for w in self.weeks:
            mix = " · ".join(f'{LANES[k]["name"]} {n}' for k, n in
                             ((k, len(self.lane_items(k, w["items"]))) for k in LANES) if n)
            weeks.append(
                f'<a href="{self.prefix}week/{w["monday"]}/"><span class="d">{escape(w["label"])}</span>'
                f'<span class="m">{len(w["items"])} items — {escape(mix)}</span></a>')
        snaps = "".join(
            f'<a href="{escape(a["file"], quote=True)}"><span class="d">{fmt_date(a["date"])}</span>'
            f'<span class="m">{a.get("items", "")} items — {escape(a.get("note", ""))}</span></a>'
            for a in sorted(self.d.get("archives", []), key=lambda a: a["date"], reverse=True))
        return f"""{self.nav("archive.html")}

  <header class="pagehead">
    <h1>Archive</h1>
    <div class="sub">Two ways in. <strong>By week</strong> is the board itself, split into
      Monday-to-Sunday pages that stay live and keep their links. <strong>By run</strong> is the
      frozen snapshot taken each time the board was published — the record of what it said that
      day, corrections and all.</div>
  </header>

  <section class="block"><h2 class="blockhead">By week — {len(self.weeks)} weeks,
    {len(self.d["items"])} items</h2>
    <div class="arch">{"".join(weeks)}</div>
  </section>

  <section class="block"><h2 class="blockhead">By run — dated snapshots</h2>
    <p class="lede">Each is a self-contained copy of the whole board as it stood that day.
      Snapshots are never edited after the fact.</p>
    <div class="arch">{snaps}</div>
  </section>

  {self.footer()}"""

    # -- about --------------------------------------------------------------
    def about_body(self) -> str:
        paras = "".join(f"<p>{escape(p)}</p>" for p in self.d.get("about", []))
        return f"""{self.nav("about.html")}

  <header class="pagehead"><h1>About {escape(SITE_NAME)}</h1></header>
  <div class="prose">{paras}</div>

  {self.footer()}"""

    # -- newsletter draft ---------------------------------------------------
    def newsletter_draft(self) -> str:
        """A paste-ready Substack post built from the same data as the board.

        This is a DRAFT and nothing more. Nothing here is posted, scheduled or
        sent — the file is written to newsletter/ for a human to read, edit and
        publish by hand.
        """
        day = fmt_date(self.as_of[:10])
        out = [f"# Machine Speed — {day}", ""]
        out.append(f"*{SITE_DESCRIPTION}* "
                   f"Covering {self.coverage} · {len(self.d['items'])} items. "
                   f"[Live board]({SITE_URL}/) · [RSS]({SITE_URL}/feed.xml)")
        out += ["", "---", ""]

        fresh = self.fresh_items()
        if fresh:
            out.append("## New in the last 48 hours")
            out.append("")
            for it in fresh:
                out.append(f"- **{LANES[it['lane']]['name']}** — {it['headline']}. "
                           f"[{it['outlet']}]({it['url']})")
            out.append("")
        else:
            out += ["## New in the last 48 hours", "",
                    "Nothing new to report since the last run. A fresh sweep across all four "
                    "lanes surfaced no verified, in-window items that weren't already shown. "
                    "No items were invented to fill this space.", ""]

        for key, lane in LANES.items():
            items = self.lane_items(key)
            if not items:
                continue
            out += [f"## {lane['name']}", ""]
            for it in items:
                out.append(f"**{it['headline']}**  ")
                out.append(f"{it['core']}  ")
                out.append(f"*{CONF.get(it['confidence'], it['confidence'])} — "
                           f"[{it['outlet']}]({it['url']}), {fmt_date(it['date'])}*")
                out.append("")

        out += ["## Still watching", ""]
        for w in self.d["watchlist"]:
            changed = f" *(last changed {fmt_date(w['changed'])})*" if w.get("changed") else ""
            out.append(f"- **{w['thread']}** — {w['status']}{changed}")
        out += ["", "---", "",
                "### Editorial note", "", self.d.get("judgmentNote", ""), "",
                f"Every link above was opened and confirmed before publication. "
                f"The board lives at [{CNAME}]({SITE_URL}/).", ""]
        return "\n".join(out)

    # -- sitemap -------------------------------------------------------------
    def sitemap(self) -> str:
        """Canonical routes only.

        Lane pages, the archive index, About and every week page — the pages
        meant to be found. Dated snapshots are deliberately left out: they are
        the same items again, and pointing crawlers at all of them would bury
        the live board under copies of itself.
        """
        day = (self.as_of or "")[:10]
        urls = [("", "daily", "1.0"), ("archive.html", "daily", "0.6"),
                ("about.html", "monthly", "0.3")]
        urls += [(v["page"], "daily", "0.8") for v in LANES.values()]
        urls += [(f'week/{w["monday"]}/', "weekly" if n else "daily", "0.7")
                 for n, w in enumerate(self.weeks)]
        out = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for loc, freq, pri in urls:
            out.append(f"  <url><loc>{SITE_URL}/{loc}</loc>"
                       + (f"<lastmod>{day}</lastmod>" if day else "")
                       + f"<changefreq>{freq}</changefreq><priority>{pri}</priority></url>")
        out.append("</urlset>")
        return "\n".join(out) + "\n"

    # -- RSS ----------------------------------------------------------------
    def feed(self) -> str:
        items_xml = []
        for i in sorted(self.d["items"], key=lambda x: x["date"], reverse=True):
            lane = LANES[i["lane"]]["name"]
            link = f"{SITE_URL}/{LANES[i['lane']]['page']}#{i['id']}"
            items_xml.append(f"""  <item>
    <title>{escape(f'[{lane}] ' + i["headline"])}</title>
    <link>{escape(link)}</link>
    <guid isPermaLink="false">{escape(i["id"])}-{i["date"]}</guid>
    <pubDate>{rfc822(i["date"])}</pubDate>
    <description>{escape(i["core"])} (Source: {escape(i["outlet"])} — {escape(i["url"])})</description>
  </item>""")
        build_date = rfc822(self.as_of[:10]) if self.as_of else ""
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>{escape(SITE_NAME)}</title>
  <link>{SITE_URL}/</link>
  <atom:link href="{SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
  <description>{escape(SITE_DESCRIPTION)}</description>
  <language>en</language>
  <lastBuildDate>{build_date}</lastBuildDate>
{chr(10).join(items_xml)}
</channel>
</rss>
"""


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build(out_dir: Path):
    root = Path(__file__).parent
    data = json.loads((root / "data.json").read_text(encoding="utf-8"))

    errors, warnings = validate(data)
    for w in warnings:
        print(f"  warning: {w}")
    if errors:
        for e in errors:
            print(f"  error:   {e}", file=sys.stderr)
        print(f"\nBUILD FAILED: {len(errors)} validation error(s) — nothing was written.",
              file=sys.stderr)
        sys.exit(1)

    site = Site(data)

    if out_dir.exists():
        shutil.rmtree(out_dir)
    (out_dir / "archive").mkdir(parents=True)

    # Past snapshots are content, not build artifacts: they live in ./archive
    # (committed to the repo) and are copied into the build output.
    src_archive = root / "archive"
    src_archive.mkdir(exist_ok=True)
    for f in sorted(src_archive.glob("*.html")):
        shutil.copy(f, out_dir / "archive" / f.name)

    # static assets
    shutil.copy(root / "assets" / "style.css", out_dir / "style.css")
    shutil.copy(root / "assets" / "theme.js", out_dir / "theme.js")

    def write(path: str, html: str):
        p = out_dir / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(html, encoding="utf-8")
        print(f"  wrote {path}  ({len(html.encode()):,} bytes)")

    # home
    write("index.html", site.page(
        path="index.html",
        title=f"{SITE_NAME} — AI-Cyber Intelligence",
        description=SITE_DESCRIPTION,
        body=site.home_body(),
        extra_head=site.home_jsonld()))

    # lanes
    for key, v in LANES.items():
        write(v["page"], site.page(
            path=v["page"],
            title=f"{v['name']} — {SITE_NAME}",
            description=f"{v['desc']} {site.coverage}, source-verified.",
            body=site.lane_body(key)))

    # week pages — one directory per Monday-to-Sunday week, two levels down, so
    # both the nav links and the shared assets need a two-step relative prefix.
    site.prefix = "../../"
    for n, w in enumerate(site.weeks):
        write(w["path"], site.page(
            path=w["path"],
            title=f'{w["label"]} — {SITE_NAME}',
            description=(f'{len(w["items"])} source-verified AI-cyber items from '
                         f'{w["label"]}: capability, policy, defense and attacks.'),
            body=site.week_body(n),
            asset_prefix="../../"))
    site.prefix = ""

    # archive index + about
    write("archive.html", site.page(
        path="archive.html", title=f"Archive — {SITE_NAME}",
        description="Dated snapshots of the Machine Speed board.",
        body=site.archive_body()))
    write("about.html", site.page(
        path="about.html", title=f"About — {SITE_NAME}",
        description=SITE_DESCRIPTION, body=site.about_body()))

    # RSS + crawl hints
    write("feed.xml", site.feed())
    write("sitemap.xml", site.sitemap())
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")

    # Custom domain. Emitted every build so an Actions deploy can never drop it.
    if CNAME:
        write("CNAME", CNAME + "\n")

    # dated snapshot of today's board (self-contained page in /archive)
    snap_date = (site.as_of or "")[:10]
    if snap_date:
        snap_name = f"archive/machine-speed-{snap_date}.html"
        banner = (f'<div class="note" style="margin-bottom:16px">Archived snapshot of the board as of '
                  f'{fmt_date(snap_date)}. <a href="../index.html">Back to the live board ↗</a></div>')
        site.prefix = "../"
        snap_body = banner + site.home_body()
        site.prefix = ""
        snap_html = site.page(
            path=snap_name,
            title=f"{SITE_NAME} board — {fmt_date(snap_date)} snapshot",
            description=f"Archived Machine Speed board, {fmt_date(snap_date)}.",
            body=snap_body,
            asset_prefix="../")
        write(snap_name, snap_html)
        # also save into the source archive so it gets committed and survives rebuilds
        (src_archive / Path(snap_name).name).write_text(snap_html, encoding="utf-8")

    # Newsletter draft — written into the repo (not dist/) for a human to publish.
    if snap_date:
        news_dir = root / "newsletter"
        news_dir.mkdir(exist_ok=True)
        draft = news_dir / f"machine-speed-{snap_date}.md"
        draft.write_text(site.newsletter_draft(), encoding="utf-8")
        print(f"  wrote newsletter/{draft.name}  (draft only — nothing is sent)")

    counts = " · ".join(f"{v['name'].lower()} {len(site.lane_items(k))}"
                        for k, v in LANES.items())
    print(f"\nBuild complete → {out_dir}")
    print(f"  {len(data['items'])} items ({counts}), "
          f"{len(site.fresh_items())} in the 48h strip, "
          f"{len(data['watchlist'])} watchlist threads")
    print(f"  site: {SITE_URL}")
    if not SUBSTACK_URL:
        print("  note: SUBSTACK_URL is unset — subscribe links are hidden. "
              "Set it at the top of build.py to turn them on.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist", help="output directory (default: dist)")
    args = ap.parse_args()
    build(Path(args.out).resolve())
