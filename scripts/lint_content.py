#!/usr/bin/env python3
"""Validate knowledge-card metadata, relations, and the derived content index."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from wiki_memory import build_content_index, project_paths


def lint(project: Path) -> list[str]:
    try:
        expected = build_content_index(project)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [str(exc)]
    errors = []
    ids = {record["id"] for record in expected}
    for record in expected:
        for relation in record["relations"]:
            if relation["target"] not in ids:
                errors.append(f"unresolved relation from {record['id']} to {relation['target']}")
    index = project_paths(project)["content_index"]
    actual = []
    if index.exists():
        try:
            actual = [json.loads(line) for line in index.read_text(encoding="utf-8").splitlines() if line]
        except json.JSONDecodeError as exc:
            errors.append(f"invalid content index: {exc}")
    if actual != expected:
        errors.append("content index drift; run rebuild_content_index.py")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    errors = lint(args.project.resolve())
    if errors:
        print("\n".join(f"error: {error}" for error in errors), file=sys.stderr)
        raise SystemExit(1)
    print("content lint passed")


if __name__ == "__main__":
    main()
