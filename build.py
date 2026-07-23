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
from datetime import datetime, timedelta
from html import escape
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration — edit these for your deployment
# ---------------------------------------------------------------------------

SITE_URL = "https://machinespeed.example.com"   # no trailing slash; set to your real domain
SITE_NAME = "Machine Speed"
SITE_TAGLINE = "AI-Cyber Intel"
SITE_DESCRIPTION = ("A daily, source-verified intelligence board on frontier AI "
                    "cyber capability and the defense & policy lag around it.")
NEW_WINDOW_DAYS = 2   # items this recent get the "New" badge / 48h strip

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


class Site:
    def __init__(self, data: dict):
        self.d = data
        self.as_of = data.get("updatedISO", "")
        self.prefix = ""  # set to "../" while rendering pages inside /archive

    # -- item queries -------------------------------------------------------
    def lane_items(self, key: str):
        items = [i for i in self.d["items"] if i["lane"] == key]
        return sorted(items, key=lambda i: i["date"], reverse=True)

    def fresh_items(self):
        fresh = [i for i in self.d["items"]
                 if days_ago(i["date"], self.as_of) <= NEW_WINDOW_DAYS]
        return sorted(fresh, key=lambda i: i["date"], reverse=True)

    def is_new(self, item) -> bool:
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

    def sources_block(self) -> str:
        seen, rows = set(), []
        for i in self.d["items"]:
            if i["url"] in seen:
                continue
            seen.add(i["url"])
            host = i["url"].split("/")[2].removeprefix("www.")
            rows.append(
                f'<li>{escape(i["headline"])} — <span class="outlet">{escape(i["outlet"])}, '
                f'{fmt_date(i["date"])}.</span> '
                f'<a href="{escape(i["url"], quote=True)}" target="_blank" rel="noopener">{escape(host)} ↗</a></li>')
        return ('<section class="block"><h2 class="blockhead">Sources</h2>'
                '<ol class="sources">' + "\n".join(rows) + "</ol></section>")

    def watchlist_block(self) -> str:
        rows = []
        for w in self.d["watchlist"]:
            changed = (f'<time datetime="{w["changed"]}">{fmt_date(w["changed"])}</time>'
                       if w.get("changed") else "—")
            rows.append(f'<tr><td class="thread">{escape(w["thread"])}</td>'
                        f'<td>{escape(w["status"])}</td>'
                        f'<td class="when">{changed}</td></tr>')
        return ('<section class="block"><h2 class="blockhead">Still watching</h2>'
                '<table><thead><tr><th scope="col">Thread</th><th scope="col">Current status</th>'
                '<th scope="col">Last changed</th></tr></thead><tbody>'
                + "\n".join(rows) + "</tbody></table></section>")

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
        return (f'<div class="chartcard"><h3>Coverage by lane · rolling 7-day</h3>'
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
        canonical = f"{SITE_URL}/{'' if path == 'index.html' else path}"
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
            items = self.lane_items(k)
            lanes_html.append(
                f'<section class="lane"><h3><span class="barv" style="background:var({v["var"]})"></span>'
                f'{v["name"]}<span class="count">{len(items)} items · 7-day</span>'
                f'<a class="more" href="{self.prefix}{v["page"]}">view lane ↗</a></h3>'
                + "".join(self.item_card(i) for i in items) + "</section>")

        return f"""{self.nav("index.html")}

  <header class="pagehead">
    <h1>The capability-vs-defense gap, tracked daily</h1>
    <div class="sub">Frontier AI cyber capability against the defense &amp; policy lag — a rolling
      7-day board, source-verified, skimmable in 60 seconds.</div>
    <div class="stamp"><span class="dot"></span>Last updated:
      <time datetime="{d.get("updatedISO", "")}">{escape(d.get("updatedDisplay", ""))}</time></div>
    <div class="note">{escape(d.get("judgmentNote", ""))}</div>
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

  {self.watchlist_block()}

  {self.sources_block()}

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

    # -- lane pages ---------------------------------------------------------
    def lane_body(self, key: str) -> str:
        v = LANES[key]
        items = self.lane_items(key)
        return f"""{self.nav(v["page"])}

  <header class="pagehead">
    <h1>{v["name"]}<span class="lanerule" style="background:var({v["var"]})"></span></h1>
    <div class="sub">{escape(v["desc"])} Rolling 7-day window · {len(items)} items.</div>
    <div class="stamp"><span class="dot"></span>Last updated:
      <time datetime="{self.as_of}">{escape(self.d.get("updatedDisplay", ""))}</time></div>
  </header>

  <div class="lanes lanes-single">
    <section class="lane"><h3><span class="barv" style="background:var({v["var"]})"></span>
      {v["name"]}<span class="count">{len(items)} items · rolling 7-day</span></h3>
      {"".join(self.item_card(i) for i in items)}
    </section>
  </div>

  {self.sources_block()}

  {self.footer()}"""

    # -- archive index ------------------------------------------------------
    def archive_body(self) -> str:
        cards = "".join(
            f'<a href="{escape(a["file"], quote=True)}"><span class="d">{fmt_date(a["date"])}</span>'
            f'<span class="m">{a.get("items", "")} items — {escape(a.get("note", ""))}</span></a>'
            for a in sorted(self.d.get("archives", []), key=lambda a: a["date"], reverse=True))
        return f"""{self.nav("archive.html")}

  <header class="pagehead">
    <h1>Archive</h1>
    <div class="sub">Dated snapshots of the board, one per publishing run.</div>
  </header>

  <div class="arch">{cards}</div>

  {self.footer()}"""

    # -- about --------------------------------------------------------------
    def about_body(self) -> str:
        paras = "".join(f"<p>{escape(p)}</p>" for p in self.d.get("about", []))
        return f"""{self.nav("about.html")}

  <header class="pagehead"><h1>About {escape(SITE_NAME)}</h1></header>
  <div class="prose">{paras}</div>

  {self.footer()}"""

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
        (out_dir / path).write_text(html, encoding="utf-8")
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
            description=f"{v['desc']} Rolling 7-day, source-verified.",
            body=site.lane_body(key)))

    # archive index + about
    write("archive.html", site.page(
        path="archive.html", title=f"Archive — {SITE_NAME}",
        description="Dated snapshots of the Machine Speed board.",
        body=site.archive_body()))
    write("about.html", site.page(
        path="about.html", title=f"About — {SITE_NAME}",
        description=SITE_DESCRIPTION, body=site.about_body()))

    # RSS
    write("feed.xml", site.feed())

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

    print(f"\nBuild complete → {out_dir}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist", help="output directory (default: dist)")
    args = ap.parse_args()
    build(Path(args.out).resolve())
