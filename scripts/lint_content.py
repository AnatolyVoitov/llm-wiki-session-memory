#!/usr/bin/env python3
"""Validate knowledge-card metadata, relations, and the derived content index."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from wiki_memory import build_content_index, project_paths


SYMMETRIC_RELATIONS = {"complements", "related-to"}
INVERSE_RELATIONS = {"replaces": "replaced-by", "replaced-by": "replaces"}
IMPORTANT_TYPES = {"skill", "project", "source", "repository", "concept", "synthesis"}


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


def graph_errors(project: Path) -> list[str]:
    try:
        records = build_content_index(project)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [str(exc)]
    edges = {(record["id"], relation["type"], relation["target"]) for record in records for relation in record["relations"]}
    connected = {source for source, _, _ in edges} | {target for _, _, target in edges}
    errors = []
    for record in records:
        identifier = record["id"]
        seen = set()
        for relation in record["relations"]:
            edge = (relation["type"], relation["target"])
            if edge in seen:
                errors.append(f"duplicate-relation: duplicate relation from {identifier} to {relation['target']}")
                continue
            seen.add(edge)
            if relation["type"] in SYMMETRIC_RELATIONS and (relation["target"], relation["type"], identifier) not in edges:
                errors.append(f"missing-symmetric-relation: missing {relation['type']} relation from {relation['target']} to {identifier}")
            inverse_type = INVERSE_RELATIONS.get(relation["type"])
            if inverse_type and (relation["target"], inverse_type, identifier) not in edges:
                errors.append(f"missing-inverse-relation: {relation['type']} relation from {identifier} to {relation['target']} has no {inverse_type} inverse")
        if record["type"] in IMPORTANT_TYPES and identifier not in connected:
            errors.append(f"isolated-important-card: important card has no relations ({identifier})")
    return errors


def strict_errors(project: Path) -> list[str]:
    from audit_content import audit

    audit_errors = [f"{item['code']}: {item['message']} ({item['card_id']})" for item in audit(project) if item["severity"] == "error"]
    return graph_errors(project) + audit_errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--strict", action="store_true", help="also fail on content-audit errors")
    args = parser.parse_args()
    project = args.project.resolve()
    errors = lint(project)
    if args.strict:
        errors.extend(strict_errors(project))
    if errors:
        print("\n".join(f"error: {error}" for error in errors), file=sys.stderr)
        raise SystemExit(1)
    print("content lint passed")


if __name__ == "__main__":
    main()
