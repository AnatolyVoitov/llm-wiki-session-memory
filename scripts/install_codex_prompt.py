#!/usr/bin/env python3
"""Install the optional user-local `/prompts:save-memory` Codex prompt."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "templates" / "prompts" / "save-memory.md"


def install(codex_home: Path, force: bool = False) -> Path:
    target = codex_home / "prompts" / "save-memory.md"
    if target.exists() and not force:
        raise FileExistsError(f"refusing to overwrite {target}; pass --force to replace it")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE, target)
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", type=Path, required=True, help="Codex home directory, for example ~/.codex")
    parser.add_argument("--force", action="store_true", help="replace an existing save-memory prompt")
    args = parser.parse_args()
    try:
        print(install(args.codex_home.expanduser(), args.force))
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
