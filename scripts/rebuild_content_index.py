#!/usr/bin/env python3
"""Build the derived local index for Markdown knowledge cards."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from bootstrap import bootstrap
from wiki_memory import build_content_index, project_paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    try:
        project = args.project.resolve()
        bootstrap(project)
        records = build_content_index(project)
        index = project_paths(project)["content_index"]
        index.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records), encoding="utf-8")
        print(f"indexed {len(records)} content cards")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
