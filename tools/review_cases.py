#!/usr/bin/env python3
"""
Review the tracker cases in editorial/trackers.json.

    python3 tools/review_cases.py                      list what is waiting
    python3 tools/review_cases.py --approve php2shell  mark one case reviewed (repeatable)
    python3 tools/review_cases.py --approve-topic critical-infrastructure
    python3 tools/review_cases.py --approve-all

A case stays off the site until it is marked reviewed. To change what a stop says,
edit its text in editorial/trackers.json first, then approve. The full checklist, with the
headlines each case rests on, is written to newsletter/review-trackers.md by every
build; `python3 build.py --drafts` previews unreviewed cases locally.
"""
import argparse
import json
import sys
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "editorial" / "trackers.json"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--approve", action="append", default=[], metavar="CASE_ID")
    ap.add_argument("--approve-topic", action="append", default=[], metavar="TOPIC_ID")
    ap.add_argument("--approve-all", action="store_true")
    args = ap.parse_args()
    doc = json.loads(PATH.read_text(encoding="utf-8"))
    known = {c["id"] for tr in doc["trackers"] for c in tr["cases"]}
    topics = {tr["topic"] for tr in doc["trackers"]}
    bad = [c for c in args.approve if c not in known] + [t for t in args.approve_topic if t not in topics]
    if bad:
        sys.exit("not found in editorial/trackers.json: " + ", ".join(bad))
    changed = 0
    for tr in doc["trackers"]:
        for c in tr["cases"]:
            if c.get("reviewed"):
                continue
            if args.approve_all or tr["topic"] in args.approve_topic or c["id"] in args.approve:
                c["reviewed"] = True
                changed += 1
    if changed:
        PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"marked {changed} case(s) reviewed")
    for tr in doc["trackers"]:
        waiting = [c for c in tr["cases"] if not c.get("reviewed")]
        print(f"\n{tr['topic']}: {len(tr['cases']) - len(waiting)} reviewed, {len(waiting)} waiting")
        for c in waiting:
            print(f"  {c['id']:<14} {c['name']}")


if __name__ == "__main__":
    main()
