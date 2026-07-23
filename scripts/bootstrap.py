#!/usr/bin/env python3
"""Create the LLM Wiki structure without replacing user-owned files."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"


def copy_if_missing(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copyfile(source, target)


def bootstrap(project: Path) -> list[Path]:
    created = []
    for directory in ("raw/sources", "raw/sessions", "raw/assets", "wiki/sources", "wiki/concepts", "wiki/syntheses", "wiki/assets", "wiki/curation", "commands"):
        path = project / directory
        if not path.exists():
            path.mkdir(parents=True)
            created.append(path)
    for relative in ("AGENTS.md", "wiki/index.md", "wiki/log.md", "wiki/session-handoff.md", "wiki/session-index.jsonl", "wiki/content-index.jsonl", "wiki/tag-taxonomy.yml", "commands/save-memory.md"):
        target = project / relative
        source = TEMPLATES / relative
        if not target.exists():
            copy_if_missing(source, target)
            created.append(target)
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    for path in bootstrap(args.project.resolve()):
        print(path.relative_to(args.project.resolve()))


if __name__ == "__main__":
    main()
