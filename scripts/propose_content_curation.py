#!/usr/bin/env python3
"""Create a review-only curation proposal from content-quality findings."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from audit_content import audit


def proposal_for(project: Path) -> dict:
    findings = audit(project)
    updates = {}
    for item in findings:
        update = updates.setdefault(item["card_id"], {"id": item["card_id"], "path": item["path"], "review": []})
        update["review"].append({"code": item["code"], "severity": item["severity"], "message": item["message"]})
    return {
        "proposal_version": 1,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "findings": findings,
        "updates": list(updates.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    proposal = proposal_for(args.project.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(proposal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
