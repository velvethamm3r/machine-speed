"""
Machine Speed — the front page and the topic pages.

The board holds every item at the same weight, which makes it a good record and
a hard read. This module gives readers a way in that is short at the top and
complete underneath:

    /                 the front page, set like a broadsheet: a dateline, a
                      contents column that says what each layer of the site is
                      for (the board, the weeks, the Watchlist, the Briefs, So
                      What), this week's lead item and the next few, the So What
                      pages, then the newest weeks as cards with the rest in
                      the Archive
    /so-what/         the pages that step back from the record (build.py's
                      SO_WHAT_PAGES), with the same descriptions the front page
                      uses
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
FRONT_WEEK_CARDS = 3   # week cards on the front page, in a fixed three-up; the Archive has them all
LEAD_FOLLOWERS = 4     # items set two-up under this week's lead

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
    for t in topics:
        r = t.get("reading")
        if r is None:
            continue
        if not isinstance(r, dict) or not isinstance(r.get("level"), int) or not 0 <= r["level"] <= 4:
            errors.append(f"topic '{t.get('id')}': reading.level must be an integer 0-4")
        elif not r.get("why"):
            warnings.append(f"topic '{t.get('id')}': reading has no 'why' — the face will show a level with no reason")
        if isinstance(r, dict) and r.get("asOf"):
            try:
                _d(r["asOf"])
            except ValueError:
                errors.append(f"topic '{t.get('id')}': reading.asOf is not a YYYY-MM-DD date")
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


def _lane_kick(L, k, when: str = "") -> str:
    """The small uppercase lane label in its lane colour, with an optional date."""
    v = L.lanes[k]
    t = f' <time datetime="{when}">{_short(_d(when))}</time>' if when else ""
    return f'<span class="kick" style="color:var({v["var"]})">{escape(v["name"])}{t}</span>'


def contents_column(site, L, w) -> str:
    """The front page's contents column: what each layer of the site is for,
    in the reader's terms, not the site's. The numbers stay small and at the
    end; the reason to click comes first."""
    live = [t for t in L.topics if t["items"]]
    moved = sorted((x for t in live for x in t["watch"] if x.get("changed")),
                   key=lambda x: x["changed"], reverse=True)
    rows = [
        ("I", _week_link(site, w), "The Board",
         "What happened, and who said so. Every claim traced to a source you can open."),
        ("II", f'{site.prefix}{ARCHIVE}', "Weeks",
         "What a week of this actually looks like, lane by lane."),
        ("III", f'{site.prefix}{TOPICS_URL}', "Watchlist",
         f"The {_words(len(live))} stories that keep moving. Check here to know what changed."
         + (f" Last moved {_short(_d(moved[0]['changed']))}." if moved else "")),
    ]
    if site.briefs:
        rows.append(("IV", f'{site.prefix}briefs/', "Briefs",
                     "How one incident unfolded, stage by stage, every stage sourced."))
    if site.so_what:
        rows.append(("V" if site.briefs else "IV", f'{site.prefix}so-what/', "So What",
                     "Step back. What the record adds up to, where the money and the rules go, "
                     "and what has precedent."))
    out = ['<nav class="ways" aria-label="Where to go">',
           '<p class="waysin">Five ways in, from the ground up.</p>'
           if len(rows) == 5 else '<p class="waysin">Ways in, from the ground up.</p>']
    for n, href, name, what in rows:
        last = " last" if name == "So What" else ""
        out.append(f'<a class="way{last}" href="{href}"><span class="wn">{n}</span>'
                   f'<span class="wb"><span class="wt">{name}</span>'
                   f'<span class="wd">{escape(what)}</span></span></a>')
    out.append('</nav>')
    return "".join(out)


ARCHIVE = "archive/"


def lead_block(site, L, w, picked, conf_labels) -> str:
    """This week's lead, set large, with the next few items two-up under a rule.

    The picks decide the order when the editor has chosen them; otherwise the
    newest items lead. Nothing here needs JavaScript."""
    if picked:
        rows = [L.by_id[p["item"]] for p in picked["picks"]]
    else:
        rows = w["items"][:1 + LEAD_FOLLOWERS]
    lead, rest = rows[0], rows[1:1 + LEAD_FOLLOWERS]
    link = _item_link(site, lead)
    conf = escape(conf_labels.get(lead["confidence"], lead["confidence"]))
    out = [f'<a class="lead" href="{link}">{_lane_kick(L, lead["lane"], lead["date"])}'
           f'<span class="lh">{escape(lead["headline"])}</span>'
           f'<span class="ls">{escape(_clip(lead["core"], 300))}</span>'
           f'<span class="lm">{conf} · {escape(lead["outlet"])} &#8599; · on the board &#8594;</span></a>']
    if rest:
        out.append('<div class="twoup">')
        for it in rest:
            out.append(f'<a class="two" href="{_item_link(site, it)}">{_lane_kick(L, it["lane"])}'
                       f'<span class="th">{escape(it["headline"])}</span></a>')
        out.append('</div>')
    out.append(f'<a class="more" href="{_week_link(site, w)}">Everything this week, by lane &#8594;</a>')
    return "".join(out)


def so_what_cards(site) -> str:
    """The So What pages, as the front page and /so-what/ both show them."""
    cards = []
    for p in site.so_what:
        colour = f' style="color:var(--{p["lane"]})"' if p.get("lane") else ""
        cards.append(f'<a class="sw" href="{site.prefix}{p["url"]}">'
                     f'<span class="kick"{colour}>{escape(p["kicker"])}</span>'
                     f'<span class="swt">{escape(p["title"])}</span>'
                     f'<span class="swd">{escape(p["blurb"])}</span></a>')
    return "".join(cards)


def home_body(site, L, explore_page: str, conf_labels: dict) -> str:
    w = L.this_week
    if not w:
        return f'{site.nav("index.html", lanes=False)}<p class="lede">Nothing on the board yet.</p>{site.footer()}'
    picked = L.picks.get(w["monday"])
    note = f'<p class="lede">{escape(picked["note"])}</p>' if picked and picked.get("note") else ""
    counts = {k: sum(1 for i in w["items"] if i["lane"] == k) for k in L.lanes}
    lanes = " · ".join(f'<span style="color:var({L.lanes[k]["var"]})">{L.lanes[k]["name"]} {n}</span>'
                       for k, n in counts.items() if n)
    cards = "".join(week_card(site, L, x) for x in L.weeks[:FRONT_WEEK_CARDS])
    sowhat = (f'<section class="block sowhat"><p class="swhead"><a href="{site.prefix}so-what/">So What</a>'
              f'<em>what the record adds up to, and what has precedent</em></p>'
              f'<div class="swgrid">{so_what_cards(site)}</div></section>') if site.so_what else ""
    return f"""{site.nav("index.html", lanes=False)}

  <p class="dateline"><span><span class="dot"></span>Updated
      <time datetime="{site.as_of}">{escape(site.d.get("updatedDisplay", ""))}</time>
      &nbsp;&middot;&nbsp; {len(site.d["items"])} source-verified items since
      <time datetime="{site.cov_start}">{_short(_d(site.cov_start))}</time></span>
    <span>Week of {_short(_d(w["monday"]))} &middot; {len(w["items"])} items &middot; {lanes}</span></p>

  <section class="front">
    {contents_column(site, L, w)}
    <div class="frontlead">{note}{lead_block(site, L, w, picked, conf_labels)}</div>
  </section>

  {sowhat}

  <section class="block"><p class="blockhead rw">Recent weeks
    <a href="{site.prefix}{ARCHIVE}">All {len(L.weeks)} weeks in the Archive &#8594;</a></p>
    <div class="wgrid front">{cards}</div>
  </section>

  {site.subscribe_block(compact=True)}

  {site.footer()}"""


def so_what_body(site) -> str:
    """/so-what/: the pages that step back from the record."""
    return f"""{site.nav("so-what/", lanes=False)}
  <header class="pagehead">
    <h1>So What</h1>
    <p class="sub wide">The board, the weeks, the Watchlist and the Briefs are the record: an item, a week,
      a story, an incident. These pages step back from it and ask what it adds up to, where the money and
      the rules actually go, and what has precedent.</p>
  </header>
  <div class="swgrid tall">{so_what_cards(site)}</div>
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


# Emblems: a cast of six, one character per story, all drawn in the same hand:
# a rounded body filled with the lane's soft tint, a thick ink outline, dot
# eyes and a mouth that says how the story is going. Keyed by topic id; a story
# without one gets a plain mark. All drawn here, nothing loaded. Classes:
# .bd body fill, .ac accent stroke, .af accent fill, .ey eyes, .mo mouth.
# -- The scale ---------------------------------------------------------------
# Each story's face is a reading, not a decoration. It follows the Gap Map's
# own measure: over the trailing four weeks, new problems (capability and
# attack items) against answers (policy, defense, markets). Same bands as the
# Gap Map's verdicts, so the face never says anything the rest of the site
# does not. Level 0 is a story with no new problems at all.
PACE_WEEKS = 4
PROBLEM_LANES = ("cap", "atk")
ANSWER_LANES = ("pol", "def", "mkt")
SCALE = [
    ("Quiet", "No new problems in the last four weeks."),
    ("Keeping up", "Answers are arriving as fast as problems."),
    ("Slipping", "Problems are arriving up to twice as fast as answers."),
    ("Falling behind", "Problems are arriving more than twice as fast as answers."),
    ("Unanswered", "New problems, and not one answer yet."),
]


def pace_count(L, t):
    """Problems and answers the board logged on this story in the window."""
    since = (L.run - timedelta(days=7 * PACE_WEEKS)).isoformat()
    recent = [i for i in t["items"] if i["date"] >= since]
    return (sum(1 for i in recent if i["lane"] in PROBLEM_LANES),
            sum(1 for i in recent if i["lane"] in ANSWER_LANES))


def pace_level(L, t) -> int:
    p, a = pace_count(L, t)
    if p == 0:
        return 0
    if a == 0:
        return 4 if p >= 3 else 3
    r = p / a
    return 1 if r <= 1 else 2 if r <= 2 else 3


def reading(L, t) -> dict:
    """What the face shows. The editor's call from topics.json when there is
    one (level, asOf, why); otherwise the board's own count. Either way the
    count is returned too, so the page can print it as the evidence."""
    p, a = pace_count(L, t)
    r = t.get("reading")
    if r and isinstance(r.get("level"), int) and 0 <= r["level"] <= 4:
        return {"level": r["level"], "editor": True, "asOf": r.get("asOf", ""),
                "why": r.get("why", ""), "p": p, "a": a}
    return {"level": pace_level(L, t), "editor": False, "asOf": "", "why": "", "p": p, "a": a}


def face(level: int, cx: float, cy: float, s: float = 1.0) -> str:
    """Eyes, brows and mouth for a reading, centred on (cx, cy), scaled by s."""
    r = 3.3 * s
    dx = 5.2 * s
    lx, rx = cx - dx, cx + dx
    def eye(x, look, pr=0.5, lid=False):
        px, py = x + look[0] * r * 0.5, cy + look[1] * r * 0.5
        out = f'<circle class="sc" cx="{x:.1f}" cy="{cy:.1f}" r="{r:.1f}"/>'
        out += f'<circle class="pu" cx="{px:.1f}" cy="{py:.1f}" r="{r * pr:.1f}"/>'
        out += f'<circle class="hl" cx="{px - r * 0.2:.1f}" cy="{py - r * 0.22:.1f}" r="{r * 0.17:.1f}"/>'
        if lid:
            out += (f'<path class="bd" d="M{x - r:.1f} {cy:.1f}a{r:.1f} {r:.1f} 0 0 1 {2 * r:.1f} 0z"/>'
                    f'<path d="M{x - r:.1f} {cy:.1f}h{2 * r:.1f}"/>')
        return out
    my = cy + 7.5 * s
    by = cy - 5.5 * s
    if level == 0:    # half asleep
        return (eye(lx, (0, 0.6), 0.45, True) + eye(rx, (0, 0.6), 0.45, True)
                + f'<path class="mo" d="M{cx - 3 * s:.1f} {my:.1f}h{6 * s:.1f}"/>')
    if level == 1:    # content
        return (eye(lx, (0.4, 0.2)) + eye(rx, (0.4, 0.2))
                + f'<path class="mo" d="M{cx - 4.5 * s:.1f} {my - s:.1f}q{4.5 * s:.1f} {4 * s:.1f} {9 * s:.1f} 0"/>')
    if level == 2:    # unsure: a glance sideways, one brow up, flat mouth
        return (eye(lx, (0.8, 0.1)) + eye(rx, (0.8, 0.1))
                + f'<path d="M{rx - 3.5 * s:.1f} {by - 1.5 * s:.1f}l{7 * s:.1f} -{1.5 * s:.1f}"/>'
                + f'<path class="mo" d="M{cx - 3.5 * s:.1f} {my:.1f}h{7 * s:.1f}"/>')
    if level == 3:    # worried: brows up at the inside, a frown
        return (eye(lx, (0.2, -0.2), 0.55) + eye(rx, (0.2, -0.2), 0.55)
                + f'<path d="M{lx - 3.5 * s:.1f} {by:.1f}l{7 * s:.1f} -{2 * s:.1f}M{rx + 3.5 * s:.1f} {by:.1f}l-{7 * s:.1f} -{2 * s:.1f}"/>'
                + f'<path class="mo" d="M{cx - 4 * s:.1f} {my + s:.1f}q{4 * s:.1f} -{3.5 * s:.1f} {8 * s:.1f} 0"/>')
    # alarmed: wide eyes, small pupils, open mouth, a bead of sweat
    return (eye(lx, (0, 0), 0.35) + eye(rx, (0, 0), 0.35)
            + f'<path d="M{lx - 3.5 * s:.1f} {by - s:.1f}l{7 * s:.1f} -{1.5 * s:.1f}M{rx + 3.5 * s:.1f} {by - s:.1f}l-{7 * s:.1f} -{1.5 * s:.1f}"/>'
            + f'<ellipse class="mo" cx="{cx:.1f}" cy="{my:.1f}" rx="{2.4 * s:.1f}" ry="{3 * s:.1f}"/>'
            + f'<path class="sw" d="M{rx + 9 * s:.1f} {cy - 4 * s:.1f}q{2.5 * s:.1f} {4 * s:.1f} 0 {6 * s:.1f}q-{2.5 * s:.1f} -{2 * s:.1f} 0 -{6 * s:.1f}z"/>')


# The cast: one object per story, drawn in one hand, with the point where its
# face goes. The expression and the body tint come from the reading above.
# Keyed by topic id; a story without one gets a plain round face.
EMBLEMS = {
    # a flask with a crack, contents getting out
    "evaluation-incidents": ("""<path class="bd" d="M25 6h14M28 6v14L14 46a5 5 0 0 0 4.5 7h27a5 5 0 0 0 4.5-7L36 20V6"/>
<path class="af" d="M20 40h24l4 8a3 3 0 0 1-3 3h-26a3 3 0 0 1-3-3z" opacity=".9"/>
<path class="ac" d="M42 30l-3 5 4 4-2 5"/><circle class="af" cy="54" cx="48" r="2"/><circle class="af" cy="58" cx="43" r="1.4"/>""", (31.5, 28, 0.95)),
    # a mountain, flag already above the old record line
    "frontier-capability": ("""<path class="bd" d="M4 56L22 18l9 13 7-9 22 34z"/><path class="ac" d="M4 36h56" stroke-dasharray="3 3"/>
<path d="M38 22V5"/><path class="af" d="M38 5h13l-4 4 4 4H38z"/>""", (24.5, 45, 0.95)),
    # a window with a bolt for a cowlick: the agent at the keyboard
    "ai-in-attacks": ("""<rect class="bd" x="8" y="16" width="48" height="38" rx="6"/><path d="M8 26h48"/>
<circle class="af" cx="15" cy="21" r="1.6"/><circle class="af" cx="21" cy="21" r="1.6"/>
<path class="af ac" d="M35 2l-7 11h6l-3 8 9-11h-6l3-8z"/>""", (32, 38, 1.1)),
    # a shield with a bite out of it
    "attacks-on-ai": ("""<path class="bd" d="M32 5l20 7v17c0 13-9 22-20 27C21 51 12 42 12 29V12z"/>
<path class="ac" d="M40 20a7 7 0 1 1 1 14"/><circle class="af" cx="56" cy="28" r="5"/>""", (29, 33, 1.0)),
    # a magnifying glass over a cracked plate; the lens is its one big eye
    "ai-found-vulnerabilities": ("""<rect class="bd" x="4" y="12" width="36" height="40" rx="4"/><path class="ac" d="M12 30l6 4-4 6 7 4"/>
<circle class="lens" cx="42" cy="36" r="13"/><circle class="pu" cx="40" cy="38" r="5"/><circle class="hl" cx="38" cy="36" r="1.6"/>
<path d="M51 46l9 9"/><path d="M31 25q11-6 22 0"/>""", None),
    # a water tower on its legs: the old thing underneath everything
    "critical-infrastructure": ("""<path class="bd" d="M17 14h30l-2 18H19z"/><path d="M13 14h38"/><path class="af" d="M22 14q10-7 20 0z"/>
<path d="M22 32L14 58M42 32l8 26M18 46h28M32 32v26"/>""", (32, 23, 0.85)),
}


def emblem(L, t, level: int) -> str:
    art, anchor = EMBLEMS.get(t["id"], ('<circle class="bd" cx="32" cy="32" r="22"/>', (32, 32, 1.2)))
    lane = t["items"][0]["lane"] if t["items"] else "cap"
    counts = {}
    for i in t["items"]:
        counts[i["lane"]] = counts.get(i["lane"], 0) + 1
    lane = max(counts, key=counts.get) if counts else lane
    colour = f'var({L.lanes[lane]["var"]})'
    fc = face(level, *anchor) if anchor else ""
    return (f'<svg class="emblem lv{level}" viewBox="0 0 64 64" role="img" '
            f'aria-label="{SCALE[level][0]}" style="--em:{colour}">{art}{fc}</svg>')


def scale_strip(L) -> str:
    """The legend: five readings, each with its face on a plain round body."""
    cells = []
    for n, (name, what) in enumerate(SCALE):
        cells.append(f'<div class="sc-cell"><svg class="emblem lv{n}" viewBox="0 0 64 64" aria-hidden="true">'
                     f'<circle class="bd" cx="32" cy="32" r="24"/>{face(n, 32, 31, 1.3)}</svg>'
                     f'<span class="sc-n">{n}</span><span class="sc-name">{name}</span><span class="sc-what">{what}</span></div>')
    return (f'<div class="scale" role="img" aria-label="The scale: {"; ".join(f"{n} {a}" for n, (a, _) in enumerate(SCALE))}">'
            + "".join(cells) + "</div>")


def story_entry(site, L, t) -> str:
    """One of the six stories on the Watchlist page: its emblem, its name, one
    line on what it is, and the latest thing that moved."""
    latest = t["watch"][0] if t["watch"] else None
    moved = (f'last moved <time datetime="{latest["changed"]}">{_short(_d(latest["changed"]))}</time>'
             if latest and latest.get("changed") else "")
    status = (f'<span class="st"><b>{escape(latest["thread"])}.</b> {escape(_clip(latest["status"], 150))}</span>'
              if latest else "")
    rd = reading(L, t)
    level = rd["level"]
    who = (f'editor, {_short(_d(rd["asOf"]))}' if rd["editor"] and rd["asOf"] else "editor" if rd["editor"]
           else "board count")
    count = (f'Board, last {PACE_WEEKS} weeks: {rd["p"]} problem{"" if rd["p"] == 1 else "s"}, '
             f'{rd["a"]} answer{"" if rd["a"] == 1 else "s"}.')
    why = f'<span class="why">{escape(rd["why"])} <em>{count}</em></span>' if rd["why"] else f'<span class="why"><em>{count}</em></span>'
    return (f'<a class="story lv{level}" href="{site.prefix}topic/{t["id"]}/">'
            f'{emblem(L, t, level)}'
            f'<span class="kick"><span class="rd">{level} · {SCALE[level][0]}</span><span>{who}</span></span>'
            f'<span class="sn">{escape(t["name"])}</span>'
            f'{why}'
            f'<span class="sd">{escape(t["definition"])}</span>{status}'
            f'<span class="smeta">{len(t["items"])} items{" · " + moved if moved else ""}</span></a>')


def topics_body(site, L) -> str:
    live = [t for t in L.topics if t["items"]]
    live.sort(key=lambda t: (reading(L, t)["level"], t["watch"][0].get("changed", "") if t["watch"] else ""), reverse=True)
    entries = "".join(story_entry(site, L, t) for t in live)
    other = also_watching(site, L, L.other_watch)
    return f"""{site.nav(TOPICS_URL)}

  <header class="pagehead">
    <h1>Watchlist</h1>
    <div class="sub wide">The {_words(len(live))} stories the board is following, worst first. Each face is a reading of
      whether the answers are keeping up with the problems: the editor's call where there is one, dated, and the
      board's own four-week count otherwise. The count is printed under every face. Open a story for everything on it.</div>
  </header>

  {scale_strip(L)}

  <div class="stories">{entries}</div>

  {f'<section class="block alsow"><p class="blockhead">Also watching</p><p class="lede">Running threads outside the {_words(len(live))} stories. Open one for its items and their original sources.</p>{other}</section>' if other else ""}

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
