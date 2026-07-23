#!/usr/bin/env python3
"""Report quality findings for knowledge cards without modifying the Wiki."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from wiki_memory import content_cards, content_schema_version


def finding(card: dict, path: Path, severity: str, code: str, message: str) -> dict:
    return {
        "severity": severity,
        "code": code,
        "card_id": card["id"],
        "path": path.as_posix(),
        "message": message,
    }


def audit(project: Path) -> list[dict]:
    findings = []
    title_paths: dict[str, Path] = {}
    for path, card in content_cards(project):
        relative = path.relative_to(project)
        if content_schema_version(card) == 1:
            findings.append(finding(card, relative, "warning", "legacy-schema", "Card has no schema_version: 2."))
        if re.fullmatch(r"Maintained [a-z-]+ card: .+\.", card["description"]):
            findings.append(finding(card, relative, "warning", "generic-description", "Replace the migration-generated description with a useful summary."))
        if len(card["tags"]) == 1 and card["tags"][0].startswith("topic:"):
            findings.append(finding(card, relative, "suggestion", "generated-only-tags", "Add at least one domain, capability, workflow, tool, or platform tag."))
        if len(card["tags"]) != len(set(card["tags"])):
            findings.append(finding(card, relative, "warning", "duplicate-tags", "Remove duplicate tags."))
        if len(card["aliases"]) != len(set(alias.lower() for alias in card["aliases"])):
            findings.append(finding(card, relative, "warning", "duplicate-aliases", "Remove duplicate aliases."))
        if any(relation["type"] == "related-to" for relation in card["relations"]):
            findings.append(finding(card, relative, "suggestion", "generic-relation", "Review generic related-to links and use a semantic relation when known."))
        if card["type"] in {"article", "repository", "source"} and set(card["source"]) == {"wiki_path"}:
            findings.append(finding(card, relative, "error", "missing-external-source", "Add the source URL, repository, or raw path when known."))
        title = card["title"].strip().lower()
        if title in title_paths:
            findings.append(finding(card, relative, "suggestion", "duplicate-title", f"Title duplicates {title_paths[title].relative_to(project)}."))
        else:
            title_paths[title] = path
    return findings


def render_markdown(findings: list[dict]) -> str:
    if not findings:
        return "# Content Quality Audit\n\nNo findings.\n"
    lines = ["# Content Quality Audit", ""]
    for item in findings:
        lines.append(f"- [{item['severity']}] `{item['code']}` `{item['card_id']}`: {item['message']}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    args = parser.parse_args()
    findings = audit(args.project.resolve())
    if args.format == "json":
        print(json.dumps(findings, ensure_ascii=False, indent=2))
    else:
        print(render_markdown(findings), end="")


if __name__ == "__main__":
    main()
