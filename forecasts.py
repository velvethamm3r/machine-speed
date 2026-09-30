"""
Machine Speed — forecasts.

The board reports; it does not forecast. DAILY_RUN.md says so in as many words,
and that rule still binds every daily run. This module is the one place the
analyst does forecast, kept on its own page and in its own file so a forecast
can never be mistaken for a sourced item.

    forecasts.json        the forecasts and their resolutions — written by hand,
                          never by a daily run
    forecasts.lock.json   the integrity ledger — written by the build, committed
                          by the GitHub Action, never edited by hand

A forecast record is only worth anything if it cannot be quietly improved after
the fact. So the lock stores a fingerprint of every forecast and every
resolution the first time a build sees it, and validate() refuses a build in
which any of them has changed. The way to change your mind is a new forecast
that `supersedes` the old one; both stay on the record and both are scored.
Git history is the second witness: the lock says when a forecast was first
seen, and the commit that introduced it says the same thing independently.

Two kinds of forecast:

  judgment  A question about the world, resolved by hand with a source,
            exactly as a board item is sourced.
  board     A question about the board's own counts ("at least 60 Attacks
            items dated Oct 1 – Dec 31"). The build resolves these itself once
            the window has closed and a grace period for late-arriving items has
            passed, then freezes the answer in the lock. Each also gets a
            baseline: the probability a naive model (the lane's recent weekly
            rate, Poisson) would have given on the day the forecast was made.
            Scoring the analyst against that baseline is the honest test of
            whether judgment adds anything to the trend line.

Scoring is the Brier score: (probability − outcome)², outcome 1 or 0, averaged.
0 is perfect, 0.25 is what always saying 50% earns, lower is better.

Python 3 standard library only, like build.py.
"""

import hashlib
import json
import math
import os
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

FORECASTS_FILE = "forecasts.json"
LOCK_FILE = "forecasts.lock.json"
FORECASTS_URL = "forecasts/"

# Board forecasts count items by their event date, but items keep arriving for
# days after the event — the board's measured tail runs four days and more. A
# window is only counted once this many days have passed since it closed, and
# the count is then frozen, so a late item can never flip a resolved forecast.
GRACE_DAYS = 7

# How many full Monday–Sunday weeks before a board forecast's `made` date feed
# its baseline rate, and the fewest that must exist for a baseline to be given.
BASELINE_WEEKS = 8
BASELINE_MIN_WEEKS = 4

# A new forecast whose `made` date is more than this many days before the build
# that first logs it is refused in CI: that is a forecast written with hindsight.
# Locally it is only a warning, because a laptop's lock can be stale and a daily
# run must never be blocked by a file it does not own.
BACKDATE_SLACK_DAYS = 2

P_MIN, P_MAX = 0.01, 0.99
OUTCOMES = ("yes", "no", "void")


def _today() -> str:
    # UTC, because the lock is written by the GitHub runner, which runs on UTC.
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _in_ci() -> bool:
    return os.environ.get("GITHUB_ACTIONS") == "true"


def _d(iso: str):
    return datetime.strptime(iso, "%Y-%m-%d").date()


def _fingerprint(obj: dict) -> str:
    blob = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _kebab(s: str) -> bool:
    return bool(s) and all(c.isalnum() or c == "-" for c in s)


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def load(root: Path):
    """(forecasts dict or None, lock dict). None means the feature is off."""
    p = root / FORECASTS_FILE
    fc = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
    lp = root / LOCK_FILE
    lock = (json.loads(lp.read_text(encoding="utf-8")) if lp.exists()
            else {"forecasts": {}, "resolutions": {}, "auto": {}})
    for k in ("forecasts", "resolutions", "auto"):
        lock.setdefault(k, {})
    return fc, lock


# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------

def validate(fc: dict, lock: dict, items: list, lanes: dict):
    """(errors, warnings). Same contract as build.validate: errors stop the build."""
    errors, warnings = [], []
    if fc is None:
        return errors, warnings
    today = _today()
    item_ids = {i.get("id") for i in items}
    seen = {}

    for n, f in enumerate(fc.get("forecasts", [])):
        fid = f.get("id", "")
        where = f"forecast[{n}] {fid or '<no id>'}"
        kind = f.get("kind", "judgment")
        for key in ("id", "made", "question", "p", "criteria"):
            if f.get(key) in (None, ""):
                errors.append(f"{where}: missing field '{key}'")
        if not _kebab(fid):
            errors.append(f"{where}: id must be kebab-case (letters, digits, hyphens)")
        if fid in seen:
            errors.append(f"{where}: duplicate id")
        seen[fid] = f
        if kind not in ("judgment", "board"):
            errors.append(f"{where}: kind must be 'judgment' or 'board'")

        p = f.get("p")
        if not isinstance(p, (int, float)) or isinstance(p, bool) or not P_MIN <= p <= P_MAX:
            errors.append(f"{where}: p must be a number from {P_MIN} to {P_MAX} — "
                          f"0 and 1 are not forecasts, and one wrong call at either "
                          f"would cost the maximum score")

        try:
            made = _d(f["made"])
        except (KeyError, ValueError):
            errors.append(f"{where}: made must be YYYY-MM-DD")
            continue
        if made > _d(today) + timedelta(days=1):
            errors.append(f"{where}: made is in the future ({f['made']})")

        if f.get("lane") and f["lane"] not in lanes:
            errors.append(f"{where}: lane must be one of {', '.join(lanes)}")
        for iid in f.get("items", []):
            if iid not in item_ids:
                errors.append(f"{where}: refers to board item '{iid}', which is not in items[]")

        if kind == "judgment":
            try:
                if _d(f["resolveBy"]) < made:
                    errors.append(f"{where}: resolveBy is before made")
            except (KeyError, ValueError):
                errors.append(f"{where}: resolveBy must be YYYY-MM-DD")
        else:
            m = f.get("metric") or {}
            if m.get("lane") not in lanes:
                errors.append(f"{where}: metric.lane must be one of {', '.join(lanes)}")
            if not isinstance(m.get("atLeast"), int) or m.get("atLeast", -1) < 0:
                errors.append(f"{where}: metric.atLeast must be a whole number, 0 or more")
            try:
                lo, hi = _d(m["from"]), _d(m["to"])
                if hi < lo:
                    errors.append(f"{where}: metric window runs backwards")
                # A board forecast about a window that has already begun is partly
                # a report of what the board already shows.
                if lo <= made:
                    errors.append(f"{where}: metric.from must be after made — a board "
                                  f"forecast has to be about days that have not happened yet")
            except (KeyError, ValueError):
                errors.append(f"{where}: metric.from and metric.to must be YYYY-MM-DD")

        sup = f.get("supersedes")
        if sup:
            if sup == fid:
                errors.append(f"{where}: a forecast cannot supersede itself")
            elif sup not in seen:
                errors.append(f"{where}: supersedes '{sup}', which is not an earlier forecast "
                              f"in the file (list the original first)")
            elif seen[sup].get("made", "") > f["made"]:
                errors.append(f"{where}: supersedes a forecast made after it")

        # The integrity check. A forecast already in the lock must be byte-for-byte
        # what it was when first logged.
        entry = lock["forecasts"].get(fid)
        if entry and entry.get("hash") != _fingerprint(f):
            errors.append(f"{where}: changed after it was logged on {entry.get('firstSeen')}. "
                          f"Forecasts are append-only — restore the original and add a new "
                          f"forecast with \"supersedes\": \"{fid}\"")
        if not entry:
            lag = (_d(today) - made).days
            if lag > BACKDATE_SLACK_DAYS:
                msg = (f"{where}: made {f['made']} but first logged {today}, {lag} days "
                       f"later — a forecast is only worth scoring if it was on the record "
                       f"before the outcome could be known")
                (errors if _in_ci() else warnings).append(msg)

    ids = set(seen)
    resolved = set()
    for n, r in enumerate(fc.get("resolutions", [])):
        rid = r.get("id", "")
        where = f"resolution[{n}] {rid or '<no id>'}"
        if rid not in ids:
            errors.append(f"{where}: no forecast with that id")
            continue
        if rid in resolved:
            errors.append(f"{where}: resolved twice")
        resolved.add(rid)
        if r.get("outcome") not in OUTCOMES:
            errors.append(f"{where}: outcome must be one of {', '.join(OUTCOMES)}")
        f = seen[rid]
        if f.get("kind") == "board" and r.get("outcome") != "void":
            errors.append(f"{where}: board forecasts resolve themselves from the board's "
                          f"counts; the only hand resolution allowed is 'void'")
        try:
            if _d(r["date"]) < _d(f["made"]):
                errors.append(f"{where}: resolved before the forecast was made")
        except (KeyError, ValueError):
            errors.append(f"{where}: date must be YYYY-MM-DD")
        if r.get("outcome") in ("yes", "no"):
            src = r.get("source") or {}
            if not str(src.get("url", "")).startswith("https://") or not src.get("outlet"):
                errors.append(f"{where}: a yes/no resolution needs a source with an https:// "
                              f"url and an outlet — the same rule as a board item")
        elif r.get("outcome") == "void" and not r.get("note"):
            errors.append(f"{where}: a void resolution needs a note saying why")
        entry = lock["resolutions"].get(rid)
        if entry and entry.get("hash") != _fingerprint(r):
            errors.append(f"{where}: changed after it was logged on {entry.get('firstSeen')} "
                          f"— resolutions are append-only too")

    for fid in lock["forecasts"]:
        if fid not in ids:
            errors.append(f"forecast '{fid}' is in {LOCK_FILE} but has been removed from "
                          f"{FORECASTS_FILE} — a forecast that went badly still stays on the record")

    for fid, f in seen.items():
        if fid in resolved or f.get("kind") == "board":
            continue
        try:
            overdue = (_d(today) - _d(f["resolveBy"])).days
        except (KeyError, ValueError):
            continue
        if overdue > 0:
            warnings.append(f"forecast '{fid}' passed its resolveBy date {overdue} day(s) ago "
                            f"and has no resolution yet")

    return errors, warnings


# ---------------------------------------------------------------------------
# Lock, baselines and auto-resolution
# ---------------------------------------------------------------------------

def _poisson_at_least(k: int, lam: float) -> float:
    if k <= 0:
        return 1.0
    term, cdf = math.exp(-lam), 0.0
    for i in range(k):
        cdf += term
        term *= lam / (i + 1)
    return max(0.0, 1.0 - cdf)


def baseline(f: dict, items: list, entered: dict):
    """What the lane's recent rate alone would have said, as of f['made'].

    Only items the board had actually logged by that day count (entry date from
    entered.json, falling back to the item date), so the baseline never sees
    anything the forecaster could not have seen.
    """
    m = f["metric"]
    made = _d(f["made"])
    this_monday = made - timedelta(days=made.weekday())
    start = this_monday - timedelta(weeks=BASELINE_WEEKS)
    counts = [0] * BASELINE_WEEKS
    first_seen_week = None
    for it in items:
        if it.get("lane") != m["lane"]:
            continue
        d = _d(it["date"])
        logged = _d(entered.get(it.get("id"), it["date"]))
        if start <= d < this_monday and logged <= made:
            wk = (d - start).days // 7
            counts[wk] += 1
            first_seen_week = wk if first_seen_week is None else min(first_seen_week, wk)
    if first_seen_week is None:
        return None
    weeks = counts[first_seen_week:]           # ignore weeks before the board existed
    if len(weeks) < BASELINE_MIN_WEEKS:
        return None
    lam = sum(weeks) / len(weeks) * (((_d(m["to"]) - _d(m["from"])).days + 1) / 7)
    return round(min(P_MAX, max(P_MIN, _poisson_at_least(m["atLeast"], lam))), 3)


def board_count(f: dict, items: list) -> int:
    m = f["metric"]
    return sum(1 for i in items
               if i.get("lane") == m["lane"] and m["from"] <= i.get("date", "") <= m["to"])


def sync_lock(root: Path, fc: dict, lock: dict, items: list, entered: dict) -> dict:
    """Log anything new, freeze any board count that is due, write the lock back."""
    if fc is None:
        return lock
    today = _today()
    changed = []
    for f in fc.get("forecasts", []):
        if f["id"] not in lock["forecasts"]:
            entry = {"hash": _fingerprint(f), "firstSeen": today}
            if f.get("kind") == "board":
                entry["baseline"] = baseline(f, items, entered)
            lock["forecasts"][f["id"]] = entry
            changed.append(f"logged {f['id']}")
    for r in fc.get("resolutions", []):
        if r["id"] not in lock["resolutions"]:
            lock["resolutions"][r["id"]] = {"hash": _fingerprint(r), "firstSeen": today}
            changed.append(f"logged resolution of {r['id']}")
    manual = {r["id"] for r in fc.get("resolutions", [])}
    for f in fc.get("forecasts", []):
        if f.get("kind") != "board" or f["id"] in lock["auto"] or f["id"] in manual:
            continue
        due = _d(f["metric"]["to"]) + timedelta(days=GRACE_DAYS)
        if _d(today) >= due:
            n = board_count(f, items)
            lock["auto"][f["id"]] = {
                "count": n, "outcome": "yes" if n >= f["metric"]["atLeast"] else "no",
                "frozen": today}
            changed.append(f"resolved {f['id']} ({n} items)")
    # Only the GitHub Action writes the lock to disk, and it commits what it
    # writes. A local build — a daily run on a laptop, a preview — works from
    # the same entries in memory but leaves the file alone, so the committed
    # lock only ever records what the published site saw, on the day it saw it.
    if changed and _in_ci():
        (root / LOCK_FILE).write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n",
                                      encoding="utf-8")
        for c in changed:
            print(f"  {LOCK_FILE}: {c}")
    elif changed:
        print(f"  {LOCK_FILE}: {len(changed)} change(s) held in memory — only the "
              f"GitHub Action writes this file")
    return lock


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def records(fc: dict, lock: dict):
    """Every forecast with its status, outcome and score, in file order."""
    manual = {r["id"]: r for r in fc.get("resolutions", [])}
    superseded_by = {f["supersedes"]: f["id"] for f in fc.get("forecasts", [])
                     if f.get("supersedes")}
    out = []
    for f in fc.get("forecasts", []):
        rec = {"f": f, "outcome": None, "brier": None, "base_brier": None,
               "resolution": manual.get(f["id"]), "auto": lock["auto"].get(f["id"]),
               "baseline": (lock["forecasts"].get(f["id"]) or {}).get("baseline"),
               "logged": (lock["forecasts"].get(f["id"]) or {}).get("firstSeen", f["made"]),
               "superseded_by": superseded_by.get(f["id"])}
        if rec["resolution"]:
            rec["outcome"] = rec["resolution"]["outcome"]
        elif rec["auto"]:
            rec["outcome"] = rec["auto"]["outcome"]
        if rec["outcome"] in ("yes", "no"):
            o = 1.0 if rec["outcome"] == "yes" else 0.0
            rec["brier"] = (f["p"] - o) ** 2
            if rec["baseline"] is not None:
                rec["base_brier"] = (rec["baseline"] - o) ** 2
        out.append(rec)
    return out


def summary(recs):
    scored = [r for r in recs if r["brier"] is not None]
    paired = [r for r in scored if r["base_brier"] is not None]
    mean = lambda xs: sum(xs) / len(xs) if xs else None
    bins = []
    for lo in range(0, 100, 10):
        hi = lo + 10
        inbin = [r for r in scored if lo / 100 <= r["f"]["p"] < hi / 100 or (hi == 100 and r["f"]["p"] == 1)]
        if inbin:
            bins.append({"label": f"{lo}–{hi}%", "n": len(inbin),
                         "said": mean([r["f"]["p"] for r in inbin]),
                         "happened": mean([1.0 if r["outcome"] == "yes" else 0.0 for r in inbin])})
    return {
        "open": sum(1 for r in recs if r["outcome"] is None),
        "resolved": len(scored),
        "void": sum(1 for r in recs if r["outcome"] == "void"),
        "brier": mean([r["brier"] for r in scored]),
        "paired": len(paired),
        "brier_paired": mean([r["brier"] for r in paired]),
        "brier_base": mean([r["base_brier"] for r in paired]),
        "bins": bins,
    }


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def _pct(p) -> str:
    return f"{round(p * 100)}%"


def _b(x) -> str:
    return "—" if x is None else f"{x:.3f}"


def body(site, fc: dict, lock: dict, lanes: dict, fmt_date) -> str:
    recs = records(fc, lock)
    s = summary(recs)
    who = escape(fc.get("forecaster", ""))

    def lanepill(key):
        v = lanes.get(key)
        return f'<span class="lanepill {v["pill"]}">{v["name"]}</span>' if v else ""

    def card(r):
        f = r["f"]
        meta = [f'Made <time datetime="{f["made"]}">{fmt_date(f["made"])}</time>']
        if f.get("kind") == "board":
            m = f["metric"]
            meta.append(f'Counts {escape(lanes[m["lane"]]["name"])} items dated '
                        f'{fmt_date(m["from"])} – {fmt_date(m["to"])}; resolves itself '
                        f'{GRACE_DAYS} days after')
            if r["baseline"] is not None:
                meta.append(f'Trend baseline {_pct(r["baseline"])}')
        else:
            meta.append(f'Resolves by <time datetime="{f["resolveBy"]}">'
                        f'{fmt_date(f["resolveBy"])}</time>')
        if f.get("supersedes"):
            meta.append(f'Updates <a href="#{escape(f["supersedes"])}">an earlier call</a>')
        if r["superseded_by"]:
            meta.append(f'Updated by <a href="#{escape(r["superseded_by"])}">a later call</a>')

        verdict = ""
        if r["outcome"] in ("yes", "no"):
            detail = ""
            if r["resolution"]:
                src = r["resolution"]["source"]
                detail = (f' · <a href="{escape(src["url"], quote=True)}" target="_blank" '
                          f'rel="noopener">{escape(src["outlet"])} ↗</a>')
            elif r["auto"]:
                detail = f' · {r["auto"]["count"]} items on the board'
            verdict = (f'<div class="fc-verdict fc-{r["outcome"]}">Resolved '
                       f'{r["outcome"].upper()}{detail} · Brier {_b(r["brier"])}</div>')
        elif r["outcome"] == "void":
            verdict = (f'<div class="fc-verdict fc-void">Void — '
                       f'{escape(r["resolution"].get("note", ""))}</div>')

        why = (f'<p class="fc-why"><b>Reasoning.</b> {escape(f["rationale"])}</p>'
               if f.get("rationale") else "")
        return (f'<article class="item fc" id="{escape(f["id"])}">'
                f'<div class="fc-p" aria-label="Probability {_pct(f["p"])}">{_pct(f["p"])}</div>'
                f'<div class="fc-main"><h4>{lanepill(f.get("lane") or (f.get("metric") or {}).get("lane"))} '
                f'{escape(f["question"])}</h4>'
                f'<p><b>Resolves YES if</b> {escape(f["criteria"])}</p>{why}'
                f'<div class="meta src">{" · ".join(meta)}</div>{verdict}</div></article>')

    open_recs = sorted((r for r in recs if r["outcome"] is None),
                       key=lambda r: r["f"].get("resolveBy") or r["f"]["metric"]["to"])
    done = sorted((r for r in recs if r["outcome"] is not None),
                  key=lambda r: (r["resolution"] or {}).get("date")
                  or (r["auto"] or {}).get("frozen", ""), reverse=True)

    stats = [
        (str(s["open"]), "Open"),
        (str(s["resolved"]), "Resolved"),
        (_b(s["brier"]), "Brier score"),
    ]
    if s["paired"]:
        stats.append((f'{_b(s["brier_paired"])} / {_b(s["brier_base"])}',
                      f'Analyst vs trend · {s["paired"]} board call{"" if s["paired"] == 1 else "s"}'))
    tiles = "".join(f'<div class="stat"><div class="n">{n}</div><div class="l">{escape(l)}</div></div>'
                    for n, l in stats)

    if s["bins"]:
        rows = "".join(f'<tr><td>{b["label"]}</td><td>{b["n"]}</td><td>{_pct(b["said"])}</td>'
                       f'<td>{_pct(b["happened"])}</td></tr>' for b in s["bins"])
        calib = ('<table class="fc-cal"><thead><tr><th scope="col">Range</th>'
                 '<th scope="col">Calls</th><th scope="col">Forecast</th>'
                 '<th scope="col">Happened</th></tr></thead>'
                 f'<tbody>{rows}</tbody></table>')
    else:
        calib = '<p class="lede">Nothing has resolved yet. The table fills in as forecasts close.</p>'

    open_html = ("".join(card(r) for r in open_recs)
                 or '<p class="lede">No open forecasts.</p>')
    done_html = ("".join(card(r) for r in done)
                 or '<p class="lede">Nothing has resolved yet.</p>')
    intro = escape(fc.get("intro", ""))

    return f"""{site.nav(FORECASTS_URL)}

  <header class="pagehead">
    <h1>Forecasts</h1>
    <div class="sub">Probabilistic calls{f" by {who}" if who else ""}, logged before the
      fact and scored against what happened.{f" {intro}" if intro else ""}</div>
  </header>

  <div class="note" style="margin:-4px 0 22px">The board reports; it does not forecast.
    This page is kept apart from it so a forecast never reads as a sourced item.</div>

  <div class="stats">{tiles}</div>

  <section class="block"><h2 class="blockhead">Open — {len(open_recs)}</h2>
    <div class="lane fc-list">{open_html}</div>
  </section>

  <section class="block"><h2 class="blockhead">Resolved — {len(done)}</h2>
    <div class="lane fc-list">{done_html}</div>
  </section>

  <section class="block"><h2 class="blockhead">Calibration</h2>
    <p class="lede">A well-calibrated forecaster's 70% calls come true about 70% of the time.
      Each row groups the resolved calls by the probability given, and compares the average forecast with how often the event happened.</p>
    {calib}
  </section>

  <section class="block"><h2 class="blockhead">Method</h2>
    <div class="prose">
      <p>Every forecast carries a probability, a date, and resolution criteria written
        before the outcome was known. Scores use the Brier score — the squared distance
        between the probability and what happened, averaged. 0 is perfect; always
        answering 50% earns 0.25; lower is better.</p>
      <p>Forecasts are append-only. The build fingerprints each forecast and each
        resolution the first time it sees one and refuses to publish if any has changed
        since; a changed view is a new forecast that updates the old one, and both are
        scored. The repository's commit history independently records when each was added.</p>
      <p>Judgment calls resolve by hand against a source, under the same sourcing rules
        as the board. Board calls are about the board's own counts and resolve themselves
        {GRACE_DAYS} days after their window closes, so late-arriving items are counted
        before the answer is frozen. Each is also scored against a trend baseline — what
        the lane's recent weekly rate alone would have predicted on the day the forecast
        was made — which is the test of whether judgment adds anything to the trend.
        Counts measure what this board tracked, not everything that happened.</p>
    </div>
  </section>

  {site.footer()}"""
