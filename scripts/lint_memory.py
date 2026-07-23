#!/usr/bin/env python3
"""Check stored session metadata and its derived JSONL index."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from wiki_memory import index_record, project_paths, read_frontmatter, validate_session


def lint(project: Path) -> list[str]:
    paths = project_paths(project)
    errors = []
    expected = {}
    for session in sorted(paths["sessions"].glob("*.md")):
        try:
            data = read_frontmatter(session)
            identifier = data.pop("id")
            validate_session(data)
            expected[identifier] = index_record(data, identifier, session.relative_to(project).as_posix())
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            errors.append(str(exc))
    actual = {}
    if paths["index"].exists():
        for number, line in enumerate(paths["index"].read_text(encoding="utf-8").splitlines(), 1):
            if not line:
                continue
            try:
                row = json.loads(line)
                identifier = row["id"]
                if identifier in actual:
                    errors.append(f"duplicate index record for {identifier}")
                actual[identifier] = row
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                errors.append(f"index line {number}: {exc}")
    for identifier, record in expected.items():
        if actual.get(identifier) != record:
            errors.append(f"index drift for {identifier}")
    for identifier in sorted(set(actual) - set(expected)):
        errors.append(f"stale index record for {identifier}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    errors = lint(args.project.resolve())
    if errors:
        print("\n".join(f"error: {error}" for error in errors), file=sys.stderr)
        raise SystemExit(1)
    print("memory lint passed")


if __name__ == "__main__":
    main()
