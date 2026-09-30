"""
Machine Speed — the front page and the topic pages.

The board holds every item at the same weight, which makes it a good record and
a hard read. This module gives readers a way in that is short at the top and
complete underneath:

    /                 This week (the editor's picks, or the newest items until
                      picks are chosen), the topics, a search box, then one
                      card per week, newest first
    /watchlist/       the six topics, each with its latest watchlist status,
                      plus the watchlist threads no topic covers
    /topic/<id>/      one topic: its watchlist threads, then its items week by
                      week, one line each
    /search/          search every item (assets/search.js over data/items.json)

Every page carries a search box in its header that leads to /search/. Everything
is derived from data.json (`weekly`, `items[].topics`, `watchlist[].topic`) and
topics.json. Nothing here adds a claim.

Python 3 standard library only, like build.py.
"""

from datetime import date, timedelta
from html import escape

TOPICS_URL = "watchlist/"     # the six topics; "Watchlist" in the navigation
SEARCH_URL = "search/"
PICKS_MAX = 5          # This week is a short read by design; more warns
LATEST_WHEN_NO_PICKS = 5
CARD_HEADLINES = 3

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _d(iso: str) -> date:
    return date.fromisoformat(iso[:10])


def _short(dt: date) -> str:
    return f"{MONTHS[dt.month - 1]} {dt.day}"


def _monday(dt: date) -> date:
    return dt - timedelta(days=dt.weekday())


# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------

def validate(d: dict, topics: list = ()):
    errors, warnings = [], []
    known = {t.get("id") for t in topics}
    ids = {i.get("id") for i in d.get("items", [])}
    for w in d.get("watchlist", []):
        for iid in w.get("items", []):
            if iid not in ids:
                warnings.append(f"watchlist thread '{w.get('thread')}': item '{iid}' is not on the board")
        if w.get("topic") and w["topic"] not in known:
            errors.append(f"watchlist thread '{w.get('thread')}': topic '{w['topic']}' is not in topics.json")
    ids = {i.get("id") for i in d.get("items", [])}
    for it in d.get("items", []):
        if "key" in it and not isinstance(it["key"], bool):
            errors.append(f"item {it.get('id')}: key must be true or false")
    seen = set()
    for n, wk in enumerate(d.get("weekly", [])):
        where = f"weekly[{n}]"
        try:
            mon = date.fromisoformat(wk.get("week", ""))
            if mon.weekday() != 0:
                errors.append(f"{where}: week must be the Monday that starts the week")
        except ValueError:
            errors.append(f"{where}: week must be YYYY-MM-DD")
            continue
        if wk["week"] in seen:
            errors.append(f"{where}: week {wk['week']} appears twice")
        seen.add(wk["week"])
        picks = wk.get("picks", [])
        if not picks:
            errors.append(f"{where}: no picks")
        if len(picks) > PICKS_MAX:
            warnings.append(f"{where}: {len(picks)} picks — This week is meant to be a "
                            f"{PICKS_MAX}-item read")
        for p in picks:
            if p.get("item") not in ids:
                errors.append(f"{where}: pick '{p.get('item')}' is not on the board")
            if not p.get("why"):
                errors.append(f"{where}: pick '{p.get('item')}' needs a 'why' line")
    return errors, warnings


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

class Layers:
    def __init__(self, d: dict, lanes: dict, ins, topics: list, weeks: list):
        self.d = d
        self.lanes = lanes
        self.run = _d(d["updatedISO"])
        self.by_id = {i["id"]: i for i in d.get("items", [])}
        self.weeks = weeks                      # build.py's week buckets, newest first
        self.picks = {w["week"]: w for w in d.get("weekly", [])}
        lag = {r["id"]: r for r in ins.threads()}
        self.topics = []
        for tp in topics:
            items = sorted((i for i in d.get("items", []) if tp["id"] in i.get("topics", [])),
                           key=lambda i: i["date"], reverse=True)
            watch = sorted((w for w in d.get("watchlist", []) if w.get("topic") == tp["id"]),
                           key=lambda w: w.get("changed") or "", reverse=True)
            self.topics.append(dict(tp, items=items, lag=lag.get(tp["id"]), watch=watch))
        known = {tp["id"] for tp in topics}
        self.other_watch = sorted((w for w in d.get("watchlist", []) if w.get("topic") not in known),
                                  key=lambda w: w.get("changed") or "", reverse=True)

    @property
    def this_week(self):
        """The newest week that has items — on a Monday that is still last week."""
        return self.weeks[0] if self.weeks else None


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _pill(lanes, k):
    v = lanes[k]
    return f'<span class="lanepill {v["pill"]}">{v["name"]}</span>'


def _item_link(site, it):
    return f'{site.prefix}{site.lanes_meta[it["lane"]]["page"]}#{escape(it["id"])}'


def _week_link(site, w):
    return f'{site.prefix}week/{w["monday"]}/'


def picks_list(site, L, wk) -> str:
    rows = []
    for n, p in enumerate(wk["picks"], 1):
        it = L.by_id[p["item"]]
        rows.append(f'<li class="pick"><span class="pn">{n}</span><div>'
                    f'<a class="ph" href="{_item_link(site, it)}">{escape(it["headline"])}</a>'
                    f'<p class="pw">{escape(p["why"])}</p>'
                    f'<span class="pm">{_pill(L.lanes, it["lane"])} {escape(it["outlet"])} · '
                    f'{_short(_d(it["date"]))}</span></div></li>')
    return f'<ol class="picks">{"".join(rows)}</ol>'


def latest_list(site, L, items) -> str:
    rows = []
    for it in items:
        rows.append(f'<li class="pick nopn"><div>'
                    f'<a class="ph" href="{_item_link(site, it)}">{escape(it["headline"])}</a>'
                    f'<p class="pw">{escape(it["core"])}</p>'
                    f'<span class="pm">{_pill(L.lanes, it["lane"])} {escape(it["outlet"])} · '
                    f'{_short(_d(it["date"]))}</span></div></li>')
    return f'<ol class="picks">{"".join(rows)}</ol>'


def _lanebar(L, items) -> str:
    """A thin bar split by lane, so a week's mix reads at a glance."""
    n = len(items) or 1
    segs, key = [], []
    for k, v in L.lanes.items():
        c = sum(1 for i in items if i["lane"] == k)
        if c:
            segs.append(f'<i style="flex:{c};background:var(--{k}-mark)" title="{v["name"]}: {c}"></i>')
            key.append(f'{v["name"]} {c}')
    return (f'<span class="wbar" role="img" aria-label="{escape(", ".join(key))}">{"".join(segs)}</span>'
            f'<span class="wkey">{escape(" · ".join(key))}</span>')


def week_card(site, L, w) -> str:
    picks = L.picks.get(w["monday"])
    if picks:
        heads = [L.by_id[p["item"]] for p in picks["picks"]][:CARD_HEADLINES]
        label = "Picks"
    else:
        keyed = [i for i in w["items"] if i.get("key")]
        heads = (keyed or w["items"])[:CARD_HEADLINES]
        label = "Key items" if keyed else "Newest"
    lines = "".join(f'<li>{_pill(L.lanes, i["lane"])}<span>{escape(i["headline"])}</span></li>'
                    for i in heads)
    return (f'<a class="wcard" href="{_week_link(site, w)}">'
            f'<span class="wt">Week of {_short(_d(w["monday"]))}<b>{len(w["items"])} items</b></span>'
            f'{_lanebar(L, w["items"])}'
            f'<span class="wl">{label}</span><ul>{lines}</ul>'
            f'<span class="wgo">Read the week →</span></a>')


def topic_chip(site, t) -> str:
    return (f'<a class="topic" href="{site.prefix}topic/{t["id"]}/">'
            f'<span class="tn">{escape(t["name"])}<b>{len(t["items"])}</b></span>'
            f'<span class="td">{escape(t["definition"])}</span></a>')


def nav_search(prefix: str) -> str:
    """The search box every page carries in its header."""
    return (f'<form class="navsearch" action="{prefix}{SEARCH_URL}" method="get" role="search">'
            f'<input name="q" type="search" placeholder="Search the board" aria-label="Search the board">'
            f'</form>')


def watch_table(rows, with_thread=True) -> str:
    if not rows:
        return ""
    out = []
    for w in rows:
        when = (f'<time datetime="{w["changed"]}">{_short(_d(w["changed"]))}</time>' if w.get("changed") else "—")
        out.append(f'<tr><td class="thread">{escape(w["thread"])}</td>'
                   f'<td class="status">{escape(w["status"])}</td><td class="when">{when}</td></tr>')
    return ('<table class="watch"><thead><tr><th scope="col">Thread</th><th scope="col">Current status</th>'
            '<th scope="col">Last changed</th></tr></thead><tbody>' + "".join(out) + '</tbody></table>')


def _clip(text: str, n: int) -> str:
    return text if len(text) <= n else text[: n - 1].rsplit(" ", 1)[0] + "…"


def this_week_banner(site, L, w, picked, conf_labels) -> str:
    """This week, in the same banner as Explore's "New to the board" carousel.

    Every slide is pre-rendered, so a reader without JavaScript gets them all,
    stacked. assets/home.js then turns the stack into the carousel: one slide
    at a time, arrows, the numbered thumbs and the tick bar, advancing every
    seven seconds unless the reader is hovering, focused inside it, or has
    asked for reduced motion.
    """
    if picked:
        rows = [(L.by_id[p["item"]], p["why"]) for p in picked["picks"]]
        title = f'THIS WEEK &middot; WEEK OF {_short(_d(w["monday"])).upper()}'
    else:
        rows = [(it, None) for it in w["items"][:LATEST_WHEN_NO_PICKS]]
        title = f'LATEST &middot; WEEK OF {_short(_d(w["monday"])).upper()}'
    n = len(rows)
    slides, thumbs, ticks = [], [], []
    for j, (it, why) in enumerate(rows):
        k = it["lane"]
        ln = f"--ln:var(--x-{k});--ln-soft:var(--{k}-soft);--ln-text:var(--{k})"
        link = _item_link(site, it)
        body = (f'<p><b class="why">Why it matters.</b> {escape(why)}</p>' if why
                else f'<p>{escape(_clip(it["core"], 340))}</p>')
        slides.append(
            f'<div class="msx-carslide" style="{ln}" data-i="{j}">'
            f'<div class="msx-carkick"><i>{escape(L.lanes[k]["name"].upper())}</i>'
            f'<time datetime="{it["date"]}">{_short(_d(it["date"])).upper()}</time></div>'
            f'<h3><a href="{link}">{escape(_clip(it["headline"], 104))}</a></h3>{body}'
            f'<div class="msx-carsrc"><span class="msx-conf">{escape(conf_labels.get(it["confidence"], it["confidence"]))}</span>'
            f'<a class="msx-src" href="{escape(it["url"], quote=True)}" target="_blank" rel="noopener">{escape(it["outlet"])} &#8599;</a>'
            f'<a class="msx-src" href="{link}">on the board &#8594;</a></div></div>')
        thumbs.append(
            f'<button class="msx-carthumb{" on" if j == 0 else ""}" data-i="{j}" type="button" '
            f'aria-current="{"true" if j == 0 else "false"}" style="{ln}">'
            f'<span class="t"><i></i>{j + 1:02d}</span>'
            f'<span class="h">{escape(_clip(it["headline"], 46))}</span></button>')
        ticks.append(f'<i class="{"on" if j == 0 else ""}" style="{ln}"></i>')
    return (f'<div class="msx msx-carpanel hcar" data-hcar>'
            f'<div class="msx-carhead"><span class="msx-cartitle"><i></i>{title}</span>'
            f'<span class="msx-carnav"><span class="mono c">1 / {n}</span>'
            f'<button class="msx-carbtn" data-step="-1" type="button" aria-label="Previous">&#8592;</button>'
            f'<button class="msx-carbtn" data-step="1" type="button" aria-label="Next">&#8594;</button></span></div>'
            f'<div class="hcar-slides">{"".join(slides)}</div>'
            f'<div class="msx-carticks">{"".join(ticks)}</div>'
            f'<div class="msx-carthumbs" style="grid-template-columns:repeat({min(n, 6)},minmax(0,1fr))">'
            f'{"".join(thumbs)}</div></div>')


def _words(n: int) -> str:
    return (["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"][n]
            if 0 <= n <= 10 else str(n))


def guide_bar(site, L, w) -> str:
    """The strip under the banner that says where to go next and what each
    place is: the rest of this week, the Watchlist, the Briefs."""
    cells = []
    lo, hi = w["items"][-1]["date"], w["items"][0]["date"]
    cells.append(
        f'<a class="gcell" href="{_week_link(site, w)}"><span class="gl">This week</span>'
        f'<span class="gd">Everything the board logged, by lane.</span>'
        f'<span class="gm">{len(w["items"])} items · {_short(_d(lo))} – {_short(_d(hi))}</span>'
        f'<span class="ga">&#8594;</span></a>')
    live = [t for t in L.topics if t["items"]]
    moved = sorted((x for t in live for x in t["watch"] if x.get("changed")),
                   key=lambda x: x["changed"], reverse=True)
    meta = (f'Last moved: {escape(moved[0]["thread"])} · {_short(_d(moved[0]["changed"]))}'
            if moved else f'{len(live)} topics')
    cells.append(
        f'<a class="gcell" href="{site.prefix}{TOPICS_URL}"><span class="gl">Watchlist</span>'
        f'<span class="gd">The {_words(len(live))} running stories the board follows, from lab evaluation '
        f'incidents to attacks on AI systems.</span>'
        f'<span class="gm">{meta}</span><span class="ga">&#8594;</span></a>')
    if site.briefs:
        b = site.briefs[0]
        cells.append(
            f'<a class="gcell" href="{site.prefix}briefs/"><span class="gl">Briefs</span>'
            f'<span class="gd">Major incidents laid out stage by stage, every stage sourced.</span>'
            f'<span class="gm">{len(site.briefs)} briefs · latest: {escape(_clip(b["title"], 60))}</span>'
            f'<span class="ga">&#8594;</span></a>')
    return f'<nav class="guide" aria-label="Where to go next">{"".join(cells)}</nav>'


def home_body(site, L, explore_page: str, conf_labels: dict) -> str:
    w = L.this_week
    if not w:
        return f'{site.nav("index.html", lanes=False)}<p class="lede">Nothing on the board yet.</p>{site.footer()}'
    picked = L.picks.get(w["monday"])
    top = this_week_banner(site, L, w, picked, conf_labels)
    note = f'<p class="lede">{escape(picked["note"])}</p>' if picked and picked.get("note") else ""
    more = guide_bar(site, L, w)
    cards = "".join(week_card(site, L, x) for x in L.weeks)
    topics = "".join(topic_chip(site, t) for t in L.topics if t["items"])
    return f"""{site.nav("index.html", lanes=False)}

  <header class="pagehead board nohead">
    <p class="thesis">AI cyber capability against the defense and policy lag, tracked daily.</p>
    <p class="stampline"><span class="dot"></span>Updated
      <time datetime="{site.as_of}">{escape(site.d.get("updatedDisplay", ""))}</time>
      &nbsp;&middot;&nbsp; {len(site.d["items"])} source-verified items since
      <time datetime="{site.cov_start}">{_short(_d(site.cov_start))}</time></p>
  </header>

  <section class="block thisweek">
    {note}{top}{more}
  </section>

  <section class="block"><h2 class="blockhead">Every week</h2>
    <div class="wgrid">{cards}</div>
  </section>

  {site.subscribe_block(compact=True)}

  {site.footer()}"""


def watch_card(site, t) -> str:
    """A topic on the Watchlist page: definition, then its newest status line."""
    latest = t["watch"][0] if t["watch"] else None
    status = ""
    if latest:
        when = _short(_d(latest["changed"])) if latest.get("changed") else ""
        status = (f'<span class="ws"><b>{escape(latest["thread"])}{" · " + when if when else ""}.</b> '
                  f'{escape(_clip(latest["status"], 260))}</span>')
    return (f'<a class="topic wcard2" href="{site.prefix}topic/{t["id"]}/">'
            f'<span class="tn">{escape(t["name"])}<b>{len(t["items"])} items</b></span>'
            f'<span class="td">{escape(t["definition"])}</span>{status}'
            f'<span class="wgo">Open the topic →</span></a>')


def also_watching(site, L, rows) -> str:
    """Threads outside the topics: one line each; a click opens the thread's
    items, each linking to its original source and to its card on the board.
    A thread with no `items` falls back to its status line."""
    if not rows:
        return ""
    out = []
    for w in rows:
        its = sorted((L.by_id[i] for i in w.get("items", []) if i in L.by_id),
                     key=lambda i: i["date"], reverse=True)
        when = (f'<time datetime="{w["changed"]}">{_short(_d(w["changed"]))}</time>' if w.get("changed") else "")
        n = f'<em>{len(its)}</em>' if its else ""
        if its:
            body = "<ul class=\"awitems\">" + "".join(
                f'<li><time datetime="{it["date"]}">{_short(_d(it["date"]))}</time>'
                f'{_pill(L.lanes, it["lane"])}'
                f'<a class="h" href="{_item_link(site, it)}">{escape(it["headline"])}</a>'
                f'<a class="src" href="{escape(it["url"], quote=True)}" target="_blank" rel="noopener">'
                f'{escape(it["outlet"])} &#8599;</a></li>' for it in its) + "</ul>"
        else:
            body = f'<p>{escape(w["status"])}</p>'
        out.append(f'<details class="aw"><summary><span>{escape(w["thread"])}</span>{n}{when}</summary>{body}</details>')
    return f'<div class="awlist">{"".join(out)}</div>'


def topics_body(site, L) -> str:
    cards = "".join(topic_chip(site, t) for t in L.topics if t["items"])
    other = also_watching(site, L, L.other_watch)
    return f"""{site.nav(TOPICS_URL)}

  <header class="pagehead">
    <h1>Watchlist</h1>
    <div class="sub">The six stories the board is following. Open one for its latest status and
      everything on it, week by week.</div>
  </header>

  <div class="topics wide">{cards}</div>

  {f'<section class="block"><h2 class="blockhead">Also watching</h2><p class="lede">Running threads outside the six topics. Open one for its items and their original sources.</p>{other}</section>' if other else ""}

  {site.footer()}"""


def topic_body(site, L, t) -> str:
    lanes = L.lanes
    by_week = {}
    for it in t["items"]:
        by_week.setdefault(_monday(_d(it["date"])), []).append(it)
    blocks = []
    for mon in sorted(by_week, reverse=True):
        its = by_week[mon]
        rows = "".join(
            f'<li class="crow{" key" if it.get("key") else ""}"><time datetime="{it["date"]}">{_short(_d(it["date"]))}</time>'
            f'{_pill(lanes, it["lane"])}<a href="{_item_link(site, it)}">{escape(it["headline"])}</a></li>'
            for it in its)
        blocks.append(f'<h4 class="weekhead">Week of {_short(mon)}<span>{len(its)}</span></h4>'
                      f'<ul class="crows">{rows}</ul>')
    r = t["lag"]
    # Response-lag tiles are held back with the Findings page; the numbers are
    # still computed (insights.py) and return with SHOW_FINDINGS.
    tiles = [(str(len(t["items"])), "Items"),
             (_short(_d(t["items"][-1]["date"])) if t["items"] else "—", "First"),
             (_short(_d(t["items"][0]["date"])) if t["items"] else "—", "Latest")]
    tiles_html = "".join(f'<div class="stat"><div class="n">{n}</div><div class="l">{escape(l)}</div></div>'
                         for n, l in tiles)
    return f"""{site.nav(TOPICS_URL)}

  <header class="pagehead">
    <h1>{escape(t["name"])}</h1>
    <div class="sub">{escape(t["definition"])}</div>
    <p class="note" style="margin-top:8px"><a href="{site.prefix}{TOPICS_URL}">Back to the Watchlist</a></p>
  </header>

  <div class="stats">{tiles_html}</div>

  {f'<section class="block"><h2 class="blockhead">Threads in this topic</h2>{also_watching(site, L, t["watch"])}</section>' if t["watch"] else ""}

  <section class="block"><h2 class="blockhead">Items, newest week first</h2>
    <div class="lanes lanes-single"><section class="lane tlist">{"".join(blocks) or '<p class="lede">No items yet.</p>'}</section></div>
  </section>

  {site.footer()}"""


def search_body(site, lanes: dict, topics: list) -> str:
    cfg = {"lanes": {k: {"name": v["name"], "page": site.prefix + v["page"], "pill": v["pill"]}
                     for k, v in lanes.items()},
           "topics": {t["id"]: t["name"] for t in topics},
           "data": site.prefix + "data/items.json"}
    import json as _json
    blob = _json.dumps(cfg, separators=(",", ":")).replace("<", "\\u003c")
    chips = "".join(f'<button type="button" class="schip" data-lane="{k}" aria-pressed="false">'
                    f'<i style="background:var(--{k}-mark)"></i>{v["name"]}</button>' for k, v in lanes.items())
    return f"""{site.nav(SEARCH_URL)}

  <header class="pagehead">
    <h1>Search</h1>
    <div class="sub">Every item on the board: headlines, summaries, sources, organisations and topics.</div>
  </header>

  <form class="bigsearch" action="" method="get" role="search">
    <input id="sq" name="q" type="search" placeholder="langflow, PLC, npm, CVE-2026…" aria-label="Search the board" autocomplete="off">
    <div class="schips" aria-label="Limit to a lane">{chips}</div>
  </form>

  <p class="scount" id="scount" aria-live="polite">Loading the board…</p>
  <ol class="sresults" id="sresults"></ol>
  <noscript><p class="lede">Search needs JavaScript. Every item is also on the lane pages and the week pages.</p></noscript>

  <script id="search-config" type="application/json">{blob}</script>

  {site.footer()}"""
