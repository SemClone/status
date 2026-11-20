#!/usr/bin/env python3
"""
One-off: rebuild docs/data/history.json from every committed stats.json.

Each committed snapshot carries the ~180 days pypistats served that day, so
replaying them oldest to newest recovers every day since tracking began.
Later snapshots win for a day they share, matching what fetch_stats.py does.
Rows already in history.json are kept unless a snapshot carries the same day.

Run from the repository root: python3 scripts/backfill_history.py
"""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.getcwd())
from fetch_stats import load_history, merge_overall_into_history, save_history  # noqa: E402

STATS = "docs/data/stats.json"


def main() -> None:
    commits = subprocess.check_output(
        ["git", "log", "--reverse", "--format=%H", "--", STATS], text=True).split()
    history = load_history()
    read = failed = 0
    for sha in commits:
        try:
            snap = json.loads(subprocess.check_output(["git", "show", f"{sha}:{STATS}"]))
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            failed += 1
            continue
        for package, stats in (snap.get("packages") or {}).items():
            merge_overall_into_history(history, package, stats.get("overall"))
        read += 1
    save_history(history)
    print(f"{len(commits)} snapshots: {read} read, {failed} unreadable")
    if read == 0:
        sys.exit("no snapshot could be read; history.json not trustworthy")


if __name__ == "__main__":
    main()
