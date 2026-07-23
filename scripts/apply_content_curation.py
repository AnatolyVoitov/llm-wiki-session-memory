#!/usr/bin/env python3
"""Apply explicitly approved metadata updates from a reviewed curation proposal."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from wiki_memory import content_body, content_cards, read_frontmatter, render_content_frontmatter, validate_content, write_content_index


ALLOWED_FIELDS = {"type", "title", "description", "tags", "source", "relations", "aliases", "status"}


def apply(project: Path, proposal_path: Path, approved: set[str]) -> list[str]:
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    if proposal.get("proposal_version") != 1:
        raise ValueError("unsupported curation proposal_version")
    updates = {item.get("id"): item for item in proposal.get("updates", []) if item.get("id")}
    missing = approved - updates.keys()
    if missing:
        raise ValueError("approved card IDs missing from proposal: " + ", ".join(sorted(missing)))
    cards = {data["id"]: path for path, data in content_cards(project)}
    changed = []
    for identifier in sorted(approved):
        if identifier not in cards:
            raise ValueError(f"approved card does not exist: {identifier}")
        update = updates[identifier]
        fields = set(update) - {"id", "path", "review", "reasons"}
        unknown = fields - ALLOWED_FIELDS
        if unknown:
            raise ValueError("unsupported curation fields: " + ", ".join(sorted(unknown)))
        if not fields:
            continue
        path = cards[identifier]
        metadata = read_frontmatter(path)
        for field in fields:
            metadata[field] = update[field]
        metadata["dates"]["updated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        validate_content(metadata)
        path.write_text(render_content_frontmatter(metadata) + content_body(path), encoding="utf-8")
        changed.append(identifier)
    write_content_index(project)
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("proposal", type=Path)
    parser.add_argument("--approve", action="append", required=True, metavar="CARD_ID")
    args = parser.parse_args()
    try:
        for identifier in apply(args.project.resolve(), args.proposal.resolve(), set(args.approve)):
            print(identifier)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
