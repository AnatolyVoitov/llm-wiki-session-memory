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


def graph_neighbors(records: list[dict], identifier: str, relation_type: str | None) -> list[tuple[str, str, str]]:
    identifiers = {record.get("id") for record in records}
    if identifier not in identifiers:
        raise ValueError(f"unknown card id: {identifier}")
    neighbors = []
    for record in records:
        source = record.get("id")
        relations = record.get("relations")
        if not isinstance(source, str) or not isinstance(relations, list):
            raise ValueError(f"malformed content index record: {source or '<unknown>'}")
        for relation in relations:
            if not isinstance(relation, dict) or not isinstance(relation.get("type"), str) or not isinstance(relation.get("target"), str):
                raise ValueError(f"malformed relation on card {source}")
            if relation_type and relation["type"] != relation_type:
                continue
            if source == identifier:
                neighbors.append(("outgoing", relation["type"], relation["target"]))
            elif relation["target"] == identifier:
                neighbors.append(("incoming", relation["type"], source))
    direction_order = {"outgoing": 0, "incoming": 1}
    return sorted(neighbors, key=lambda row: (direction_order[row[0]], row[1], row[2]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--type")
    parser.add_argument("--tag")
    parser.add_argument("--added-since")
    parser.add_argument("--added-before")
    parser.add_argument("--text")
    graph = parser.add_mutually_exclusive_group()
    graph.add_argument("--related-to", metavar="CARD_ID")
    graph.add_argument("--complements", metavar="CARD_ID")
    args = parser.parse_args()
    index = project_paths(args.project.resolve())["content_index"]
    if not index.exists():
        raise SystemExit("error: content index is missing; run rebuild_content_index.py first")
    try:
        records = [json.loads(line) for line in index.read_text(encoding="utf-8").splitlines() if line]
    except json.JSONDecodeError as exc:
        raise SystemExit(f"error: invalid content index: {exc}") from exc
    identifier = args.related_to or args.complements
    if identifier:
        try:
            relation_type = "complements" if args.complements else None
            for direction, kind, neighbor in graph_neighbors(records, identifier, relation_type):
                print(f"{direction} | {kind} | {neighbor}")
        except ValueError as exc:
            raise SystemExit(f"error: {exc}") from exc
        return
    for row in records:
        if matches(row, args):
            print(f"{row['type']} | {row['title']} | {row['path']}")


if __name__ == "__main__":
    main()
