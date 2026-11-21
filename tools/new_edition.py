#!/usr/bin/env python3
"""
Start an edition file for a week, pre-filled with suggestions.

    python3 tools/new_edition.py              the newest week on the board
    python3 tools/new_edition.py 2026-11-09   the week starting that Monday

Writes editorial/editions/<monday>.json with "ready": false, so the build ignores it until
you have finished. In the file:

    note    one or two sentences on the week (optional)
    picks   up to five items, each with a one-line "why" (suggested: the week's key items)
    lanes   one more item per lane, shown under the picks (suggested: the next key or newest item)

Each suggestion carries its headline beside the id so you can read the file without
looking anything up; the build ignores those "_headline" lines. Fill in the "why"
lines, swap any item id you disagree with, set "ready": true, and build.
Until then the week's edition is generated from its key items on its own.
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANES = ["cap", "pol", "def", "atk", "mkt"]


def main():
    items = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))["items"]

    def monday(iso):
        d = date.fromisoformat(iso)
        return (d - timedelta(days=d.weekday())).isoformat()

    week = sys.argv[1] if len(sys.argv) > 1 else max(monday(i["date"]) for i in items)
    if date.fromisoformat(week).weekday() != 0:
        sys.exit(f"{week} is not a Monday")
    pool = sorted((i for i in items if monday(i["date"]) == week), key=lambda i: i["date"], reverse=True)
    if not pool:
        sys.exit(f"no items on the board for the week of {week}")
    out = ROOT / "editorial" / "editions" / f"{week}.json"
    if out.exists():
        sys.exit(f"{out.relative_to(ROOT)} already exists — edit it instead")
    ranked = [i for i in pool if i.get("key")] + [i for i in pool if not i.get("key")]
    picks = ranked[:5]
    used = {i["id"] for i in picks}
    lanes, hints = {}, {}
    for k in LANES:
        nxt = next((i for i in ranked if i["lane"] == k and i["id"] not in used), None)
        if nxt:
            lanes[k] = nxt["id"]
            hints[k] = nxt["headline"]
    doc = {
        "week": week,
        "ready": False,
        "note": "",
        "picks": [{"item": i["id"], "_headline": i["headline"], "why": ""} for i in picks],
        "lanes": lanes,
        "_lane_headlines": hints,
    }
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} — {len(pool)} items that week, {len(picks)} suggested picks")
    print('fill in each "why", then set "ready": true')


if __name__ == "__main__":
    main()
