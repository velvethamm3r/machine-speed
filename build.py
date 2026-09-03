#!/usr/bin/env python3
"""
Machine Speed — static site generator.

Reads data.json (single source of truth, rewritten by the daily run) and
writes a fully pre-rendered site into dist/:

    dist/
      index.html            landing page — Explore, unless LANDING is "board"
                            (the pre-rendered board is published only if BOARD_PAGE
                            is set; its markup is always used for today's snapshot)
      capability/           lane pages, one directory each
      policy/
      defense/
      attacks/
      markets/
      briefs/               brief index (only when data.json has briefs)
      brief/<slug>/         one brief: an incident laid out in acts and stages
      archive/              archive index
      archive/…​.html        dated snapshot of today's board
      about/
      capability.html …     redirect stubs at the old flat paths
      feed.xml              RSS 2.0
      style.css             shared stylesheet (cached across pages)
      theme.js              theme toggle only (site works fine without it)
      icon.svg              favicon

Usage:
    python3 build.py            # build into ./dist
    python3 build.py --out X    # build into X

No dependencies beyond the Python 3 standard library, so it runs unmodified
on Cloudflare Pages' build image, GitHub Actions, or your laptop.
"""

import argparse
import hashlib
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
SITE_DESCRIPTION = ("A daily, source-verified intelligence board on AI cyber "
                    "capability and the defense & policy lag around it.")
NEW_WINDOW_DAYS = 2   # items this recent auto-enter the "New to the board" strip; isNew overrides
STRIP_MAX = 6         # spec caps the "New to the board" strip at six

# A brief's acts can sit side by side when they share a "row" — two positions
# answering the same question, two arms of a response. Two fit on a laptop and
# still hold a readable line length; a third turns each panel into a column of
# two-word lines, so validate() refuses it rather than letting the page decide.
ACT_ROW_MAX = 2

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
# The dated snapshot is a copy of the board, so it follows this setting too; the
# newsletter draft always carries the note regardless, and data.json always keeps
# it, so the record survives whichever placement is chosen.
NOTE_PLACEMENT = "none"

# data.json's "internalNote" is the one-sentence record of what changed since the
# previous run. It is a working note, not reader-facing, so by default it stays
# off every generated page — board, weeks, lanes and the archive snapshot alike.
# validate() still requires it, so the run-to-run record lives on in data.json and
# in git history. Set to True to print it in the footer as it used to be.
SHOW_INTERNAL_NOTE = False

# Optional tagline printed in the footer between the site name and the copyright,
# e.g. "Independent · Not affiliated with any vendor". Empty leaves the footer as
# just the site name and the year. This is display text only — it describes the
# project, it does not govern how a run behaves.
FOOTER_NOTE = ""

# Symbol printed immediately after the site name in the footer. "™" asserts an
# unregistered common-law claim to the name and needs no filing; "®" is only
# lawful once the mark is actually registered, so it stays a deliberate edit
# rather than something a build could turn on by accident. Empty prints neither.
SITE_MARK = "™"

# The Archive page has always offered two ways in: by week (living pages that
# keep their links) and by run (the frozen snapshot taken each time the board
# published). Set this False to show only the weeks. The snapshots are still
# written to archive/ and still committed — validate() will not let an entry in
# archives[] point at a missing file either way — they simply stop being linked
# from the site, so the record survives even when the index for it does not.
SHOW_RUN_SNAPSHOTS = False

# The Explore board — the filterable, story-clustered view of the same items.
# It is one extra page, built from the same data.json, and it is the only page
# that needs JavaScript: every pre-rendered page keeps working untouched, and a
# visitor with JS off gets a plain list of week links instead. Set EXPLORE_PAGE
# to "" and the page, its nav link, its assets and its sitemap entry all
# disappear — the site builds exactly as it did before it existed.
# Display face for headlines. Loaded on every page (so the archive snapshots
# match the live board) and applied by the --display token in style.css. Empty
# both strings and the whole site falls back to the UI sans with no request.
DISPLAY_FONT_URL = ("https://fonts.googleapis.com/css2?"
                    "family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&display=swap")

# Which view answers the bare domain. "explore" makes the interactive board the
# landing page and moves the pre-rendered one to BOARD_PAGE; "board" restores the
# original arrangement. The pre-rendered board never goes away either way — it is
# the no-JavaScript fallback, the thing crawlers read, and what each dated archive
# snapshot is a copy of.
# Clean URLs. Every page except the landing page is written as index.html inside
# its own directory, so /capability/ works on GitHub Pages, which serves files
# literally and does not strip extensions. The old flat paths stay behind as
# redirect stubs — permanently, not as a migration step: the dated snapshots in
# archive/ are frozen HTML that still links to ../capability.html, and those files
# are never rewritten.
ARCHIVE_URL = "archive/"
BRIEFS_URL = "briefs/"
ABOUT_URL = "about/"
LEGACY_PATHS = {
    "capability.html": "capability/", "policy.html": "policy/",
    "defense.html": "defense/", "attacks.html": "attacks/",
    "markets.html": "markets/", "briefs.html": BRIEFS_URL,
    "archive.html": ARCHIVE_URL, "about.html": ABOUT_URL,
}

LANDING = "explore"

EXPLORE_PAGE = "explore.html"      # where Explore lives when it is NOT the landing page
EXPLORE_NAV = "Explore"
# Where the pre-rendered board is published when Explore is the landing page.
# Empty means it is not published at all — and that is the default, because it is
# redundant: every item it lists is already pre-rendered on the lane pages and the
# week pages, which is what crawlers and no-JavaScript readers actually reach.
# The renderer itself stays either way: each dated snapshot in archive/ IS a copy
# of that markup, frozen, and that record is the one thing the build guarantees.
BOARD_PAGE = ""
BOARD_NAV = "Full board"


# The stylesheet and the theme script keep the same filenames from one build to
# the next, so a browser that has already seen them has every reason to go on
# serving the copy it has — which is how an edit to style.css can be live on the
# server and invisible in the window. Appending a fingerprint of the file's own
# contents to the URL makes a changed file a different URL, so the cache is
# bypassed exactly when it should be and honoured the rest of the time. Nothing
# is renamed on disk: the query string is not part of the filename, so
# style.css stays style.css for anyone reading the repo.
_asset_versions: dict = {}


def asset_version(name: str) -> str:
    """`?v=` fingerprint for an asset, or "" if it cannot be read.

    Falling back to no fingerprint rather than raising is deliberate. A missing
    stylesheet is already caught by the deploy — failing the whole build over a
    cache hint would trade a small problem for a much larger one.
    """
    if name not in _asset_versions:
        p = Path(__file__).parent / "assets" / name
        try:
            digest = hashlib.sha256(p.read_bytes()).hexdigest()[:8]
        except OSError:
            digest = ""
        _asset_versions[name] = f"?v={digest}" if digest else ""
    return _asset_versions[name]


# Custom domain. Written to dist/CNAME on every build so a GitHub Pages deploy
# can never silently drop the domain setting.
CNAME = SITE_URL.split("//", 1)[1]

# Substack. Set SUBSTACK_URL to the publication home (no trailing slash) to turn
# on the subscribe links; leave it empty and every Substack element disappears.
# Point it at a subdomain of this site (newsletter.techpointe.org) rather than
# *.substack.com and the nav link stops behaving like an outbound one — see
# same_site() below.
SUBSTACK_URL = "https://velvethamm3r.substack.com"
SUBSTACK_CTA = "Get the board in your inbox"
SUBSTACK_NAV = "Subscribe"              # the nav label. "Newsletter" reads as part of the site.


def home_of(kind: str) -> str:
    """The path a view is written to, given the landing-page choice.

    Everything else in the build asks these two functions rather than hardcoding
    a filename, so flipping LANDING moves both pages and every link to them.
    """
    if kind == "explore":
        return "index.html" if LANDING == "explore" and EXPLORE_PAGE else EXPLORE_PAGE
    if LANDING == "explore" and EXPLORE_PAGE:
        return BOARD_PAGE          # "" when the pre-rendered board is not published
    return "index.html"


def same_site(url: str) -> bool:
    """True when url sits under the same registrable domain as SITE_URL.

    A link to newsletter.techpointe.org from machinespeed.techpointe.org is a
    move within one property, not a departure from it, so it should not get
    the new-tab-and-arrow treatment reserved for leaving the site. Compares the
    last two host labels, which is right for .org/.com and wrong for the
    multi-part suffixes (.co.uk); this site is on a .org and the failure mode
    is a link opening in a new tab, so the simple rule earns its keep.
    """
    def reg(u: str) -> str:
        host = u.split("//", 1)[-1].split("/", 1)[0].split(":", 1)[0].lower()
        return ".".join(host.split(".")[-2:])
    return bool(url) and reg(url) == reg(SITE_URL)

LANES = {
    "cap": {"name": "Capability", "var": "--cap", "pill": "lp-cap", "page": "capability/",
            "desc": "What AI systems can now do in the cyber domain, closed and open-weight."},
    "pol": {"name": "Policy", "var": "--pol", "pill": "lp-pol", "page": "policy/",
            "desc": "Government, standards and governance responses."},
    "def": {"name": "Defense", "var": "--def", "pill": "lp-def", "page": "defense/",
            "desc": "Defensive tooling, patching and mitigation."},
    "atk": {"name": "Attacks", "var": "--atk", "pill": "lp-atk", "page": "attacks/",
            "desc": "Real-world incidents and offensive use."},
    "mkt": {"name": "Markets", "var": "--mkt", "pill": "lp-mkt", "page": "markets/",
            "desc": "How the money prices the risk — cyber insurance, underwriting, "
                    "liability and the capital response."},
}

# Lanes are a closed taxonomy, but the page furniture that counts them is not:
# headings, empty-state copy and the newsletter all said "four lanes" when there
# were four. Deriving the word means a sixth lane never leaves a stale number in
# prose that no test would catch.
NUMWORDS = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight"]


def numword(n: int) -> str:
    return NUMWORDS[n] if n < len(NUMWORDS) else str(n)

# The last two tiers were called "official" and "vendor" until 2026-08-06. Both
# names described *who was speaking* rather than *what kind of claim they were
# making*, which is the distinction the tiers actually draw — and both carried a
# verdict the board has no business issuing. "Official" lent a lab's own
# announcement the air of a public record; "vendor" read as a slur on anyone
# with something to sell, which caught university labs and agencies touting
# their own tooling in the same net. The replacements name the epistemics
# instead: whether the speaker has formally put the statement in its own name,
# and whether the party making a measurement is the party being measured.
CONF = {
    "confirmed": "Confirmed by org", "claimed": "Claimed by attacker",
    "researchers": "Reported by researchers", "press": "Reported by press",
    "on-record": "On the record", "self-reported": "Self-reported, untested",
}
CONF_VAR = {"confirmed": "--cap", "claimed": "--atk", "researchers": "--def",
            "press": "--ink-3", "on-record": "--pol", "self-reported": "--atk"}

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
    """A date range, with every part that both ends share printed only once.

    2026-07-01, 2026-08-05 -> 'Jul 1 – Aug 5, 2026'   (shared year)
    2026-08-03, 2026-08-09 -> 'Aug 3 – 9, 2026'       (shared year and month)
    2025-12-29, 2026-01-04 -> 'Dec 29, 2025 – Jan 4, 2026'

    Repeating the month inside one month is the thing that made a column of
    week labels look inconsistent — 'Aug 3 – Aug 5' next to 'Jul 27 – Aug 2'
    reads as two different formats rather than one range that happens not to
    cross a boundary.
    """
    if not start or not end:
        return ""
    sy, sm, sd = start.split("-")
    ey, em, ed = end.split("-")
    same_year = sy == ey
    same_month = same_year and sm == em
    if same_month:
        left = f"{MONTHS[int(sm) - 1]} {int(sd)}"
    else:
        left = f"{MONTHS[int(sm) - 1]} {int(sd)}" + ("" if same_year else f", {sy}")
    right = (f"{int(ed)}" if same_month
             else f"{MONTHS[int(em) - 1]} {int(ed)}")
    return f"{left} – {right}, {ey}"


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

    # The key was called "dossiers" until 2026-08-06. Renaming it silently would
    # make every brief page vanish from a build that otherwise reports success,
    # which is the one failure mode this generator is built to make impossible.
    if "dossiers" in d:
        errors.append("data.json still has a 'dossiers' key — it was renamed to "
                      "'briefs' on 2026-08-06. Rename the key (and, inside each "
                      "entry, nothing else changes) and rebuild.")

    # briefs[] is optional — a data.json without one builds exactly as before.
    # When present it is held to the same rule as items[]: every claim carries a
    # source you opened, and nothing is dated into the future.
    item_ids = {i.get("id") for i in d["items"]}
    slugs = set()
    for n, dos in enumerate(d.get("briefs", [])):
        where = f"brief[{n}] {dos.get('slug', '<no slug>')}"
        for f in ("slug", "title", "summary", "stages"):
            if not dos.get(f):
                errors.append(f"{where}: missing field '{f}'")
        slug = dos.get("slug", "")
        if slug in slugs:
            errors.append(f"{where}: duplicate slug")
        slugs.add(slug)
        if slug and not all(c.isalnum() or c == "-" for c in slug):
            errors.append(f"{where}: slug must be kebab-case (letters, digits, hyphens)")
        if dos.get("lane") and dos["lane"] not in LANES:
            errors.append(f"{where}: lane must be one of {', '.join(LANES)}")

        # acts[] is the optional panel layout. It carries no facts of its own:
        # every bullet in a panel is a stage or an existing board item, so the
        # act layer can be added, reordered or deleted without touching a
        # single sourced claim. The checks below exist because the two ways it
        # can go wrong are both silent — a stage pointing at an act that does
        # not exist, or an act layout that quietly drops stages it forgot.
        acts = dos.get("acts", [])
        act_ids = set()
        rows = {}
        for m, a in enumerate(acts):
            aw = f"{where} act[{m}] {a.get('id', '<no id>')}"
            for f in ("id", "headline"):
                if not a.get(f):
                    errors.append(f"{aw}: missing field '{f}'")
            aid = a.get("id", "")
            if aid in act_ids:
                errors.append(f"{aw}: duplicate act id")
            act_ids.add(aid)
            if aid and not all(c.isalnum() or c == "-" for c in aid):
                errors.append(f"{aw}: id must be kebab-case (letters, digits, hyphens)")
            if a.get("lane") and a["lane"] not in LANES:
                errors.append(f"{aw}: lane must be one of {', '.join(LANES)}")
            if "row" in a:
                if not isinstance(a["row"], int):
                    errors.append(f"{aw}: row must be a whole number")
                else:
                    rows.setdefault(a["row"], []).append(aid)
            for iid in a.get("items", []):
                if iid not in item_ids:
                    errors.append(f"{aw}: folds in item '{iid}', which is not in items[]")
        for r, members in rows.items():
            if len(members) > ACT_ROW_MAX:
                errors.append(f"{where}: row {r} has {len(members)} acts "
                              f"({', '.join(members)}); at most {ACT_ROW_MAX} fit "
                              f"side by side before the panels stop being readable")

        for m, s in enumerate(dos.get("stages", [])):
            sw = f"{where} stage[{m}]"
            if acts:
                if not s.get("act"):
                    errors.append(f"{sw}: this brief has acts[], so every stage needs "
                                  f"an 'act' — a stage without one would not appear "
                                  f"on the page at all")
                elif s["act"] not in act_ids:
                    errors.append(f"{sw}: act '{s['act']}' is not one of "
                                  f"{', '.join(sorted(i for i in act_ids if i))}")
            for f in ("date", "label", "what"):
                if not s.get(f):
                    errors.append(f"{sw}: missing field '{f}'")
            if not s.get("sources"):
                errors.append(f"{sw}: no sources — every stage needs at least one "
                              f"link you opened")
            for src in s.get("sources", []):
                if not str(src.get("url", "")).startswith("https://"):
                    errors.append(f"{sw}: source url must be an https:// link")
                if not src.get("outlet"):
                    errors.append(f"{sw}: source missing 'outlet'")
            if s.get("confidence") and s["confidence"] not in CONF:
                errors.append(f"{sw}: confidence must be one of {', '.join(CONF)}")
            try:
                if days_ago(s["date"], d["updatedISO"]) < 0:
                    errors.append(f"{sw}: dated in the future ({s['date']})")
            except (KeyError, ValueError):
                errors.append(f"{sw}: date must be YYYY-MM-DD")

        # An act carrying neither a stage nor a folded-in item renders as a
        # headline over white space. That is a headline making a claim nothing
        # underneath it supports, so it is worth saying out loud.
        used = {s.get("act") for s in dos.get("stages", [])}
        for a in acts:
            if a.get("id") not in used and not a.get("items"):
                warnings.append(f"{where}: act '{a.get('id')}' has no stages and folds "
                                f"in no items — its headline would stand on nothing")

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
        warnings.append("nothing qualifies for the 'New to the board' strip — the board will say so "
                        "plainly, which is the correct outcome on a quiet day")
    elif len(strip) > STRIP_MAX:
        warnings.append(f"{len(strip)} items qualify for the 'New to the board' strip; "
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
        # Briefs are optional. With none in data.json the Briefs link, the
        # index page and the board's brief rail all disappear, so a data file
        # written before this feature existed still builds unchanged.
        self.briefs = sorted(data.get("briefs", []),
                             key=lambda x: x.get("updated", ""), reverse=True)
        # Acts fold in board items by id; this is the lookup that resolves them.
        self.by_id = {i["id"]: i for i in data.get("items", []) if i.get("id")}

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
    @property
    def home(self) -> str:
        """The board's href, as a directory rather than a filename.

        The server serves the same bytes for `/` and `/index.html`, but they
        are two URLs: they get shared, linked and indexed separately, and the
        filename version is the ugly one. `<canonical>`, the sitemap and the
        feed have always pointed at `/`; this is what makes the site's own
        links agree with them, so clicking Board from anywhere lands on the
        bare domain and the address bar never grows an `index.html`.

        `./` rather than `/` on purpose — a root-absolute link would break the
        moment the site is served from a subpath, which is exactly what the
        `username.github.io/<repo>/` fallback URL is.
        """
        return self.prefix or "./"

    def nav(self, active: str, lanes: bool = True) -> str:
        """Two rows: the places, then the lanes.

        The single row worked at four lanes and would not at five — Board,
        five lanes, Briefs, Archive, About, RSS and the theme button is
        eleven controls, which wraps into an unreadable block on a laptop and
        a wall on a phone. So the site nav keeps the destinations and the lane
        bar below it carries the taxonomy, each lane in its own colour.
        """
        if LANDING == "explore" and EXPLORE_PAGE:
            links = [("index.html", "Board")]
            if BOARD_PAGE:
                links.append((BOARD_PAGE, BOARD_NAV))
        else:
            links = [("index.html", "Board")]
            if EXPLORE_PAGE:
                links.append((EXPLORE_PAGE, EXPLORE_NAV))
        if self.briefs:
            links.append((BRIEFS_URL, "Briefs"))
        links += [(ARCHIVE_URL, "Archive"), (ABOUT_URL, "About")]
        out = ['<nav class="nav" aria-label="Site">',
               f'<a class="logo" href="{self.home}"><b>Machine&nbsp;Speed</b>'
               f'<span>{escape(SITE_TAGLINE)}</span></a>']
        for href, label in links:
            cls = "link active" if href == active else "link"
            aria = ' aria-current="page"' if href == active else ""
            # "index.html" stays the key that marks the tab active — it is the
            # page's identity everywhere else in the build — but it is not what
            # gets written into the link.
            url = self.home if href == "index.html" else self.prefix + href
            out.append(f'<a class="{cls}" href="{url}"{aria}>{label}</a>')
        out.append('<span class="spacer"></span>')
        if SUBSTACK_URL:
            tab = "" if same_site(SUBSTACK_URL) else ' target="_blank" rel="noopener"'
            out.append(f'<a class="link sub-link" href="{escape(SUBSTACK_URL, quote=True)}"'
                       f'{tab}>{escape(SUBSTACK_NAV)}</a>')
        out.append(f'<a class="link" href="{self.prefix}feed.xml">RSS</a>')
        out.append('<button class="themebtn" type="button" data-theme-toggle hidden>'
                   '<span class="ico">☀</span> <span class="lbl">Light</span></button>')
        out.append('</nav>')
        if lanes:
            out.append(self.lanebar(active))
        return "\n    ".join(out)

    def lanebar(self, active: str) -> str:
        """The lane taxonomy as its own row, under the site nav."""
        out = ['<nav class="lanebar" aria-label="Lanes">', '<span class="lbl">Lanes</span>']
        for k, v in LANES.items():
            on = v["page"] == active
            cls = "active" if on else ""
            aria = ' aria-current="page"' if on else ""
            style = f'--ln:var({v["var"]});--ln-soft:var({v["var"]}-soft)'
            n = len(self.lane_items(k))
            out.append(f'<a class="{cls}" style="{style}" href="{self.prefix}{v["page"]}"{aria}>'
                       f'<i></i>{v["name"]} <span style="color:var(--ink-3)">{n}</span></a>')
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
            f'rel="noopener">{escape(it["outlet"])} ↗</a> · '
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

    def subscribe_block(self, compact: bool = False) -> str:
        """Substack call-to-action. Renders nothing at all if SUBSTACK_URL is unset.

        A plain link rather than Substack's iframe embed: it keeps the site
        dependency-free and loads no third-party tracking, and it works
        identically on the archived snapshots.
        """
        if not SUBSTACK_URL:
            return ""
        own = same_site(SUBSTACK_URL)
        tab = "" if own else ' target="_blank" rel="noopener"'
        label = "Subscribe" if own else "Subscribe on Substack ↗"
        if compact:
            # The board is a page of dense cards; the stacked heading-paragraph-button
            # block reads as three loose elements at the end of it. Same content, one row.
            return (f'<section class="block subscribe compact">'
                    f'<h2 class="blockhead">{escape(SUBSTACK_CTA)}</h2>'
                    f'<p>The same reporting, written up and sent to your inbox.</p>'
                    f'<a class="subbtn" href="{escape(SUBSTACK_URL, quote=True)}"{tab}>{label}</a>'
                    f'</section>')
        return (f'<section class="block subscribe">'
                f'<h2 class="blockhead">{escape(SUBSTACK_CTA)}</h2>'
                f'<p>The board updates daily on the web. The newsletter is the same '
                f'reporting, written up and sent to your inbox — same sourcing rules, '
                f'same corrections policy.</p>'
                f'<p><a class="subbtn" href="{escape(SUBSTACK_URL, quote=True)}"'
                f'{tab}>{label}</a></p>'
                f'</section>')

    def footer(self) -> str:
        legend = "".join(
            f'<span><i style="background:var({v["var"]})"></i>{v["name"]}</span>'
            for v in LANES.values())
        year = (self.as_of or "2026")[:4]
        internal = escape(self.d.get("internalNote", ""))
        note = (f'<p style="margin-top:12px">{internal}</p>'
                if SHOW_INTERNAL_NOTE and internal else "")
        tag = f" · {escape(FOOTER_NOTE)}" if FOOTER_NOTE else ""
        mark = f'<span class="tm">{escape(SITE_MARK)}</span>' if SITE_MARK else ""
        return (f'<footer><div class="legend">{legend}</div>{note}'
                f'<p style="margin-top:8px">{SITE_NAME}{mark}{tag} · © {year}</p></footer>')

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
{'''<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="''' + DISPLAY_FONT_URL + '''">''' if DISPLAY_FONT_URL else ''}
<link rel="stylesheet" href="{asset_prefix}style.css{asset_version('style.css')}">
<link rel="icon" href="{asset_prefix}icon.svg{asset_version('icon.svg')}" type="image/svg+xml">
{extra_head}</head>
<body>
<div class="wrap">

  {body}

</div>
<script src="{asset_prefix}theme.js{asset_version('theme.js')}" defer></script>
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
                           f'since the last run.</strong> A fresh sweep across all {numword(len(LANES))} '
                           "lanes surfaced no verified, in-window items that weren't already shown. "
                           'No items were invented to fill this space.</p>')

        stats = "".join(
            f'<div class="stat"><div class="n">{len(self.lane_items(k))}</div>'
            f'<div class="l">{v["name"]}</div>'
            f'<div class="bar" style="background:var({v["var"]})"></div></div>'
            for k, v in LANES.items())

        lanes_html = []
        for k, v in LANES.items():
            items = self.front_items(k)
            total = len(self.lane_items(k))
            # A lane with nothing in it prints no box. A new lane is empty on the
            # day it is added, and an empty labelled box reads as a gap in the
            # reporting rather than as a lane waiting for its first verified item.
            if not total:
                continue
            count = f"{len(items)} of {total} items" if self.front_cutoff else f"{total} items"
            lanes_html.append(
                f'<section class="lane"><h3><span class="barv" style="background:var({v["var"]})"></span>'
                f'{v["name"]}<span class="count">{count}</span>'
                f'<a class="more" href="{self.prefix}{v["page"]}">view lane ↗</a></h3>'
                + self.lane_sections(k, items) + "</section>")

        if self.front_cutoff:
            shown = fmt_span(self.front_cutoff, self.cov_end)
            lede = ('AI cyber capability against the defense &amp; policy lag. '
                    if home_of("board") == "index.html" else
                    'Every item on the board, pre-rendered — no JavaScript, no filters. ')
            sub = (f'{lede}'
                   f'The last two weeks in full — <strong>{escape(shown)}</strong> — then every '
                   f'earlier item from {escape(self.coverage)} indexed by week below.')
        else:
            sub = ('AI cyber capability against the defense &amp; policy lag — '
                   f'every verified item from <strong>{escape(self.coverage)}</strong>, '
                   'grouped by lane and by week.')

        return f"""{self.nav(home_of("board"))}

  <header class="pagehead">
    <h1>{"The capability-vs-defense gap, tracked daily" if home_of("board") == "index.html" else "The full board"}</h1>
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
    <h2>⚡ New to the board</h2>
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

  {self.brief_rail()}

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
        """One Monday-to-Sunday week, every lane it touched, at its own URL."""
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
        pager.append(f'<a class="idx" href="{self.prefix}{ARCHIVE_URL}">All weeks</a>')
        pager.append(f'<a class="next" href="{self.prefix}week/{newer["monday"]}/">'
                     f'{escape(newer["label"])} →</a>' if newer else '<span class="next"></span>')
        pager.append('</nav>')
        pager_html = "".join(pager)

        return f"""{self.nav(ARCHIVE_URL)}

  <header class="pagehead">
    <h1>{escape(w["label"])}</h1>
    <div class="sub">{len(w["items"])} verified items across {numword(len(lanes_html))}
      {"lane" if len(lanes_html) == 1 else "lanes"}, from the week of
      {escape(fmt_date(w["monday"]))}. Part of the {escape(self.coverage)} board.</div>
    <div class="stamprow">
      <div class="stamp"><a href="{self.home}">← Back to the live board</a></div>
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
        if SHOW_RUN_SNAPSHOTS:
            snaps = "".join(
                f'<a href="{escape(a["file"], quote=True)}">'
                f'<span class="d">{fmt_date(a["date"])}</span>'
                f'<span class="m">{a.get("items", "")} items — '
                f'{escape(a.get("note", ""))}</span></a>'
                for a in sorted(self.d.get("archives", []),
                                key=lambda a: a["date"], reverse=True))
            runs = f"""

  <section class="block"><h2 class="blockhead">By run — dated snapshots</h2>
    <p class="lede">Each is a self-contained copy of the whole board as it stood that day.
      Snapshots are never edited after the fact.</p>
    <div class="arch">{snaps}</div>
  </section>"""
        else:
            runs = ""
        return f"""{self.nav(ARCHIVE_URL)}

  <header class="pagehead">
    <h1>Archive</h1>
    <div class="sub">The board, split into weekly pages.</div>
  </header>

  <section class="block"><h2 class="blockhead">By week — {len(self.weeks)} weeks,
    {len(self.d["items"])} items</h2>
    <div class="arch">{"".join(weeks)}</div>
  </section>{runs}

  {self.footer()}"""

    # -- briefs -------------------------------------------------------------
    def brief_card(self, dos) -> str:
        v = LANES.get(dos.get("lane", ""), {"name": "", "pill": "", "var": "--accent"})
        style = f'--ln:var({v["var"]})'
        status = escape(dos.get("status", ""))
        open_cls = " open" if dos.get("status", "").lower().startswith(("open", "active", "live")) else ""
        pill = (f'<span class="lanepill {v["pill"]}">{v["name"]}</span>' if v["pill"] else "")
        stat = f'<span class="dstatus{open_cls}">{status}</span>' if status else ""
        span = fmt_span(dos.get("opened", ""), dos.get("updated", ""))
        return (f'<a class="dcard" style="{style}" '
                f'href="{self.prefix}brief/{escape(dos["slug"], quote=True)}/">'
                f'<span class="top">{pill}{stat}</span>'
                f'<h3>{escape(dos["title"])}</h3>'
                f'<p>{escape(dos["summary"])}</p>'
                f'<span class="foot"><span>{len(dos.get("stages", []))} stages</span>'
                f'<span>{escape(span)}</span></span></a>')

    def brief_rail(self) -> str:
        """A short pointer to the briefs, printed on the board itself."""
        if not self.briefs:
            return ""
        cards = "".join(self.brief_card(x) for x in self.briefs[:3])
        more = ('<p class="lede" style="margin-top:12px">'
                f'<a href="{self.prefix}{BRIEFS_URL}">All {len(self.briefs)} briefs ↗</a></p>'
                if len(self.briefs) > 3 else "")
        return ('<section class="block"><h2 class="blockhead">Briefs — incidents in stages</h2>'
                '<p class="lede">Some stories are not a single item. A brief lays one out in '
                'dated stages, each stage carrying its own sources and its own confidence label, '
                'so what an organisation confirmed on day one stays distinguishable from what was '
                'reconstructed afterwards.</p>'
                f'<div class="dgrid">{cards}</div>{more}</section>')

    def briefs_body(self) -> str:
        cards = "".join(self.brief_card(x) for x in self.briefs)
        return f"""{self.nav(BRIEFS_URL)}

  <header class="pagehead">
    <h1>Briefs</h1>
    <div class="sub">Standout, complex incidents that require dedicated space,
      outlined chronologically.</div>
  </header>

  <section class="block"><h2 class="blockhead">{len(self.briefs)} brief{
      "" if len(self.briefs) == 1 else "s"}</h2>
    <div class="dgrid">{cards}</div>
  </section>

  {self.footer()}"""

    def stage_flags(self, s) -> str:
        """Two kinds of caveat, deliberately distinguished.

        "disputed" is a figure the sources disagree about — picking one number
        and staying quiet is exactly the failure mode the sourcing rules exist
        to prevent, so the disagreement is printed next to the claim. "note" is
        a scope limit: what the source does NOT say, which matters most where a
        stage sits next to another one it is easily read as explaining.
        """
        return "".join(
            f'<div class="flag"><b>{lbl}</b> {escape(s[k])}</div>'
            for k, lbl in (("disputed", "Contested:"), ("note", "Note:"))
            if s.get(k))

    def stage_meta(self, s) -> str:
        conf = s.get("confidence", "")
        conf_html = (f'<span class="conf c-{conf}">{CONF.get(conf, conf)}</span>'
                     if conf else "")
        srcs = " · ".join(
            f'<a href="{escape(src["url"], quote=True)}" target="_blank" rel="noopener">'
            f'{escape(src["outlet"])} ↗</a>'
            for src in s.get("sources", []))
        return f'<div class="meta">{conf_html}<span class="src">{srcs}</span></div>'

    def act_panels(self, dos, stages) -> str:
        """The act layout: numbered panels, some of them side by side.

        An act holds no facts of its own. Its bullets are the brief's own
        stages plus, optionally, board items folded in by id — so the same
        sentence never exists in two places and every line on the panel still
        carries the source it came from. Deleting acts[] from data.json gives
        back the plain timeline with nothing lost, which is the property that
        makes the layout safe to rearrange.
        """
        acts = dos.get("acts", [])
        by_act = {}
        for s in stages:
            by_act.setdefault(s.get("act"), []).append(s)

        # Group into rows first, because the numbering depends on it: acts
        # sharing a "row" value sit side by side and share a number, split by a
        # letter — 3A and 3B rather than 3 and 4. That is the whole signal of a
        # split row, that these are two answers to one question rather than two
        # consecutive beats. An act with no "row" gets a row of its own, keyed
        # on its position so it can never collide with a declared row number.
        rows, seen = [], {}
        for n, a in enumerate(acts):
            key = ("r", a["row"]) if a.get("row") is not None else ("solo", n)
            if key in seen:
                rows[seen[key]].append(a)
            else:
                seen[key] = len(rows)
                rows.append([a])

        out = []
        for r, group in enumerate(rows, 1):
            panels = []
            for k, a in enumerate(group):
                num = f"{r}{chr(65 + k)}" if len(group) > 1 else str(r)
                v = LANES.get(a.get("lane", dos.get("lane", "")),
                              {"name": "", "var": "--accent"})
                kind = escape(a.get("kind", "") or v["name"])
                when = escape(a.get("when", ""))

                # Stages and folded-in items interleave by date rather than
                # sitting in two blocks. A panel is a stretch of time, and a
                # reader following it down the page should not have to restart
                # at the top when the sourcing changes shape.
                pts = [(s["date"], self.act_point_stage(s))
                       for s in by_act.get(a["id"], [])]
                for iid in a.get("items", []):
                    it = self.by_id.get(iid)
                    if it:
                        pts.append((it["date"], self.act_point_item(it)))
                pts.sort(key=lambda x: x[0])

                note = (f'<div class="flag actnote"><b>Note:</b> {escape(a["note"])}</div>'
                        if a.get("note") else "")
                panels.append(
                    f'<section class="act" style="--ln:var({v["var"]})">'
                    f'<div class="acthead"><span class="actnum">{num}</span>'
                    f'<span class="actkind">{kind}</span>'
                    f'<span class="actwhen">{when}</span></div>'
                    f'<h3>{escape(a["headline"])}</h3>'
                    f'{note}<ul class="pts">{"".join(h for _, h in pts)}</ul></section>')
            out.append(f'<div class="actrow{" split" if len(panels) > 1 else ""}">'
                       f'{"".join(panels)}</div>')
        return "".join(out)

    def act_point_stage(self, s) -> str:
        return (f'<li><span class="pwhen">'
                f'<time datetime="{s["date"]}">{fmt_date(s["date"])}</time></span>'
                f'<b>{escape(s["label"])}</b> {escape(s["what"])}'
                f'{self.stage_meta(s)}{self.stage_flags(s)}</li>')

    def act_point_item(self, it) -> str:
        """A board item folded into a panel.

        It keeps its own headline, its own wording and its own link back to the
        lane page it was filed on, so a reader sees the item as filed rather
        than a paraphrase written for this panel — and the hollow bullet marks
        it as context the board already held, not something this brief found.
        """
        lv = LANES.get(it["lane"], {"page": "index.html"})
        conf = it.get("confidence", "")
        conf_html = (f'<span class="conf c-{conf}">{CONF.get(conf, conf)}</span>'
                     if conf else "")
        return (f'<li class="fold"><span class="pwhen">'
                f'<time datetime="{it["date"]}">{fmt_date(it["date"])}</time></span>'
                f'<b>{escape(it["headline"])}</b> {escape(it["core"])}'
                f'<div class="meta">{conf_html}<span class="src">'
                f'<a href="{escape(it["url"], quote=True)}" target="_blank" '
                f'rel="noopener">{escape(it["outlet"])} ↗</a> · '
                f'<a href="{self.prefix}{lv["page"]}#{escape(it["id"], quote=True)}">'
                f'on the board</a></span></div></li>')

    def brief_body(self, dos) -> str:
        v = LANES.get(dos.get("lane", ""), {"name": "", "var": "--accent"})
        stages = sorted(dos.get("stages", []), key=lambda s: s.get("date", ""))

        if dos.get("acts"):
            main = (f'<section class="block"><h2 class="blockhead">How it unfolded</h2>'
                    f'{self.act_panels(dos, stages)}</section>')
        else:
            rows = [f'<li style="--ln:var({v["var"]})">'
                    f'<span class="when"><time datetime="{s["date"]}">'
                    f'{fmt_date(s["date"])}</time></span>'
                    f'<h3>{escape(s["label"])}</h3>'
                    f'<p>{escape(s["what"])}</p>'
                    f'{self.stage_meta(s)}{self.stage_flags(s)}</li>'
                    for s in stages]
            main = ('<section class="block"><h2 class="blockhead">Timeline</h2>'
                    f'<ol class="tl">{"".join(rows)}</ol></section>')

        pool = [{"url": src["url"], "outlet": src["outlet"], "headline": s["label"],
                 "date": s["date"]}
                for s in stages for src in s.get("sources", [])]
        for a in dos.get("acts", []):
            for iid in a.get("items", []):
                it = self.by_id.get(iid)
                if it:
                    pool.append({"url": it["url"], "outlet": it["outlet"],
                                 "headline": it["headline"], "date": it["date"]})
        status = escape(dos.get("status", ""))
        stat = f'<span class="dstatus">{status}</span>' if status else ""
        return f"""{self.nav(BRIEFS_URL)}

  <header class="pagehead dhead">
    <h1>{escape(dos["title"])}<span class="lanerule" style="background:var({v["var"]})"></span></h1>
    <div class="sub">{escape(dos["summary"])}</div>
    <div class="dmeta">
      <span><b>Lane:</b> {escape(v["name"])}</span>
      <span><b>Stages:</b> {len(stages)}</span>
      <span><b>Span:</b> {escape(fmt_span(dos.get("opened", ""), dos.get("updated", "")))}</span>
      {stat}
    </div>
    <div class="stamp"><a href="{self.prefix}{BRIEFS_URL}">← All briefs</a></div>
  </header>

  {main}

  {self.sources_block(pool, "Sources cited in this brief")}

  {self.footer()}"""

    # -- about --------------------------------------------------------------
    def about_body(self) -> str:
        paras = "".join(f"<p>{escape(p)}</p>" for p in self.d.get("about", []))
        return f"""{self.nav(ABOUT_URL)}

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
            out.append("## New to the board")
            out.append("")
            for it in fresh:
                out.append(f"- **{LANES[it['lane']]['name']}** — {it['headline']}. "
                           f"[{it['outlet']}]({it['url']})")
            out.append("")
        else:
            out += ["## New to the board", "",
                    f"Nothing new to report since the last run. A fresh sweep across all "
                    f"{numword(len(LANES))} lanes surfaced no verified, in-window items that "
                    "weren't already shown. No items were invented to fill this space.", ""]

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
        if self.briefs:
            out += ["", "## Briefs", ""]
            for x in self.briefs:
                out.append(f"- **{x['title']}** — {x['summary']} "
                           f"[Full brief]({SITE_URL}/brief/{x['slug']}/)")
            out.append("")

        out += ["", "---", "",
                f"Every link above was opened and confirmed before publication. "
                f"The board lives at [{CNAME}]({SITE_URL}/).", ""]

        # Appends a working-notes section to the END OF THE DRAFT FILE, below a
        # visible cut line. It is the run's own account of the calls it made,
        # which is not the same thing as the editor's reasoning — so the human
        # publishing the post reads it, rewrites anything worth keeping in their
        # own words, and copies only the text ABOVE the cut line into Substack.
        # Nothing here is deleted from this file; the deletion happens in the
        # draft, by hand, at publishing time.
        out += ["<!-- ----- CUT HERE — nothing below this line is for publication ----- -->", "",
                "## Not for publication — working notes", "",
                "*Generated by the run, not written by the editor. "
                "Vet it, rewrite anything you want to keep in your own words, "
                "then delete this section before posting.*", "",
                "**Calls made this run**", "", self.d.get("judgmentNote", ""), "",
                "**Change since previous run**", "", self.d.get("internalNote", ""), ""]
        return "\n".join(out)

    # -- explore -------------------------------------------------------------
    def explore_payload(self) -> str:
        """The board's items as JSON, inlined into the page.

        Inlined rather than fetched so the page has no request to make, works
        from a file:// copy, and cannot render half a board if data.json is
        momentarily unavailable. Only the fields the view actually reads are
        included, and each item carries the lane page it lives on so every row
        can link back to its full card on the pre-rendered board.
        """
        dates = sorted({a["date"] for a in self.d.get("archives", []) if a.get("date")}, reverse=True)
        run_day = (self.as_of or "")[:10]
        prev = next((x for x in dates if x < run_day), "")
        payload = {
            "updatedDisplay": self.d.get("updatedDisplay", ""),
            "updatedISO": self.as_of,
            "coverage": self.coverage,
            "prevRun": prev,
            "lanes": [{"key": k, "name": v["name"]} for k, v in LANES.items()],
            "conf": CONF,
            "watchlist": [{"thread": w.get("thread", ""), "status": w.get("status", ""),
                           "changed": w.get("changed", "")} for w in self.d.get("watchlist", [])],
            "items": [{"id": i["id"], "lane": i["lane"], "date": i["date"],
                       "headline": i["headline"], "core": i["core"],
                       "confidence": i["confidence"], "outlet": i["outlet"],
                       "url": i["url"], "page": LANES[i["lane"]]["page"]}
                      for i in sorted(self.d["items"], key=lambda x: x["date"], reverse=True)],
        }
        # "<" is escaped so the payload can never close the script element early.
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")

    def explore_head(self) -> str:
        return (f'<link rel="stylesheet" href="board.css{asset_version("board.css")}">\n'
                f'<script id="msx-data" type="application/json">{self.explore_payload()}</script>\n'
                f'<script src="board.js{asset_version("board.js")}" defer></script>\n')

    def explore_body(self) -> str:
        """The mount point, a plain-language header, and a no-JS fallback.

        The fallback is not an apology — it is the same content the rest of the
        site already serves, so a reader without JavaScript is pointed at the
        week pages rather than at an empty box.
        """
        weeks = "".join(
            f'<li><a href="{self.prefix}week/{w["monday"]}/">{escape(w["label"])}</a> '
            f'&middot; {len(w["items"])} items</li>' for w in self.weeks)
        lane_bits = [f'<a href="{self.prefix}{v["page"]}">{v["name"]}</a>' for v in LANES.values()]
        if BOARD_PAGE:
            lane_bits.insert(0, f'<a href="{self.prefix}{BOARD_PAGE}">The full board</a>')
        lanes_links = " &middot; ".join(lane_bits)
        return f"""{self.nav(home_of("explore"), lanes=False)}

  <header class="pagehead board nohead">
    <p class="thesis">AI cyber capability against the defense and policy lag,
      tracked daily.</p>
    <p class="stampline"><span class="dot"></span>Updated
      <time datetime="{self.as_of}">{escape(self.d.get("updatedDisplay", ""))}</time>
      &nbsp;&middot;&nbsp; covering
      <time datetime="{self.cov_start}">{escape(self.coverage)}</time>
      &nbsp;&middot;&nbsp; {len(self.d["items"])} items in {numword(len(LANES))} lanes</p>
  </header>

  <div class="msx" id="msx">
    <noscript>
      <div class="msx-noscript">
        <p>Exploring by lane and week needs JavaScript. Every item is also
        pre-rendered on the pages below, which need none.</p>
        <p>{lanes_links}</p>
        <ul>{weeks}</ul>
      </div>
    </noscript>
  </div>

  {self.subscribe_block(compact=True)}

  {self.footer()}"""

    # -- sitemap -------------------------------------------------------------
    def sitemap(self) -> str:
        """Canonical routes only.

        Lane pages, the archive index, About and every week page — the pages
        meant to be found. Dated snapshots are deliberately left out: they are
        the same items again, and pointing crawlers at all of them would bury
        the live board under copies of itself.
        """
        day = (self.as_of or "")[:10]
        urls = [("", "daily", "1.0"), (ARCHIVE_URL, "daily", "0.6"),
                (ABOUT_URL, "monthly", "0.3")]
        urls += [(v["page"], "daily", "0.8") for v in LANES.values()]
        if EXPLORE_PAGE:
            # Whichever of the two is not the landing page needs its own entry — unless
            # it is not published, in which case there is nothing to point at.
            other = home_of("board") if LANDING == "explore" else EXPLORE_PAGE
            if other:
                urls.append((other, "daily", "0.9" if LANDING == "explore" else "0.7"))
        urls += [(f'week/{w["monday"]}/', "weekly" if n else "daily", "0.7")
                 for n, w in enumerate(self.weeks)]
        if self.briefs:
            urls.append((BRIEFS_URL, "weekly", "0.7"))
            urls += [(f'brief/{x["slug"]}/', "weekly", "0.7") for x in self.briefs]
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
    # The one request every browser makes without being asked. Without it the
    # server logs a 404 on every first page view — harmless, but it is the kind
    # of noise that hides a real missing asset the day one appears.
    shutil.copy(root / "assets" / "icon.svg", out_dir / "icon.svg")
    # The Explore page's stylesheet and script. Both are optional: with
    # EXPLORE_PAGE empty they are not copied and not referenced.
    if EXPLORE_PAGE:
        shutil.copy(root / "assets" / "board.css", out_dir / "board.css")
        shutil.copy(root / "assets" / "board.js", out_dir / "board.js")

    def write(path: str, html: str):
        p = out_dir / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(html, encoding="utf-8")
        print(f"  wrote {path}  ({len(html.encode()):,} bytes)")

    # the pre-rendered board and the interactive one; LANDING decides which is "/"
    board_path = home_of("board")
    if board_path:
        write(board_path, site.page(
            path=board_path,
            title=(f"{SITE_NAME} — AI-Cyber Intelligence" if board_path == "index.html"
                   else f"Full board — {SITE_NAME}"),
            description=SITE_DESCRIPTION,
            body=site.home_body(),
            extra_head=site.home_jsonld()))

    if EXPLORE_PAGE:
        explore_path = home_of("explore")
        # The ItemList follows whichever page is the landing page, so the structured
        # data always describes the URL that gets shared and indexed.
        write(explore_path, site.page(
            path=explore_path,
            title=(f"{SITE_NAME} — AI-Cyber Intelligence" if explore_path == "index.html"
                   else f"Explore — {SITE_NAME}"),
            description=(SITE_DESCRIPTION if explore_path == "index.html" else
                         "Filter the Machine Speed board by lane and week, follow a "
                         "running story across weeks, and see what is new since your "
                         "last visit."),
            body=site.explore_body(),
            extra_head=site.explore_head()
                       + (site.home_jsonld() if not board_path else "")))

    # /explore.html existed for a day and may be linked or bookmarked, so when it
    # becomes the landing page the old URL is kept as a redirect rather than a 404.
    if EXPLORE_PAGE and home_of("explore") != EXPLORE_PAGE:
        write(EXPLORE_PAGE,
              '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
              f'<title>Explore — {escape(SITE_NAME)}</title>\n'
              f'<link rel="canonical" href="{SITE_URL}/">\n'
              '<meta name="robots" content="noindex">\n'
              '<meta http-equiv="refresh" content="0; url=./">\n</head>\n'
              '<body><p>The Explore board is now the front page. '
              '<a href="./">Continue &#8594;</a></p></body>\n</html>\n')

    # lanes — one directory each, so the nav and the assets need a one-step prefix
    site.prefix = "../"
    for key, v in LANES.items():
        write(v["page"] + "index.html", site.page(
            path=v["page"] + "index.html",
            title=f"{v['name']} — {SITE_NAME}",
            description=f"{v['desc']} {site.coverage}, source-verified.",
            body=site.lane_body(key),
            asset_prefix="../"))
    site.prefix = ""

    # week pages — one directory per Monday-to-Sunday week, two levels down, so
    # both the nav links and the shared assets need a two-step relative prefix.
    site.prefix = "../../"
    for n, w in enumerate(site.weeks):
        write(w["path"], site.page(
            path=w["path"],
            title=f'{w["label"]} — {SITE_NAME}',
            description=(f'{len(w["items"])} source-verified AI-cyber items from '
                         f'{w["label"]}: '
                         + ", ".join(v["name"].lower() for v in LANES.values()) + "."),
            body=site.week_body(n),
            asset_prefix="../../"))
    site.prefix = ""

    # briefs — the index sits at the root, each brief two levels down under
    # /brief/<slug>/, so the prefixes follow the same pattern as the weeks.
    if site.briefs:
        site.prefix = "../"
        write(BRIEFS_URL + "index.html", site.page(
            path=BRIEFS_URL + "index.html", title=f"Briefs — {SITE_NAME}",
            description=("Standout, complex incidents that require dedicated space, "
                         "outlined chronologically."),
            body=site.briefs_body(),
            asset_prefix="../"))
        site.prefix = ""
        site.prefix = "../../"
        for dos in site.briefs:
            write(f'brief/{dos["slug"]}/index.html', site.page(
                path=f'brief/{dos["slug"]}/index.html',
                title=f'{dos["title"]} — {SITE_NAME}',
                description=dos["summary"][:180],
                body=site.brief_body(dos),
                asset_prefix="../../"))
        site.prefix = ""

    # archive index + about
    site.prefix = "../"
    write(ARCHIVE_URL + "index.html", site.page(
        path=ARCHIVE_URL + "index.html", title=f"Archive — {SITE_NAME}",
        description="The Machine Speed board, split into weekly pages.",
        body=site.archive_body(),
        asset_prefix="../"))
    write(ABOUT_URL + "index.html", site.page(
        path=ABOUT_URL + "index.html", title=f"About — {SITE_NAME}",
        description=SITE_DESCRIPTION, body=site.about_body(),
        asset_prefix="../"))
    site.prefix = ""

    # Redirect stubs at the old flat paths. Permanent: the frozen snapshots in
    # archive/ link to them and are never rewritten.
    for old, new in LEGACY_PATHS.items():
        if new == BRIEFS_URL and not site.briefs:
            continue          # no briefs means no /briefs/ to send anyone to
        write(old,
              '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
              f'<link rel="canonical" href="{SITE_URL}/{new}">\n'
              '<meta name="robots" content="noindex">\n'
              f'<meta http-equiv="refresh" content="0; url=./{new}">\n</head>\n'
              f'<body><p><a href="./{new}">Continue &#8594;</a></p></body>\n</html>\n')

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
                  f'{fmt_date(snap_date)}. <a href="../">Back to the live board ↗</a></div>')
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
          f"{len(site.fresh_items())} in the 'New to the board' strip, "
          f"{len(data['watchlist'])} watchlist threads")
    if site.briefs:
        acts = sum(len(b.get("acts", [])) for b in site.briefs)
        stages = sum(len(b.get("stages", [])) for b in site.briefs)
        print(f"  {len(site.briefs)} brief{'' if len(site.briefs) == 1 else 's'}, "
              f"{stages} stages, {acts} acts")
    print(f"  site: {SITE_URL}")
    if not SUBSTACK_URL:
        print("  note: SUBSTACK_URL is unset — subscribe links are hidden. "
              "Set it at the top of build.py to turn them on.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist", help="output directory (default: dist)")
    args = ap.parse_args()
    build(Path(args.out).resolve())
