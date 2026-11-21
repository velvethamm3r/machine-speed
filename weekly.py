"""
Machine Speed — the weekly layer.

Three pages read the same board a week at a time:

    archive/            the hub: alerts, one staged tracker per topic, every edition
    weekly/<n>/         one edition per week: the note, the picks, the cases that
                        moved, one more item from each lane
    week/<monday>/      the full record: every item of the week, summaries folded

Nothing here adds content. Items come from data.json; three small files carry the
editorial layer on top of them, and every one of them is optional:

    editorial/trackers.json     cases followed across items, each with three stops
    editorial/alerts.json       items flagged for impact or novelty
    editorial/editions/*.json   a week's note, picks and per-lane choices (same shape as
                        weekly[] in data.json, which still works)

A week with no edition file and no weekly[] entry still gets an edition: the picks
fall back to the week's key items, then to its newest.

Python 3 standard library only, like the rest of the build.
"""

import json
from datetime import date, timedelta
from html import escape
from pathlib import Path

EDITION_URL = "weekly/"
# Everything edited by hand for the weekly layer lives in this one folder.
EDITORIAL = "editorial"
WEEKLY_NAV = "Weekly"

# A case in editorial/trackers.json carries "reviewed": false until a person has checked its
# three stops against the items it cites. Unreviewed cases stay off the site unless
# the build is run with --drafts (a local preview) or this is switched on.
SHOW_UNREVIEWED_CASES = False

PICKS = 5            # picks an edition shows
MOVED_MAX = 5        # "cases that moved" an edition shows
ALERTS_MAX = 6       # alert cards on the hub
OPEN_MONTHS = 2      # months of editions the hub opens by default
TURNING_POINTS = 7   # key items listed for a topic that has no tracker yet
TEASER = 230         # characters of a summary shown before "Read the full summary"

ALERT_TYPES = {"impact": "Impact", "novel": "Novel"}
ALERT_HELP = {"impact": "the attack had a real-world effect", "novel": "a first of its kind"}
# The colour of a tracker's third stop: harm (exploited, attributed), a policy
# response, or an access decision.
TONES = ("harm", "policy", "access")


def _d(iso: str) -> date:
    return date.fromisoformat(iso)


def _short(iso: str) -> str:
    d = _d(iso)
    return f"{d.strftime('%b')} {d.day}"


def _json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load(root: Path):
    """(trackers, alerts, editions) — each empty when its file is missing."""
    trackers = _json(root / EDITORIAL / "trackers.json", {}).get("trackers", [])
    alerts = _json(root / EDITORIAL / "alerts.json", {}).get("alerts", [])
    editions = {}
    folder = root / EDITORIAL / "editions"
    if folder.is_dir():
        for f in sorted(folder.glob("*.json")):
            e = json.loads(f.read_text(encoding="utf-8"))
            # "ready": false parks a half-written edition without breaking the build.
            if e.get("week") and e.get("ready", True):
                editions[e["week"]] = e
    return trackers, alerts, editions


def merge_weekly(weekly: list, editions: dict):
    """Fold editions/*.json into data.json's weekly[]; a file wins over the array.

    Returns the merged weekly list (in the shape layers.py already validates) and
    the per-lane choices, which only this module reads.
    """
    by = {w.get("week"): dict(w) for w in weekly}
    lanes = {}
    for mon, e in editions.items():
        cur = by.get(mon, {"week": mon})
        for k in ("note", "picks"):
            if e.get(k):
                cur[k] = e[k]
        if cur.get("picks"):
            by[mon] = cur
        if e.get("lanes"):
            lanes[mon] = e["lanes"]
    return [by[k] for k in sorted(by)], lanes


def validate(data: dict, topics: list, trackers: list, alerts: list, lane_choices: dict, lanes: dict):
    errors, warnings = [], []
    ids = {i.get("id") for i in data.get("items", [])}
    known = {t.get("id") for t in topics}
    seen = set()
    for tr in trackers:
        tw = f"editorial/trackers.json '{tr.get('topic')}'"
        if tr.get("topic") not in known:
            errors.append(f"{tw}: topic is not in topics.json")
        if len(tr.get("stages", [])) != 3:
            errors.append(f"{tw}: needs exactly three stages")
        if tr.get("tone", "harm") not in TONES:
            errors.append(f"{tw}: tone must be one of {', '.join(TONES)}")
        for c in tr.get("cases", []):
            cw = f"{tw} case '{c.get('id')}'"
            if not c.get("id") or not c.get("name"):
                errors.append(f"{cw}: needs an id and a name")
            if c.get("id") in seen:
                errors.append(f"{cw}: id appears twice")
            seen.add(c.get("id"))
            stops = c.get("stops", [])
            if len(stops) != 3:
                errors.append(f"{cw}: needs exactly three stops")
            for s in stops:
                if s.get("date"):
                    try:
                        _d(s["date"])
                    except ValueError:
                        errors.append(f"{cw}: stop date '{s['date']}' is not YYYY-MM-DD")
                if s.get("on") and not s.get("text"):
                    errors.append(f"{cw}: a reached stop needs its text")
            if not c.get("items"):
                errors.append(f"{cw}: cites no items")
            for iid in c.get("items", []):
                if iid not in ids:
                    warnings.append(f"{cw}: item '{iid}' is not on the board")
    for n, a in enumerate(alerts):
        if a.get("item") not in ids:
            warnings.append(f"editorial/alerts.json[{n}]: item '{a.get('item')}' is not on the board")
        if a.get("type") not in ALERT_TYPES:
            errors.append(f"editorial/alerts.json[{n}]: type must be one of {', '.join(ALERT_TYPES)}")
        if not a.get("why"):
            errors.append(f"editorial/alerts.json[{n}]: needs a 'why' line")
    for mon, ch in lane_choices.items():
        for k, iid in ch.items():
            if k not in lanes:
                errors.append(f"editorial/editions/{mon}.json: lanes has an unknown lane '{k}'")
            elif iid not in ids:
                errors.append(f"editorial/editions/{mon}.json: lanes.{k} '{iid}' is not on the board")
    return errors, warnings


# ---------------------------------------------------------------------------
# The model
# ---------------------------------------------------------------------------

class Weekly:
    def __init__(self, data, weeks, lanes, conf, topics, trackers, alerts, lane_choices, drafts=False):
        self.lanes, self.conf, self.topics = lanes, conf, topics
        self.by_id = {i["id"]: i for i in data.get("items", [])}
        self.items = data.get("items", [])
        self.weeks = weeks                      # newest first, from build.week_buckets
        self.picks = {w["week"]: w for w in data.get("weekly", [])}
        self.lane_choices = lane_choices
        show_all = drafts or SHOW_UNREVIEWED_CASES
        self.hidden_cases = 0
        self.trackers = {}
        for tr in trackers:
            cases = []
            for c in tr.get("cases", []):
                if not (c.get("reviewed") or show_all):
                    self.hidden_cases += 1
                    continue
                thread = sorted((self.by_id[i] for i in c.get("items", []) if i in self.by_id),
                                key=lambda i: i["date"])
                if thread:
                    cases.append(dict(c, thread=thread))
            self.trackers[tr["topic"]] = dict(tr, cases=cases)
        self.alerts = sorted((dict(a, it=self.by_id[a["item"]]) for a in alerts if a.get("item") in self.by_id),
                             key=lambda a: a["it"]["date"], reverse=True)
        self.alert_of = {a["item"]: a for a in self.alerts}

    # -- weeks ----------------------------------------------------------------
    def number(self, idx: int) -> int:
        return len(self.weeks) - idx

    def edition(self, idx: int) -> dict:
        """What an edition prints: note, picks, the cases that moved, one per lane."""
        w = self.weeks[idx]
        chosen = self.picks.get(w["monday"])
        if chosen:
            picks = [dict(it=self.by_id[p["item"]], why=p.get("why", "")) for p in chosen["picks"]
                     if p.get("item") in self.by_id][:PICKS]
            note = chosen.get("note", "")
        else:
            keyed = [i for i in w["items"] if i.get("key")]
            picks = [dict(it=i, why="") for i in (keyed or w["items"])[:PICKS]]
            note = ""
        moved = self.moved(w)
        used = {p["it"]["id"] for p in picks} | {i["id"] for c, _ in moved for i in c["thread"]}
        choice = self.lane_choices.get(w["monday"], {})
        more = []
        for k in self.lanes:
            pool = [i for i in w["items"] if i["lane"] == k]
            if not pool:
                continue
            if choice.get(k) in self.by_id:
                it = self.by_id[choice[k]]
            else:
                rest = [i for i in pool if i["id"] not in used]
                it = next((i for i in rest if i.get("key")), rest[0] if rest else None)
            if it:
                more.append((k, len(pool), it))
        return dict(week=w, no=self.number(idx), note=note, picks=picks, chosen=bool(chosen),
                    moved=moved, more=more)

    def moved(self, w: dict):
        """Cases where a stop was reached inside this week, newest movement first."""
        out = []
        hi = (_d(w["monday"]) + timedelta(days=6)).isoformat()
        for tr in self.trackers.values():
            for c in tr["cases"]:
                hits = [s["date"] for s in c["stops"] if s.get("on") and s.get("date")
                        and w["monday"] <= s["date"] <= hi]
                # A case belongs to a week only once its first stop has been reached.
                first = c["stops"][0].get("date") or c["thread"][0]["date"]
                if hits and first <= hi:
                    out.append((max(hits), c, tr))
        out.sort(key=lambda x: x[0], reverse=True)
        return [(c, tr) for _, c, tr in out[:MOVED_MAX]]

    def lead(self, w: dict):
        chosen = self.picks.get(w["monday"])
        if chosen:
            heads = [self.by_id[p["item"]] for p in chosen["picks"] if p.get("item") in self.by_id]
        else:
            heads = [i for i in w["items"] if i.get("key")] + [i for i in w["items"] if not i.get("key")]
        return heads[:2]


# ---------------------------------------------------------------------------
# Shared pieces
# ---------------------------------------------------------------------------

HEAD = ('<link rel="stylesheet" href="{p}weekly.css{v}">\n'
        '<script src="{p}weekly.js{vj}" defer></script>\n')


def head(asset_prefix: str, v_css: str = "", v_js: str = "") -> str:
    return HEAD.format(p=asset_prefix, v=v_css, vj=v_js)


def _lane(wk, k: str, extra: str = "") -> str:
    v = wk.lanes[k]
    return f'<span class="wk-lane" style="color:var({v["var"]})">{v["name"]}{extra}</span>'


def _board(site, wk, it) -> str:
    return f'{site.prefix}{wk.lanes[it["lane"]]["page"]}#{escape(it["id"])}'


def _conf(wk, it) -> str:
    c = it["confidence"]
    return f'<span class="conf c-{c}">{wk.conf.get(c, c)}</span>'


def _src(it) -> str:
    return (f'<a href="{escape(it["url"], quote=True)}" target="_blank" rel="noopener">'
            f'{escape(it["outlet"])} ↗</a>')


def _mix(wk, items) -> str:
    segs, key = [], []
    for k, v in wk.lanes.items():
        n = sum(1 for i in items if i["lane"] == k)
        if n:
            segs.append(f'<i style="flex:{n};background:var(--{k}-mark)"></i>')
            key.append(f'{v["name"]} {n}')
    label = " · ".join(key)
    return (f'<span class="wk-mix"><span class="wk-bar" role="img" aria-label="{escape(label)}">'
            f'{"".join(segs)}</span><span class="wk-key">{escape(label)}</span></span>')


def _alert_badge(wk, it) -> str:
    a = wk.alert_of.get(it["id"])
    return f'<span class="wk-alert a-{a["type"]}">{ALERT_TYPES[a["type"]]}</span>' if a else ""


def case_row(site, wk, c, tr, week=None, open_=False) -> str:
    """One case as a line with three stops; the thread folds out underneath.

    With `week` set the case is drawn as it stood at the end of that week, and a
    stop reached inside the week is marked new.
    """
    hi = (_d(week["monday"]) + timedelta(days=6)).isoformat() if week else None
    tone = tr.get("tone", "harm")
    stops, states = [], []
    for s in c["stops"]:
        on = bool(s.get("on")) and not (hi and s.get("date") and s["date"] > hi)
        states.append(on)
    for n, s in enumerate(c["stops"]):
        on = states[n]
        new = bool(week and on and s.get("date") and week["monday"] <= s["date"] <= hi)
        nxt = states[n + 1] if n < 2 else None
        cls = f'wk-stop s{n + 1}' + (" on" if on else "") + (" to-on" if nxt else "") + (" last" if n == 2 else "")
        text = s.get("text", "") if on else (s.get("text") if not s.get("on") else "Not yet")
        stops.append(f'<span class="{cls}"><i aria-hidden="true"></i>'
                     f'<b>{escape(tr["stages"][n])}{"<em>New</em>" if new else ""}</b>'
                     f'<span>{escape(text or "Not stated")}</span></span>')
    thread = [i for i in c["thread"] if not hi or i["date"] <= hi]
    rows = "".join(f'<li><time datetime="{i["date"]}">{_short(i["date"])}</time>{_lane(wk, i["lane"])}'
                   f'<a href="{_board(site, wk, i)}">{escape(i["headline"])}</a></li>' for i in thread)
    n = len(thread)
    topic = f'<small class="wk-topicname">{escape(tr["name"])}</small>' if week else ""
    return (f'<details class="wk-case t-{tone}" data-wk-key="{"on" if states[2] else "off"}"{" open" if open_ else ""}>'
            f'<summary><span class="wk-case-id">{topic}<b>{escape(c["name"])}</b>'
            f'<small>{escape(c.get("sub", ""))}</small>'
            f'<em class="wk-toggle">thread · {n} item{"" if n == 1 else "s"}</em></span>'
            f'<span class="wk-stops">{"".join(stops)}</span></summary>'
            f'<ol class="wk-thread">{rows}</ol></details>')


# ---------------------------------------------------------------------------
# The hub — archive/
# ---------------------------------------------------------------------------

def hub_body(site, wk, archive_url: str) -> str:
    # alerts
    cards = []
    for a in wk.alerts[:ALERTS_MAX]:
        it = a["it"]
        cards.append(
            f'<article class="wk-card" data-wk-key="{a["type"]}">'
            f'<div class="wk-cardtop"><span class="wk-alert a-{a["type"]}">{ALERT_TYPES[a["type"]]}</span>'
            f'<span class="wk-dim">{wk.lanes[it["lane"]]["name"]} · {_short(it["date"])}</span></div>'
            f'<p class="wk-why a-{a["type"]}">{escape(a["why"])}</p>'
            f'<a class="wk-h" href="{_board(site, wk, it)}">{escape(it["headline"])}</a>'
            f'<div class="wk-meta">{_conf(wk, it)}<span>{escape(it["outlet"])}</span></div></article>')
    alerts = ""
    if cards:
        shown = wk.alerts[:ALERTS_MAX]
        chips = "".join(
            f'<button type="button" data-wk-show="{k}" aria-pressed="{"true" if k == "all" else "false"}">'
            f'{label} {n}</button>'
            for k, label, n in [("all", "All", len(shown))] + [
                (t, ALERT_TYPES[t], sum(1 for a in shown if a["type"] == t)) for t in ALERT_TYPES])
        helps = " ".join(f'<b>{ALERT_TYPES[t]}</b>: {ALERT_HELP[t]}.' for t in ALERT_TYPES)
        alerts = (f'<section class="wk-sec" id="alerts" data-wk-group><div class="wk-sechead">'
                  f'<div><h2>Alerts</h2><p>{helps}</p></div>'
                  f'<div class="wk-chips" role="group" aria-label="Filter alerts" hidden>{chips}</div></div>'
                  f'<div class="wk-cards">{"".join(cards)}</div></section>')

    # stories
    tabs, panels = [], []
    for t in wk.topics:
        its = sorted((i for i in wk.items if t["id"] in i.get("topics", [])),
                     key=lambda i: i["date"], reverse=True)
        if not its:
            continue
        tabs.append(f'<a href="#story-{t["id"]}"><b>{escape(t["name"])}</b>'
                    f'<small>{len(its)} items</small></a>')
        tr = wk.trackers.get(t["id"])
        figures = ""
        if tr and tr.get("figures"):
            figures = '<div class="wk-figs">' + "".join(
                f'<div class="wk-fig"><div class="wk-big">{escape(f["big"])} <span>{escape(f.get("of", ""))}</span></div>'
                f'<p>{escape(f["text"])}</p><small>{escape(f.get("source", ""))}</small></div>'
                for f in tr["figures"]) + "</div>"
            figures = '<div class="wk-label">The base rate, as reported</div>' + figures
        if tr and tr["cases"]:
            cases = tr["cases"]
            n = len(cases)
            c2 = sum(1 for c in cases if c["stops"][1].get("on"))
            c3 = sum(1 for c in cases if c["stops"][2].get("on"))
            summary = (f'{n} {tr.get("noun", "cases")}. {c2} {tr.get("say2", "reached the second stop")}. '
                       f'{c3} {tr.get("say3", "reached the third")}. {tr.get("note", "")}')
            chips = "".join(
                f'<button type="button" data-wk-show="{k}" aria-pressed="{"true" if k == "all" else "false"}">'
                f'{escape(label)} {m}</button>'
                for k, label, m in (("all", "All", n), ("on", tr.get("chipOn", "Reached"), c3),
                                    ("off", tr.get("chipOff", "Not reached"), n - c3)))
            rows = "".join(case_row(site, wk, c, dict(tr, name=t["name"]), open_=(c["id"] == tr.get("open")))
                           for c in cases)
            body = (f'<div class="wk-panel" data-wk-group><div class="wk-sechead"><div><h4>{escape(tr["title"])}</h4>'
                    f'<p>{escape(summary.strip())}</p></div>'
                    f'<div class="wk-chips" role="group" aria-label="Filter cases" hidden>{chips}</div></div>'
                    f'<div class="wk-cases">{rows}</div>'
                    f'<p class="wk-foot">"None reported" and "Not stated" reflect what the items on the board say so far.</p></div>')
        else:
            keyed = [i for i in its if i.get("key")]
            pts = (keyed or its)[:TURNING_POINTS]
            rows = "".join(f'<li><time datetime="{i["date"]}">{_short(i["date"])}</time>{_lane(wk, i["lane"])}'
                           f'<a href="{_board(site, wk, i)}">{escape(i["headline"])}</a></li>' for i in pts)
            body = (f'<div class="wk-panel"><h4>{"Turning points, newest first" if keyed else "Latest on the board"}</h4>'
                    f'<ol class="wk-thread big">{rows}</ol></div>')
        panels.append(f'<section class="wk-topic" id="story-{t["id"]}"><h3>{escape(t["name"])}</h3>'
                      f'<p class="wk-def">{escape(t["definition"])}</p>{figures}{body}</section>')
    stories = ""
    if panels:
        stories = (f'<section class="wk-sec" id="stories"><div class="wk-sechead"><div><h2>Follow a story</h2>'
                   f'<p>{site_numword(len(panels))} questions the board keeps returning to. '
                   f'Pick one to see how far each case has travelled.</p></div></div>'
                   f'<nav class="wk-topicnav" aria-label="Stories">{"".join(tabs)}</nav>'
                   f'<div class="wk-topics">{"".join(panels)}</div></section>')

    # editions, by month
    months = []
    for idx, w in enumerate(wk.weeks):
        m = _d(w["lo"]).strftime("%B %Y")
        if not months or months[-1][0] != m:
            months.append((m, []))
        months[-1][1].append((idx, w))
    blocks = []
    for mi, (name, ws) in enumerate(months):
        total = sum(len(w["items"]) for _, w in ws)
        rows = []
        for idx, w in ws:
            heads = wk.lead(w)
            also = f'<span class="wk-also">Also: {escape(heads[1]["headline"])}</span>' if len(heads) > 1 else ""
            rows.append(
                f'<a class="wk-week" href="{site.prefix}{EDITION_URL}{wk.number(idx)}/">'
                f'<span class="wk-when"><b>{escape(w["label"])}</b>'
                f'<small>No. {wk.number(idx)} · {len(w["items"])} items</small></span>'
                f'<span class="wk-lead">{_lane(wk, heads[0]["lane"])}'
                f'<span class="wk-h">{escape(heads[0]["headline"])}</span>{also}</span>'
                f'{_mix(wk, w["items"])}</a>')
        blocks.append(f'<details class="wk-month"{" open" if mi < OPEN_MONTHS else ""}><summary><b>{name}</b>'
                      f'<small>{len(ws)} week{"" if len(ws) == 1 else "s"} · {total} items</small></summary>'
                      f'{"".join(rows)}</details>')
    editions = (f'<section class="wk-sec" id="editions"><div class="wk-sechead"><div><h2>Weekly editions</h2>'
                f'<p>One edition for each of the {len(wk.weeks)} weeks.</p></div></div>{"".join(blocks)}</section>')

    jumps = "".join(f'<a href="#{i}">{label} ↓</a>' for i, label, on in (
        ("alerts", "Alerts", alerts), ("stories", "Follow a story", stories), ("editions", "Weekly editions", True)) if on)
    return f"""{site.nav(archive_url)}

  <header class="wk-head">
    <div class="wk-eyebrow">Archive</div>
    <h1>What happened after the headline.</h1>
    <p>{len(wk.items)} source-verified items since {escape(_short(site.cov_start))}, {site.cov_start[:4]}, organised by what happened next.</p>
    <div class="wk-jumps">{jumps}</div>
  </header>

  {alerts}

  {stories}

  {editions}

  {site.subscribe_block(compact=True)}

  {site.footer()}"""


def site_numword(n: int) -> str:
    words = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten"]
    return words[n] if n < len(words) else str(n)


# ---------------------------------------------------------------------------
# An edition — weekly/<n>/
# ---------------------------------------------------------------------------

def _pager(site, wk, idx: int) -> str:
    older = idx + 1 if idx + 1 < len(wk.weeks) else None
    newer = idx - 1 if idx > 0 else None

    def link(i, cls, text):
        if i is None:
            return f'<span class="{cls}"></span>'
        return (f'<a class="{cls}" href="{site.prefix}{EDITION_URL}{wk.number(i)}/"><small>{text}</small>'
                f'<b>No. {wk.number(i)} · {escape(wk.weeks[i]["label"])}</b></a>')
    return (f'<nav class="wk-pager" aria-label="Editions">{link(older, "prev", "← Previous edition")}'
            f'{link(newer, "next", "Next edition →")}</nav>')


def edition_body(site, wk, idx: int, archive_url: str) -> str:
    e = wk.edition(idx)
    w = e["week"]
    record = f'{site.prefix}week/{w["monday"]}/'
    picks = []
    for n, p in enumerate(e["picks"], 1):
        it = p["it"]
        if p["why"]:
            para = f'<p><strong>Why it matters.</strong> {escape(p["why"])}</p>'
        else:
            core = it["core"]
            para = f'<p>{escape(core if len(core) <= TEASER * 2 else core[:TEASER * 2].rsplit(" ", 1)[0] + "…")}</p>'
        picks.append(
            f'<article class="wk-pick"><div class="wk-n" style="color:var({wk.lanes[it["lane"]]["var"]})" aria-hidden="true">{n}</div>'
            f'<div><div class="wk-cardtop">{_alert_badge(wk, it)}{_lane(wk, it["lane"], " · " + _short(it["date"]))}</div>'
            f'<h3><a href="{_board(site, wk, it)}">{escape(it["headline"])}</a></h3>{para}'
            f'<div class="wk-meta">{_conf(wk, it)}{_src(it)}</div></div></article>')
    note = (f'<section class="wk-note"><div class="wk-label">The week in one paragraph</div>'
            f'<p>{escape(e["note"])}</p></section>') if e["note"] else ""
    moved = ""
    if e["moved"]:
        rows = "".join(case_row(site, wk, c, dict(tr, name=_topic_name(wk, tr["topic"])), week=w) for c, tr in e["moved"])
        n = len(e["moved"])
        moved = (f'<section class="wk-sec"><div class="wk-sechead"><div><h2>Stories that moved this week</h2>'
                 f'<p>{site_numword(n)} case{"" if n == 1 else "s"} the board is following moved forward this week. '
                 f'Filled stops have happened and hollow stops are still unreported.</p></div>'
                 f'<a class="wk-go" href="{site.prefix}{archive_url}#stories">All stories →</a></div>'
                 f'<div class="wk-panel"><div class="wk-cases">{rows}</div></div></section>')
    more = ""
    if e["more"]:
        rows = "".join(
            f'<div class="wk-more"><div>{_lane(wk, k)}<a href="{record}#lane-{k}">All {n} this week →</a></div>'
            f'<div><a class="wk-h" href="{_board(site, wk, it)}">{escape(it["headline"])}</a>'
            f'<div class="wk-meta">{_conf(wk, it)}{_src(it)}<span>{_short(it["date"])}</span></div></div></div>'
            for k, n, it in e["more"])
        more = (f'<section class="wk-sec"><div class="wk-sechead"><div><h2>One more from each lane</h2>'
                f'<p>The next thing worth knowing in each lane. Everything else from the week stays in the full record.</p>'
                f'</div></div>{rows}</section>')
    n_items = len(w["items"])
    return f"""{site.nav(archive_url, lanes=False)}

  <div class="wk-col">
  <header class="wk-head ed">
    <div class="wk-crumbs"><a href="{site.prefix}{archive_url}">← All editions</a></div>
    <div class="wk-eyebrow">Machine Speed Weekly · No. {e["no"]}</div>
    <h1>{escape(w["label"])}</h1>
    <p><a href="{record}">Full record: {n_items} items with summaries and sources</a></p>
  </header>

  {note}

  <section class="wk-picks"><div class="wk-label">{"This week's picks" if e["chosen"] else "This week's key items"}</div>
    {"".join(picks)}
  </section>

  {moved}

  {more}

  <div class="wk-box"><div><b>Want the whole week?</b>
    <span>The full record for {escape(w["label"])} keeps all {n_items} items as the board wrote them, lane by lane.</span></div>
    <a href="{record}">Open the full record →</a></div>

  {_pager(site, wk, idx)}
  </div>

  {site.footer()}"""


def _topic_name(wk, topic_id: str) -> str:
    return next((t["name"] for t in wk.topics if t["id"] == topic_id), topic_id)


def edition_description(wk, idx: int) -> str:
    e = wk.edition(idx)
    if e["note"]:
        return e["note"][:240]
    return e["picks"][0]["it"]["headline"][:240] if e["picks"] else ""


# ---------------------------------------------------------------------------
# The full record — week/<monday>/
# ---------------------------------------------------------------------------

def record_body(site, wk, idx: int, archive_url: str) -> str:
    w = wk.weeks[idx]
    no = wk.number(idx)
    chosen = wk.picks.get(w["monday"])
    pick_no = {p["item"]: n for n, p in enumerate(chosen["picks"], 1)} if chosen else {}
    chips, sections = [], []
    for k, v in wk.lanes.items():
        items = site.lane_items(k, w["items"])
        if not items:
            continue
        chips.append(f'<a href="#lane-{k}"><i style="background:var({v["var"]})"></i><b>{v["name"]}</b>'
                     f'<small>{len(items)} item{"" if len(items) == 1 else "s"}</small></a>')
        rows = []
        for it in items:
            tag = (f'Pick {pick_no[it["id"]]}' if it["id"] in pick_no else "Key" if it.get("key") else "")
            core = it["core"]
            if len(core) > TEASER + 60:
                teaser = core[:TEASER].rsplit(" ", 1)[0] + "…"
                summary = (f'<details class="wk-sum"><summary><span class="wk-teaser">{escape(teaser)}</span>'
                           f'<span class="wk-readmore"></span></summary><p>{escape(core)}</p></details>')
            else:
                summary = f'<p>{escape(core)}</p>'
            rows.append(
                f'<article class="wk-item" id="{escape(it["id"])}"><div class="wk-when">'
                f'<time datetime="{it["date"]}">{_short(it["date"])}</time>'
                f'{f"<span class=wk-tag>{tag}</span>" if tag else ""}</div>'
                f'<div><h3>{escape(it["headline"])}</h3>{summary}'
                f'<div class="wk-meta">{_conf(wk, it)}{_src(it)}</div></div></article>')
        sections.append(
            f'<section class="wk-lanesec" id="lane-{k}"><div class="wk-sechead"><div>'
            f'<h2 style="color:var({v["var"]})">{v["name"]} · {len(items)} item{"" if len(items) == 1 else "s"}</h2></div>'
            f'<button type="button" class="wk-expand" data-wk-expand hidden>Expand all summaries</button></div>'
            f'{"".join(rows)}</section>')
    edition = f'{site.prefix}{EDITION_URL}{no}/'
    older = wk.weeks[idx + 1] if idx + 1 < len(wk.weeks) else None
    newer = wk.weeks[idx - 1] if idx > 0 else None
    pager = ('<nav class="wk-pager" aria-label="Weeks">'
             + (f'<a class="prev" href="{site.prefix}week/{older["monday"]}/"><small>← Previous week</small>'
                f'<b>{escape(older["label"])}</b></a>' if older else '<span class="prev"></span>')
             + (f'<a class="next" href="{site.prefix}week/{newer["monday"]}/"><small>Next week →</small>'
                f'<b>{escape(newer["label"])}</b></a>' if newer else '<span class="next"></span>')
             + '</nav>')
    return f"""{site.nav(archive_url, lanes=False)}

  <div class="wk-col">
  <header class="wk-head ed">
    <div class="wk-crumbs"><a href="{edition}">← Back to the edition, No. {no}</a>
      <a href="{site.prefix}{archive_url}">All weeks</a></div>
    <div class="wk-eyebrow">Full record · Week {no}</div>
    <h1>{escape(w["label"])}</h1>
    <p>All {len(w["items"])} items from the week as the board wrote them, each with its source and a label
      for who is making the claim. For the short version, <a href="{edition}">read the edition</a>.</p>
  </header>

  <nav class="wk-lanenav" aria-label="Lanes">{"".join(chips)}</nav>

  {"".join(sections)}

  <div class="wk-box"><div><b>Short on time?</b>
    <span>The edition covers this week in a few minutes.</span></div>
    <a href="{edition}">Read the edition →</a></div>

  {pager}

  {site.sources_block(w["items"], "Sources cited this week")}
  </div>

  {site.footer()}"""


# ---------------------------------------------------------------------------
# Edition draft — written for the newest week so there is always a file to edit
# ---------------------------------------------------------------------------

def write_edition_draft(root: Path, wk) -> str:
    """Pre-fill editorial/editions/<monday>.json for the newest week, once.

    The file is written with "ready": false, which the build ignores, so it changes
    nothing on the site until a person fills in the "why" lines and switches it on.
    Returns the path written, or "" when the week already has a file or picks.
    """
    if not wk.weeks:
        return ""
    w = wk.weeks[0]
    path = root / EDITORIAL / "editions" / f'{w["monday"]}.json'
    if path.exists() or w["monday"] in wk.picks:
        return ""
    ranked = [i for i in w["items"] if i.get("key")] + [i for i in w["items"] if not i.get("key")]
    picks = ranked[:PICKS]
    used = {i["id"] for i in picks}
    lanes, hints = {}, {}
    for k in wk.lanes:
        nxt = next((i for i in ranked if i["lane"] == k and i["id"] not in used), None)
        if nxt:
            lanes[k], hints[k] = nxt["id"], nxt["headline"]
    doc = {"week": w["monday"], "ready": False,
           "_how": "Write a why for each pick, swap any item id you disagree with, add a note if you "
                   "want one, then set ready to true. Lines starting with _ are only here to help you.",
           "note": "",
           "picks": [{"item": i["id"], "_headline": i["headline"], "why": ""} for i in picks],
           "lanes": lanes, "_lane_headlines": hints}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return str(path.relative_to(root))


# ---------------------------------------------------------------------------
# Review sheet — a draft for a human, never published
# ---------------------------------------------------------------------------

def review_sheet(wk, trackers_raw: list, by_id: dict, as_of: str = "") -> str:
    """Markdown: cases a run changed in the last week, then every unreviewed case."""
    out = ["# Machine Speed — tracker cases waiting for review", "",
           "> Each case below is hidden from the site until `\"reviewed\": true` is set on it in",
           "> `editorial/trackers.json`. Check the three stops against the headlines, fix any wording in",
           "> `editorial/trackers.json`, then approve with `python3 tools/review_cases.py --approve <case id>`",
           "> (or `--approve-topic <topic id>`, or `--approve-all`).", ""]
    since = (_d(as_of[:10]) - timedelta(days=7)).isoformat() if as_of else ""
    recent = [(tr, c) for tr in trackers_raw for c in tr.get("cases", [])
              if c.get("reviewed") and since and c.get("changed", "") >= since]
    if recent:
        out += ["## Changed in the last 7 days (already live — glance and fix if wrong)", ""]
        for tr, c in recent:
            out.append(f"### {c['name']}  (`{c['id']}`, changed {c['changed']})")
            for label, s in zip(tr["stages"], c["stops"]):
                when = f" [{s['date']}]" if s.get("date") else ""
                out.append(f"- {'●' if s.get('on') else '○'} **{label}**{when}: {s.get('text', '')}")
            out.append("")
    n = 0
    for tr in trackers_raw:
        pending = [c for c in tr.get("cases", []) if not c.get("reviewed")]
        if not pending:
            continue
        out += [f"## {tr.get('title', tr['topic'])}  (`{tr['topic']}`)", ""]
        for c in pending:
            n += 1
            out.append(f"### {c['name']}  (`{c['id']}`)")
            for label, s in zip(tr["stages"], c["stops"]):
                mark = "●" if s.get("on") else "○"
                when = f" [{s['date']}]" if s.get("date") else ""
                out.append(f"- {mark} **{label}**{when}: {s.get('text', '')}")
            out.append("")
            for iid in c.get("items", []):
                it = by_id.get(iid)
                if it:
                    out.append(f"  - {it['date']} · {it['headline']}")
            out.append("")
    if not n:
        out.append("Nothing is waiting. Every case in editorial/trackers.json has been reviewed.")
    return "\n".join(out) + "\n"
