#!/usr/bin/env python3
"""Build the derived local index for Markdown knowledge cards."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from bootstrap import bootstrap
from wiki_memory import write_content_index


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    try:
        project = args.project.resolve()
        bootstrap(project)
        records = write_content_index(project)
        print(f"indexed {len(records)} content cards")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
