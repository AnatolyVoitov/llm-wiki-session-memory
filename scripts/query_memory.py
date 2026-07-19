#!/usr/bin/env python3
"""Search the local session index by time, tag, file, or status."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from wiki_memory import project_paths


def matches(row: dict, args: argparse.Namespace) -> bool:
    if args.tag and args.tag not in row["tags"]:
        return False
    if args.file and args.file not in row["files"]:
        return False
    if args.status and row["status"] != args.status:
        return False
    if args.yesterday:
        zone = ZoneInfo(args.timezone)
        today = datetime.now(zone).date()
        target = today - timedelta(days=1)
        return datetime.fromisoformat(row["started_at"]).astimezone(zone).date() == target
    return True


def query(project: Path, args: argparse.Namespace) -> list[dict]:
    index = project_paths(project)["index"]
    if not index.exists():
        return []
    rows = [json.loads(line) for line in index.read_text(encoding="utf-8").splitlines() if line]
    return [row for row in rows if matches(row, args)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--yesterday", action="store_true")
    parser.add_argument("--timezone", default="UTC")
    parser.add_argument("--tag")
    parser.add_argument("--file")
    parser.add_argument("--status")
    args = parser.parse_args()
    for row in query(args.project.resolve(), args):
        print(f"{row['ended_at'][:10]} | {row['status']} | {row['task']} | {row['source']}")


if __name__ == "__main__":
    main()
