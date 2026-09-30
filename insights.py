"""
Machine Speed — insights: the layer that turns the record into findings.

Everything here is computed from data.json (plus entered.json and entities.json)
at build time. Nothing here adds a claim of its own: every number is a count or
a date difference over items that are already sourced on the board, and every
page says how it was counted. That keeps it inside the board's rule — report,
do not advocate or forecast.

    /findings/            weekly trends, the confidence mix, how fast items
                          reach the board, and the response lag by topic
    /entities/            every tracked organisation, model and platform
    /entity/<id>/         one entity's items
    /data/                the open dataset: items.json, items.csv, topics.json
    /methodology/         sourcing rules and confidence tiers, in public
    /corrections/         the corrections log

and, written into the repo for a human (never published by the build):

    newsletter/weekly-<monday>.md        a Friday one-pager draft
    newsletter/quarterly-<yyyy>-q<n>.md  a quarterly report draft, numbers filled in

Two optional data fields feed it, both documented in SCHEMA.md:

    items[].topics    topic ids from topics.json the item belongs to
    corrections[]     the public corrections log

Python 3 standard library only, like build.py.
"""

import csv
import io
import json
import re
from datetime import date, timedelta
from html import escape
from pathlib import Path

FINDINGS_URL = "findings/"
ENTITIES_URL = "entities/"
DATA_URL = "data/"
METHOD_URL = "methodology/"
CORRECTIONS_URL = "corrections/"
ENTITIES_FILE = "entities.json"

# The dataset's licence. CC BY 4.0 lets anyone reuse the data with credit,
# which is what makes it citable; change both strings together if you choose
# another licence.
DATA_LICENSE = "CC BY 4.0"
DATA_LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"

# Lanes that start a topic's clock, and lanes that answer. The response lag is
# the days from a topic's first capability or attack item to its first answer.
TRIGGER_LANES = ("cap", "atk")
RESPONSE_LANES = ("pol", "def", "mkt")

# entered.json was created on this day and seeded every item already on the
# board at its own date, so those entries say nothing about how fast the board
# learned. Event-to-board time is measured only on items that entered from here
# on. Stated rather than inferred: a date correction to an old item would
# otherwise look like a real entry and move the start.
LEDGER_START = "2026-09-04"

# The landing page inlines every item for Explore, by design (see explore_payload
# in build.py). Past this size the build says so, which is the moment to revisit
# that trade-off rather than before.
PAGE_WEIGHT_WARN = 1_000_000

ENTITY_KINDS = {
    "lab": "AI labs", "model": "Model families", "government": "Government and public bodies",
    "research": "Research, evaluation and standards", "security": "Security companies",
    "platform": "Platforms and tools", "insurance": "Insurance", "actor": "Threat actors (by attributed nexus)",
}


def _d(iso: str) -> date:
    return date.fromisoformat(iso[:10])


def _median(xs):
    xs = sorted(xs)
    if not xs:
        return None
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2


def _pct(n, d) -> str:
    return f"{round(100 * n / d)}%" if d else "—"


def _num(x) -> str:
    if x is None:
        return "—"
    return f"{x:g}" if isinstance(x, float) else str(x)


# ---------------------------------------------------------------------------
# Load and validate
# ---------------------------------------------------------------------------

TOPICS_FILE = "topics.json"


def load_topics(root: Path):
    p = root / TOPICS_FILE
    return json.loads(p.read_text(encoding="utf-8")).get("topics", []) if p.exists() else []


def load_entities(root: Path):
    p = root / ENTITIES_FILE
    return json.loads(p.read_text(encoding="utf-8")).get("entities", []) if p.exists() else []


def validate(d: dict, entities: list, lanes: dict, topics: list):
    errors, warnings = [], []
    known = {t.get("id") for t in topics}
    for it in d.get("items", []):
        if "threads" in it:
            errors.append(f"item {it.get('id')}: 'threads' was replaced by 'topics' on 2026-09-30 — "
                          f"use topic ids from topics.json")
        ts = it.get("topics")
        if ts is None:
            continue
        if not isinstance(ts, list):
            errors.append(f"item {it.get('id')}: topics must be a list of topic ids")
            continue
        for t in ts:
            if t not in known:
                errors.append(f"item {it.get('id')}: topic '{t}' is not in topics.json "
                              f"({', '.join(sorted(k for k in known if k))})")
    tids = set()
    for n, t in enumerate(topics):
        for f in ("id", "name", "definition"):
            if not t.get(f):
                errors.append(f"topics[{n}]: missing field '{f}'")
        if t.get("id") in tids:
            errors.append(f"topics[{n}]: duplicate id {t.get('id')}")
        tids.add(t.get("id"))

    ids = set()
    for n, e in enumerate(entities):
        where = f"entities[{n}] {e.get('id', '<no id>')}"
        for f in ("id", "name", "kind", "aliases"):
            if not e.get(f):
                errors.append(f"{where}: missing field '{f}'")
        if e.get("id") in ids:
            errors.append(f"{where}: duplicate id")
        ids.add(e.get("id"))
        if e.get("id") and not all(c.isalnum() or c == "-" for c in e["id"]):
            errors.append(f"{where}: id must be kebab-case")
        if e.get("kind") and e["kind"] not in ENTITY_KINDS:
            errors.append(f"{where}: kind must be one of {', '.join(ENTITY_KINDS)}")
        if e.get("weights") and e["weights"] not in ("open", "closed"):
            errors.append(f"{where}: weights must be 'open' or 'closed'")

    item_ids = {i.get("id") for i in d.get("items", [])}
    for n, c in enumerate(d.get("corrections", [])):
        where = f"corrections[{n}]"
        for f in ("date", "text"):
            if not c.get(f):
                errors.append(f"{where}: missing field '{f}'")
        try:
            if len(c.get("date", "")) != 10:
                raise ValueError
            date.fromisoformat(c["date"])
        except (ValueError, KeyError):
            errors.append(f"{where}: date must be YYYY-MM-DD")
        if c.get("item") and c["item"] not in item_ids:
            warnings.append(f"{where}: item '{c['item']}' is no longer on the board — the "
                            f"entry will print without a link")
    return errors, warnings


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

class Insights:
    def __init__(self, d: dict, entities: list, entered: dict, lanes: dict, topics: list = ()):
        self.d = d
        self.items = sorted(d.get("items", []), key=lambda i: i["date"])
        self.entered = entered
        self.lanes = lanes
        self.entities = entities
        self.topics = list(topics)
        self.by_id = {i["id"]: i for i in self.items}
        self.tags = self._tag_entities()
        self.ent_items = {}
        for iid, eids in self.tags.items():
            for e in eids:
                self.ent_items.setdefault(e, []).append(self.by_id[iid])
        self.live_entities = [e for e in entities if self.ent_items.get(e["id"])]

    # -- entities -----------------------------------------------------------
    def _tag_entities(self):
        """Entity ids per item, longest alias first across the whole registry.

        Each match is blanked out of the text before shorter aliases are tried,
        so "Claude Code" tags the tool and not also the model family, and
        "Gemini CLI" tags the CLI and not also Gemini.
        """
        pats = sorted(((a, e["id"]) for e in self.entities for a in e.get("aliases", [])),
                      key=lambda p: -len(p[0]))
        pats = [(re.compile(rf"(?<![A-Za-z0-9]){re.escape(a)}(?![A-Za-z0-9])"), eid) for a, eid in pats]
        order = {e["id"]: n for n, e in enumerate(self.entities)}
        out = {}
        for it in self.items:
            text, hits = f'{it["headline"]} {it["core"]}', set()
            for rx, eid in pats:
                if rx.search(text):
                    hits.add(eid)
                    text = rx.sub(lambda m: "\0" * len(m.group(0)), text)
            out[it["id"]] = sorted(hits, key=order.get)
        return out

    # -- weekly trend -------------------------------------------------------
    def weeks(self):
        """[(monday, {lane: n}), ...] for every week from the first item to the run."""
        if not self.items:
            return []
        start = _d(self.d.get("coverageStart") or self.items[0]["date"])
        start -= timedelta(days=start.weekday())
        end = _d(self.d.get("updatedISO", self.items[-1]["date"]))
        out, mon = [], start
        while mon <= end:
            out.append((mon, {k: 0 for k in self.lanes}))
            mon += timedelta(weeks=1)
        idx = {m: c for m, c in out}
        for it in self.items:
            dt = _d(it["date"])
            c = idx.get(dt - timedelta(days=dt.weekday()))
            if c is not None:
                c[it["lane"]] += 1
        return out

    # -- confidence ---------------------------------------------------------
    def confidence(self):
        tab = {k: {} for k in self.lanes}
        for it in self.items:
            tab[it["lane"]][it["confidence"]] = tab[it["lane"]].get(it["confidence"], 0) + 1
        return tab

    # -- how fast the board learns ------------------------------------------
    def board_lag(self):
        """Days from an item's own date to the day it entered the board.

        The entry ledger was seeded with each item's own date when it was
        created, so items from before the ledger existed would all read as zero.
        Only items that entered on or after LEDGER_START count.
        """
        since = LEDGER_START
        lags = sorted((_d(e) - _d(i["date"])).days for i in self.items
                      if (e := self.entered.get(i["id"])) and e >= since)
        if not lags:
            return None
        return {"since": since, "n": len(lags), "median": _median(lags),
                "p90": lags[min(len(lags) - 1, int(len(lags) * 0.9))],
                "within2": sum(1 for x in lags if x <= 2)}

    # -- response lag by topic ----------------------------------------------
    # (The row key stays "thread" for the exports' field names; the unit is a topic.)
    def threads(self):
        rows = []
        for tp in self.topics:
            name = tp["name"]
            its = [i for i in self.items if tp["id"] in i.get("topics", [])]
            if not its:
                continue
            trig = [i for i in its if i["lane"] in TRIGGER_LANES]
            row = {"thread": name, "id": tp["id"], "items": its, "trigger": trig[0] if trig else None,
                   "first": {}, "lag": {}, "ahead": {}}
            for lane in RESPONSE_LANES:
                resp = [i for i in its if i["lane"] == lane]
                if row["trigger"]:
                    t = row["trigger"]["date"]
                    after = [i for i in resp if i["date"] >= t]
                    row["ahead"][lane] = any(i["date"] < t for i in resp)
                    if after:
                        row["first"][lane] = after[0]
                        row["lag"][lane] = (_d(after[0]["date"]) - _d(t)).days
            rows.append(row)
        return rows

    def lag_summary(self, rows=None):
        rows = self.threads() if rows is None else rows
        started = [r for r in rows if r["trigger"]]
        out = {"threads": len(started)}
        for lane in RESPONSE_LANES:
            lags = [r["lag"][lane] for r in started if lane in r["lag"]]
            open_days = [(_d(self.d["updatedISO"][:10]) - _d(r["trigger"]["date"])).days
                         for r in started if lane not in r["lag"]]
            out[lane] = {"n": len(lags), "median": _median(lags),
                         "open": len(started) - len(lags), "min_open": min(open_days, default=0),
                         "ahead": sum(1 for r in started if r["ahead"].get(lane))}
        return out

    # -- headline numbers ---------------------------------------------------
    def headline(self):
        n = len(self.items)
        conf = {}
        for it in self.items:
            conf[it["confidence"]] = conf.get(it["confidence"], 0) + 1
        cap = [i for i in self.items if i["lane"] == "cap"]
        cap_self = sum(1 for i in cap if i["confidence"] == "self-reported")
        models = [e for e in self.live_entities if e.get("kind") == "model" and e.get("weights")]
        mcount = {"open": set(), "closed": set()}
        for e in models:
            for it in self.ent_items[e["id"]]:
                mcount[e["weights"]].add(it["id"])
        return {"n": n, "confirmed": conf.get("confirmed", 0), "on_record": conf.get("on-record", 0),
                "cap": len(cap), "cap_self": cap_self,
                "open_items": len(mcount["open"]), "closed_items": len(mcount["closed"])}

    # -- exports ------------------------------------------------------------
    def export_items(self):
        return [dict(i, entities=self.tags.get(i["id"], []), topics=i.get("topics", []),
                     entered=self.entered.get(i["id"], i["date"]))
                for i in self.items]

    def items_json(self, meta: dict) -> str:
        rows = [{k: v for k, v in r.items() if k != "isNew"} for r in self.export_items()]
        return json.dumps(dict(meta, items=rows), ensure_ascii=False, indent=1) + "\n"

    def items_csv(self) -> str:
        buf = io.StringIO()
        cols = ["id", "date", "entered", "lane", "confidence", "headline", "core", "outlet",
                "url", "topics", "entities"]
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(cols)
        for r in self.export_items():
            w.writerow([r["id"], r["date"], r["entered"], r["lane"], r["confidence"],
                        r["headline"], r["core"], r["outlet"], r["url"],
                        "; ".join(r["topics"]), "; ".join(r["entities"])])
        return buf.getvalue()

    def threads_json(self) -> str:
        out = []
        for r in self.threads():
            out.append({
                "topic": r["id"], "name": r["thread"], "items": [i["id"] for i in r["items"]],
                "trigger": r["trigger"] and {"id": r["trigger"]["id"], "date": r["trigger"]["date"],
                                             "lane": r["trigger"]["lane"]},
                "firstResponse": {k: {"id": v["id"], "date": v["date"], "lagDays": r["lag"][k]}
                                  for k, v in r["first"].items()},
            })
        return json.dumps(out, ensure_ascii=False, indent=1) + "\n"


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def _tile(n, label, sub="") -> str:
    s = f'<div class="d">{escape(sub)}</div>' if sub else ""
    return f'<div class="stat"><div class="n">{n}</div><div class="l">{escape(label)}</div>{s}</div>'


def _short(dt: date) -> str:
    return f'{["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][dt.month-1]} {dt.day}'


def multiples(ins: Insights, lanes: dict) -> str:
    """Weekly items per lane as small multiples on one shared scale.

    Columns rather than a stacked chart: five series stacked hide every lane
    but the bottom one. The last week is usually still in progress and is
    drawn faded and labelled so, rather than read as a fall.
    """
    wk = ins.weeks()
    if not wk:
        return ""
    last_full = _d(ins.d.get("updatedISO", "")[:10]).weekday() == 6
    # The first week usually starts before the board does; label it by the
    # board's first day so the axis never claims days it does not cover.
    first_day = max(wk[0][0], _d(ins.d.get("coverageStart") or ins.items[0]["date"]))
    mx = max(max(c.values()) for _, c in wk) or 1
    panels = []
    for k, v in lanes.items():
        total = sum(c[k] for _, c in wk)
        cols = []
        for n, (mon, c) in enumerate(wk):
            partial = (n == len(wk) - 1 and not last_full) or (n == 0 and first_day > mon)
            h = c[k] / mx * 100
            tip = (f'{v["name"]}, week of {_short(mon)}: {c[k]} item{"" if c[k] == 1 else "s"}'
                   + ((" (week in progress)" if n else f" (from {_short(first_day)}, when the board begins)")
                      if partial else ""))
            cols.append(f'<span class="ms-col{" partial" if partial else ""}" title="{escape(tip, quote=True)}">'
                        f'<i style="height:{h:.1f}%"></i></span>')
        panels.append(
            f'<div class="ms-mini"><div class="ms-mhead"><span class="sw" style="background:var(--{k}-mark)"></span>'
            f'{v["name"]}<b>{total}</b></div>'
            f'<div class="ms-cols" style="--c:var(--{k}-mark)" role="img" '
            f'aria-label="{v["name"]}: weekly items, {", ".join(str(c[k]) for _, c in wk)}">{"".join(cols)}</div>'
            f'<div class="ms-axis"><span>{_short(first_day)}</span><span>{_short(wk[-1][0])}</span></div></div>')
    table_rows = "".join(
        f'<tr><td>{_short(mon)}</td>' + "".join(f"<td>{c[k]}</td>" for k in lanes) + "</tr>"
        for mon, c in reversed(wk))
    table = (f'<details class="notebox ms-table"><summary>Show as a table</summary>'
             f'<table class="fc-cal"><thead><tr><th scope="col">Week of</th>'
             + "".join(f'<th scope="col">{v["name"]}</th>' for v in lanes.values())
             + f'</tr></thead><tbody>{table_rows}</tbody></table></details>')
    return (f'<p class="lede">Items per week, by the date of the event. One scale across all five '
            f'lanes (tallest column: {mx}). Hover a column for its count.'
            + " Faded columns are part-weeks: the board's first, and the week in progress." + '</p>'
            f'<div class="ms-multiples">{"".join(panels)}</div>{table}')


def lag_block(ins: Insights, lanes: dict, site) -> str:
    rows = ins.threads()
    s = ins.lag_summary(rows)
    started = [r for r in rows if r["trigger"]]
    if not started:
        return '<p class="lede">No topic has a capability or attack item yet.</p>'
    lo = _d(ins.d.get("coverageStart") or ins.items[0]["date"])
    hi = _d(ins.d.get("updatedISO")[:10])
    span = max(1, (hi - lo).days)

    def x(iso):
        return max(0.0, min(100.0, (_d(iso) - lo).days / span * 100))

    def cell(r, lane):
        if lane in r["lag"]:
            f = r["first"][lane]
            href = f'{site.prefix}{lanes[f["lane"]]["page"]}#{escape(f["id"])}'
            note = ' <span class="ahead" title="An item in this lane predates the topic\'s first capability or attack item">*</span>' if r["ahead"].get(lane) else ""
            return f'<td class="num"><a href="{href}" title="{escape(f["headline"], quote=True)}">{r["lag"][lane]} d</a>{note}</td>'
        days = (hi - _d(r["trigger"]["date"])).days
        note = "*" if r["ahead"].get(lane) else ""
        # Markets rarely answers a topic at all, so its open count is noise;
        # it keeps the dash and moves the day count to the tooltip.
        shown = "" if lane == "mkt" else f" <small>{days} d open</small>"
        return (f'<td class="num open" title="No {lanes[lane]["name"].lower()} item on the board yet, '
                f'{days} days on">—{shown}{note}</td>')

    body = []
    for r in sorted(started, key=lambda r: r["trigger"]["date"]):
        dots = "".join(
            f'<i class="{"trig" if i["lane"] in TRIGGER_LANES else "resp"}" '
            f'style="left:{x(i["date"]):.2f}%;background:var(--{i["lane"]}-mark)" '
            f'title="{escape(lanes[i["lane"]]["name"] + " · " + i["date"] + " · " + i["headline"], quote=True)}"></i>'
            for i in r["items"])
        t = r["trigger"]
        body.append(
            f'<tr><th scope="row">{escape(r["thread"])}<small>{len(r["items"])} items · starts '
            f'{_short(_d(t["date"]))} ({lanes[t["lane"]]["name"].lower()})</small></th>'
            f'{cell(r, "pol")}{cell(r, "def")}{cell(r, "mkt")}'
            f'<td class="strip"><span class="track">{dots}</span></td></tr>')
    months, m = [], date(lo.year, lo.month, 1)
    while m <= hi:
        if m >= lo:
            months.append(f'<span style="left:{x(m.isoformat()):.2f}%">{_short(m).split()[0]}</span>')
        m = date(m.year + (m.month // 12), m.month % 12 + 1, 1)
    legend = "".join(f'<span><i style="background:var(--{k}-mark)"></i>{lanes[k]["name"]}</span>'
                     for k in list(TRIGGER_LANES) + list(RESPONSE_LANES))
    return f"""<div class="lagwrap"><table class="lagtab">
      <thead><tr><th scope="col">Topic</th><th scope="col" class="num">Policy</th>
        <th scope="col" class="num">Defense</th><th scope="col" class="num">Markets</th>
        <th scope="col" class="strip"><span class="months">{"".join(months)}</span></th></tr></thead>
      <tbody>{"".join(body)}</tbody></table></div>
    <div class="ms-legend">{legend}</div>
    <p class="note">Days from each topic's first capability or attack item to its first item
      in each response lane. “— n d open” means nothing yet, n days on. * marks a lane that had
      already moved before the topic's first capability or attack item. Items are assigned to
      topics by the editor; the board begins on {escape(site.coverage.split(" – ")[0])}, so a topic whose story
      began earlier starts its clock late.</p>"""


def findings_body(site, ins: Insights, lanes: dict, conf_labels: dict) -> str:
    h = ins.headline()
    bl = ins.board_lag()
    ls = ins.lag_summary()
    tiles = [
        _tile(h["n"], "Items on the board", site.coverage),
        _tile(_pct(h["confirmed"], h["n"]), "Confirmed by the affected organisation",
              f'{h["confirmed"]} of {h["n"]}'),
        _tile(_pct(h["cap_self"], h["cap"]), "Capability items resting on self-reported claims",
              f'{h["cap_self"]} of {h["cap"]}'),
    ]
    if ls.get("pol", {}).get("n"):
        tiles.append(_tile(f'{_num(ls["pol"]["median"])} d', "Median policy lag, where policy has answered",
                           f'{ls["pol"]["n"]} of {ls["threads"]} topics; {ls["pol"]["open"]} still open, '
                           f'the shortest {ls["pol"]["min_open"]} days'))
    if bl:
        tiles.append(_tile(f'{_num(bl["median"])} d', "Median event-to-board time",
                           f'{_pct(bl["within2"], bl["n"])} within two days'))

    ct = ins.confidence()
    tiers = list(conf_labels)
    conf_rows = "".join(
        f'<tr><th scope="row">{v["name"]}</th>'
        + "".join(f'<td class="num">{_pct(ct[k].get(t, 0), sum(ct[k].values()))}</td>' for t in tiers)
        + f'<td class="num">{sum(ct[k].values())}</td></tr>' for k, v in lanes.items())
    conf_table = (f'<div class="lagwrap"><table class="fc-cal conftab"><thead><tr><th scope="col">Lane</th>'
                  + "".join(f'<th scope="col" class="num">{escape(conf_labels[t])}</th>' for t in tiers)
                  + f'<th scope="col" class="num">Items</th></tr></thead><tbody>{conf_rows}</tbody></table></div>')

    models = ""
    if h["open_items"] or h["closed_items"]:
        models = (f'<p class="lede" style="margin-top:14px">Items naming an open-weight model family: <b>{h["open_items"]}</b>. '
                  f'Naming a closed one: <b>{h["closed_items"]}</b>. Counted from the '
                  f'<a href="{site.prefix}{ENTITIES_URL}">entity index</a>, which marks weights only where the '
                  f'board’s own items establish them.</p>')

    lag_note = (f'Measured on the {bl["n"]} items that entered since the entry ledger began on '
                f'{_short(_d(bl["since"]))}: median {_num(bl["median"])} days from the event to the board, '
                f'90th percentile {bl["p90"]} days.') if bl else ""

    return f"""{site.nav(FINDINGS_URL)}

  <header class="pagehead">
    <h1>Findings</h1>
    <div class="sub">What the board shows when it is counted, rather than read. Every number
      is computed from the sourced items at build time; nothing on this page is a claim the
      items do not carry. {escape(site.coverage)}.</div>
  </header>

  <div class="stats">{"".join(tiles)}</div>

  <section class="block"><h2 class="blockhead">The lag — response time by topic</h2>
    {lag_block(ins, lanes, site)}
  </section>

  <section class="block"><h2 class="blockhead">Weekly items by lane</h2>
    {multiples(ins, lanes)}
  </section>

  <section class="block"><h2 class="blockhead">What kind of claim each lane rests on</h2>
    <p class="lede">Share of each lane's items by confidence tier. The tier describes the kind
      of claim, not the publisher — see the <a href="{site.prefix}{METHOD_URL}">methodology</a>.</p>
    {conf_table}
    {models}
  </section>

  <section class="block"><h2 class="blockhead">How fast the board learns</h2>
    <p class="lede">{lag_note} Counts throughout measure what this board tracked, not
      everything that happened; the source list has grown since July, which lifts later weeks.</p>
    <p class="lede">The underlying data is <a href="{site.prefix}{DATA_URL}">open for reuse</a>.</p>
  </section>

  {site.footer()}"""


def entities_body(site, ins: Insights) -> str:
    groups = []
    for kind, label in ENTITY_KINDS.items():
        es = sorted((e for e in ins.live_entities if e["kind"] == kind),
                    key=lambda e: -len(ins.ent_items[e["id"]]))
        if not es:
            continue
        cards = "".join(
            f'<a href="{site.prefix}entity/{e["id"]}/"><span class="d">{escape(e["name"])}'
            + (f' <small class="wt">{e["weights"]} weights</small>' if e.get("weights") else "")
            + f'</span><span class="m">{len(ins.ent_items[e["id"]])} items · last '
              f'{_short(_d(ins.ent_items[e["id"]][-1]["date"]))}</span></a>' for e in es)
        groups.append(f'<section class="block"><h2 class="blockhead">{label}</h2>'
                      f'<div class="arch">{cards}</div></section>')
    return f"""{site.nav(ENTITIES_URL)}

  <header class="pagehead">
    <h1>Entities</h1>
    <div class="sub">Every organisation, model family and platform the board's items name,
      with the items that name it. Tagged automatically from each item's headline and summary.</div>
  </header>

  {"".join(groups)}

  {site.footer()}"""


def entity_body(site, ins: Insights, e: dict, lanes: dict) -> str:
    its = list(reversed(ins.ent_items[e["id"]]))
    mix = " · ".join(f'{v["name"]} {n}' for k, v in lanes.items()
                     if (n := sum(1 for i in its if i["lane"] == k)))
    weights = f' · {e["weights"]} weights' if e.get("weights") else ""
    return f"""{site.nav(ENTITIES_URL)}

  <header class="pagehead">
    <h1>{escape(e["name"])}</h1>
    <div class="sub">{len(its)} items{weights} · {escape(mix)} ·
      <a href="{site.prefix}{ENTITIES_URL}">all entities</a></div>
  </header>

  <div class="lanes lanes-single"><section class="lane">{"".join(site.item_card(i) for i in its)}</section></div>

  {site.footer()}"""


def data_body(site, ins: Insights, citation: str) -> str:
    return f"""{site.nav(DATA_URL)}

  <header class="pagehead">
    <h1>Data</h1>
    <div class="sub">The whole board as open data, rebuilt with every update.</div>
  </header>

  <div class="stats">
    {_tile(len(ins.items), "Items", site.coverage)}
    {_tile(len(ins.live_entities), "Entities tagged")}
    {_tile(len([r for r in ins.threads()]), "Topics")}
  </div>

  <section class="block"><h2 class="blockhead">Download</h2>
    <div class="arch">
      <a href="items.csv"><span class="d">items.csv</span><span class="m">One row per item — opens in any spreadsheet</span></a>
      <a href="items.json"><span class="d">items.json</span><span class="m">The same, with metadata, for code</span></a>
      <a href="topics.json"><span class="d">topics.json</span><span class="m">Topic membership and response lags</span></a>
    </div>
  </section>

  <section class="block"><h2 class="blockhead">Licence and citation</h2>
    <div class="prose">
      <p>Released under <a href="{DATA_LICENSE_URL}" target="_blank" rel="noopener">{DATA_LICENSE} ↗</a>:
        reuse it for anything, with credit. Each item's summary is the board's own wording; the
        linked sources belong to their publishers.</p>
      <p><b>Cite as:</b> {escape(citation)}</p>
    </div>
  </section>

  <section class="block"><h2 class="blockhead">Fields</h2>
    <div class="prose">
      <p><b>id</b> stable identifier · <b>date</b> when the event happened or was published ·
        <b>entered</b> when the board recorded it · <b>lane</b> capability, policy, defense,
        attacks or markets · <b>confidence</b> the kind of claim (see the
        <a href="{site.prefix}{METHOD_URL}">methodology</a>) · <b>headline</b>, <b>core</b> the
        board's summary · <b>outlet</b>, <b>url</b> the source · <b>topics</b> the
        subjects the editor assigned · <b>entities</b> names tagged automatically.</p>
      <p>Items are corrected in place; the <a href="{site.prefix}{CORRECTIONS_URL}">corrections log</a>
        records every change to a published item.</p>
    </div>
  </section>

  {site.footer()}"""


def methodology_body(site, conf_labels: dict, show_findings: bool = True) -> str:
    tiers = {
        "confirmed": "The organisation that was affected says it happened to them.",
        "claimed": "The attacker says they did it, and nobody else has stood behind it.",
        "researchers": "Security researchers reported it and the victim has not confirmed.",
        "press": "Established press reported it and no primary source could be opened.",
        "on-record": "A statement the speaker has formally put in its own name, where it is the only "
                     "possible authority and the statement is itself the event: a bill is introduced, an "
                     "agency issues an alert, a lab discloses what its own model did.",
        "self-reported": "A testable claim where the party measuring is the party being measured and no "
                         "one independent has checked: benchmark scores, capability assertions, launches "
                         "written to read as findings. Flagged, not endorsed.",
    }
    analysis = (f' Analysis lives on separate pages: <a href="{site.prefix}{FINDINGS_URL}">Findings</a> '
                f'counts the board, and any forecasts are published apart from it, signed and scored.'
                if show_findings else "")
    rows = "".join(f'<tr><td class="thread"><span class="conf c-{k}">{escape(conf_labels.get(k, k))}</span></td>'
                   f'<td class="status">{escape(v)}</td></tr>' for k, v in tiers.items() if k in conf_labels)
    return f"""{site.nav(METHOD_URL)}

  <header class="pagehead">
    <h1>Methodology</h1>
    <div class="sub">How items get on the board, and what each label means.</div>
  </header>

  <section class="block"><h2 class="blockhead">Sourcing</h2>
    <div class="prose">
      <p>Every item cites a source that was opened and read. Primary sources come first: the lab's
        own report, the agency's own page, the vendor's own advisory. Press is a fallback when the
        primary cannot be reached, and an item carried on press is upgraded when the primary opens.</p>
      <p>Nothing is invented or estimated. A CVE number, figure, date or quote that cannot be verified
        is dropped rather than guessed. Where sources disagree on a figure, the primary wins and the
        disagreement is noted. The same event arriving from several directions is filed once.</p>
      <p>The board reports; it does not recommend or forecast.{analysis}</p>
      <p>An empty lane on a quiet day is the honest outcome. Lanes are never padded.</p>
    </div>
  </section>

  <section class="block"><h2 class="blockhead">Confidence tiers</h2>
    <p class="lede">A tier describes the kind of claim, not the identity of the publisher. The same
      lab can land in two tiers in one post: “our model escaped its sandbox” is on the record;
      “our model scores 92% on a cyber benchmark” is self-reported.</p>
    <table class="watch"><tbody>{rows}</tbody></table>
  </section>

  <section class="block"><h2 class="blockhead">Lanes and dates</h2>
    <div class="prose">
      <p>Each item sits in one lane: what AI systems can now do (Capability), what governments and
        standards bodies do about it (Policy), defensive tooling and guidance (Defense), real-world
        incidents (Attacks), and how insurers and investors price the risk (Markets). An item's date
        is when the event happened or was published; the board separately records when it learned
        of it.</p>
      <p>Mistakes are corrected on the item itself and logged in public on the
        <a href="{site.prefix}{CORRECTIONS_URL}">corrections page</a>. Dated snapshots in the archive
        are never edited.</p>
    </div>
  </section>

  {site.footer()}"""


def corrections_body(site, lanes: dict) -> str:
    cs = sorted(site.d.get("corrections", []), key=lambda c: c["date"], reverse=True)
    rows = []
    for c in cs:
        it = site.by_id.get(c.get("item", ""))
        link = (f'<a href="{site.prefix}{lanes[it["lane"]]["page"]}#{escape(it["id"])}">{escape(it["headline"])}</a>'
                if it else escape(c.get("item", "")))
        rows.append(f'<tr><td class="when"><time datetime="{c["date"]}">{_short(_d(c["date"]))}, '
                    f'{c["date"][:4]}</time></td><td class="status">{link}'
                    f'<p>{escape(c["text"])}</p></td></tr>')
    table = (f'<table class="corr"><tbody>{"".join(rows)}</tbody></table>' if rows
             else '<p class="lede">No corrections recorded yet.</p>')
    return f"""{site.nav(CORRECTIONS_URL)}

  <header class="pagehead">
    <h1>Corrections</h1>
    <div class="sub">Every material change to an item after it was published: a wrong date, a
      figure the primary source did not support, a claim tied to the wrong event. Sourcing
      upgrades that change nothing a reader relied on are not listed.</div>
  </header>

  <section class="block"><h2 class="blockhead">{len(cs)} correction{"" if len(cs) == 1 else "s"}</h2>
    {table}
  </section>

  {site.footer()}"""


# ---------------------------------------------------------------------------
# Drafts for a human — written into newsletter/, never published by the build
# ---------------------------------------------------------------------------

def weekly_draft(ins: Insights, lanes: dict, site_url: str, conf_labels: dict) -> tuple:
    run = _d(ins.d["updatedISO"][:10])
    mon = run - timedelta(days=run.weekday())
    week = [i for i in ins.items if mon <= _d(i["date"]) <= mon + timedelta(days=6)]
    prior = [c for m, c in ins.weeks() if mon - timedelta(weeks=8) <= m < mon]
    days = min(7, (run - mon).days + 1)
    lines = [f"# Machine Speed — week of {_short(mon)}, {mon.year}", "",
             "> DRAFT for a human. Pick the five items that matter most, write one line on why each",
             "> matters, and delete the rest. Nothing here is sent.", "",
             f"## The week in numbers ({days} of 7 days so far; averages scaled to match)", ""]
    for k, v in lanes.items():
        n = sum(1 for i in week if i["lane"] == k)
        avg = sum(c[k] for c in prior) / len(prior) * days / 7 if prior else 0
        lines.append(f"- {v['name']}: {n} (8-week average for {days} days: {avg:.1f})")
    lines += ["", "## Candidates — pick five", ""]
    for k, v in lanes.items():
        its = [i for i in week if i["lane"] == k]
        if not its:
            continue
        lines += [f"### {v['name']}", ""]
        for i in sorted(its, key=lambda x: x["date"], reverse=True):
            lines.append(f"- [ ] **{i['headline']}** — {conf_labels.get(i['confidence'], '')}, "
                         f"{i['outlet']}, {i['date']}. {site_url}/{v['page']}#{i['id']}")
        lines.append("")
    return f"newsletter/weekly-{mon.isoformat()}.md", "\n".join(lines) + "\n"


def _quarter(day: date):
    q = (day.month - 1) // 3
    qs = date(day.year, q * 3 + 1, 1)
    qe = date(day.year + (q == 3), (q * 3 + 3) % 12 + 1, 1) - timedelta(days=1)
    return q, qs, qe


# Items keep arriving for days after the event, so a quarter that has just
# closed keeps being redrafted, now marked complete, for this long after.
QUARTER_GRACE_DAYS = 14


def quarterly_drafts(ins: Insights, lanes: dict, site_url: str, conf_labels: dict):
    """The current quarter's draft, plus the last one while it is still settling."""
    run = _d(ins.d["updatedISO"][:10])
    out = [quarterly_draft(ins, lanes, site_url, conf_labels, run)]
    _, qs, _ = _quarter(run)
    if (run - qs).days < QUARTER_GRACE_DAYS:
        out.append(quarterly_draft(ins, lanes, site_url, conf_labels, qs - timedelta(days=1)))
    return out


def quarterly_draft(ins: Insights, lanes: dict, site_url: str, conf_labels: dict, day: date) -> tuple:
    run = _d(ins.d["updatedISO"][:10])
    q, qs, qe = _quarter(day)
    its = [i for i in ins.items if qs <= _d(i["date"]) <= qe]
    label = f"Q{q + 1} {qs.year}"
    status = "complete" if run > qe else f"to date — the quarter closes {qe.isoformat()}"
    n = len(its)
    conf = {}
    for i in its:
        conf[i["confidence"]] = conf.get(i["confidence"], 0) + 1
    ls = ins.lag_summary()
    lines = [f"# State of AI-Cyber — {label}", "",
             f"> DRAFT ({status}). Every number below is computed from the board; the sections marked",
             "> WRITE are for you. Nothing here is published by the build.", "",
             "## Summary", "", "WRITE: three sentences — what changed this quarter, and why it matters.", "",
             "## By the numbers", "",
             f"- {n} source-verified items, {qs.isoformat()} to {min(run, qe).isoformat()}."]
    for k, v in lanes.items():
        lines.append(f"  - {v['name']}: {sum(1 for i in its if i['lane'] == k)}")
    lines += [f"- Confirmed by the affected organisation: {conf.get('confirmed', 0)} of {n} ({_pct(conf.get('confirmed', 0), n)}).",
              f"- Resting on self-reported, untested claims: {conf.get('self-reported', 0)} ({_pct(conf.get('self-reported', 0), n)})."]
    for lane, word in (("pol", "policy"), ("def", "defense")):
        s = ls.get(lane, {})
        if s.get("n"):
            lines.append(f"- Median {word} response lag, since the board began, among topics {word} has answered: {_num(s['median'])} days "
                         f"({s['n']} of {ls['threads']} topics have a {word} response; {s['open']} still open).")
    lines += ["", f"## The lag, topic by topic (since the board began, {ins.items[0]['date']})", ""]
    for r in sorted((r for r in ins.threads() if r["trigger"]), key=lambda r: r["trigger"]["date"]):
        pol = f"{r['lag']['pol']} days" if "pol" in r["lag"] else "none yet"
        dfn = f"{r['lag']['def']} days" if "def" in r["lag"] else "none yet"
        lines.append(f"- **{r['thread']}** — starts {r['trigger']['date']}; policy {pol}; defense {dfn}.")
    lines += ["", "## Most-named entities", ""]
    counts = sorted(((sum(1 for i in ins.ent_items[e["id"]] if qs <= _d(i["date"]) <= qe), e)
                     for e in ins.live_entities), key=lambda x: -x[0])[:12]
    lines += [f"- {e['name']}: {c}" for c, e in counts if c]
    lines += ["", "## Three stories that defined the quarter", "",
              "WRITE: pick three topics above; for each, one paragraph and the key items.", "",
              "## What to watch next quarter", "",
              "WRITE: point to open forecasts on the Forecasts page rather than forecasting here.", "",
              f"Data: {site_url}/{DATA_URL} ({DATA_LICENSE})", ""]
    return f"newsletter/quarterly-{qs.year}-q{q + 1}.md", "\n".join(lines)
