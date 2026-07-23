#!/usr/bin/env python3
"""Search Markdown knowledge cards by type, tag, time, or text."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

from wiki_memory import project_paths


def searchable(value: str) -> str:
    return re.sub(r"[-_:/]+", " ", value.lower())


def matches(row: dict, args: argparse.Namespace) -> bool:
    if args.type and row["type"] != args.type:
        return False
    if args.tag and args.tag not in row["tags"]:
        return False
    added = date.fromisoformat(row["dates"]["added_at"][:10])
    if args.added_since and added < date.fromisoformat(args.added_since):
        return False
    if args.added_before and added > date.fromisoformat(args.added_before):
        return False
    if args.text:
        haystack = searchable(" ".join([row["title"], row["description"], *row["aliases"], *row["tags"]]))
        if searchable(args.text) not in haystack:
            return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--type")
    parser.add_argument("--tag")
    parser.add_argument("--added-since")
    parser.add_argument("--added-before")
    parser.add_argument("--text")
    args = parser.parse_args()
    index = project_paths(args.project.resolve())["content_index"]
    if not index.exists():
        raise SystemExit("error: content index is missing; run rebuild_content_index.py first")
    for row in (json.loads(line) for line in index.read_text(encoding="utf-8").splitlines() if line):
        if matches(row, args):
            print(f"{row['type']} | {row['title']} | {row['path']}")


if __name__ == "__main__":
    main()
