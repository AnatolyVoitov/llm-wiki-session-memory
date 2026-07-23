#!/usr/bin/env python3
"""Add safe baseline metadata to an existing Markdown Wiki without rewriting bodies."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

from bootstrap import bootstrap
from wiki_memory import SCHEMA_VERSION, read_frontmatter, slug


STRUCTURAL_FILES = {"index.md", "log.md", "source-manifest.md", "session-handoff.md"}
TYPE_BY_DIRECTORY = {
    "skills": "skill",
    "sources": "source",
    "concepts": "concept",
    "syntheses": "synthesis",
    "questions": "question",
    "projects": "project",
    "entities": "concept",
    "tools": "tool",
    "mcp": "tool",
}
LINK = re.compile(r"\[\[([^\]|#]+)")


def candidates(project: Path, include_metadata: bool = False) -> list[Path]:
    wiki = project / "wiki"
    return [
        path for path in sorted(wiki.rglob("*.md"))
        if path.relative_to(wiki).as_posix() not in STRUCTURAL_FILES
        and (include_metadata or not path.read_text(encoding="utf-8").startswith("---\n"))
    ]


def card_id(project: Path, path: Path) -> str:
    relative = path.relative_to(project / "wiki").with_suffix("")
    return ".".join(slug(part) for part in relative.parts)


def card_type(project: Path, path: Path, body: str) -> str:
    relative = path.relative_to(project / "wiki")
    directory = relative.parts[0] if len(relative.parts) > 1 else ""
    if directory == "entities" and re.search(r"^Type:\s*skill\b", body, re.MULTILINE | re.IGNORECASE):
        return "skill"
    return TYPE_BY_DIRECTORY.get(directory, "concept")


def tags_for(project: Path, path: Path, content_type: str) -> list[str]:
    value = path.relative_to(project / "wiki").as_posix().lower()
    tags = [f"topic:{slug(path.stem)}"]
    if content_type == "skill":
        tags.append("capability:agent-skills")
    if any(word in value for word in ("design", "figma", "frontend", "mobile", "impeccable", "taste")):
        tags.extend(["domain:web-design", "capability:ui-design"])
    if any(word in value for word in ("agent", "llm", "memory", "harness", "prompt")):
        tags.append("domain:ai-agents")
    if any(word in value for word in ("wiki", "memory", "context")):
        tags.append("topic:context-engineering")
    return list(dict.fromkeys(tags))


def title_for(path: Path, body: str) -> str:
    heading = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    return heading.group(1).strip() if heading else path.stem.replace("-", " ").replace("_", " ").title()


def source_for(project: Path, path: Path, body: str) -> dict:
    match = re.search(r"^(?:Raw source|Source):\s*`?([^`\n]+)`?", body, re.MULTILINE | re.IGNORECASE)
    if match:
        source = match.group(1).strip()
        if source.startswith("http://") or source.startswith("https://"):
            return {"url": source}
        return {"raw_path": source}
    return {"wiki_path": path.relative_to(project).as_posix()}


def resolve_link(project: Path, path: Path, reference: str, ids: dict[Path, str]) -> str | None:
    wiki = project / "wiki"
    reference = reference.strip()
    choices = [wiki / f"{reference}.md", path.parent / f"{reference}.md"]
    for choice in choices:
        try:
            normalized = choice.resolve()
        except OSError:
            continue
        if normalized in ids:
            return ids[normalized]
    return None


def render_metadata(metadata: dict) -> str:
    return "---\n" + "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in metadata.items()) + "\n---\n\n"


def body_after_frontmatter(content: str) -> str:
    close = content.find("\n---\n", 4)
    if close < 0:
        raise ValueError("metadata front matter is not closed")
    return content[close + 5:]


def migrate(project: Path, refresh_types: bool = False, upgrade_schema: bool = False) -> list[Path]:
    bootstrap(project)
    paths = candidates(project, include_metadata=refresh_types or upgrade_schema)
    ids = {path.resolve(): card_id(project, path) for path in paths}
    migrated = []
    for path in paths:
        content = path.read_text(encoding="utf-8")
        existing = content.startswith("---\n")
        body = body_after_frontmatter(content) if existing else content
        content_type = card_type(project, path, body)
        if existing:
            metadata = read_frontmatter(path)
            changed = False
            if refresh_types and metadata.get("type") != content_type:
                metadata["type"] = content_type
                changed = True
            if upgrade_schema and "schema_version" not in metadata:
                metadata = {"schema_version": SCHEMA_VERSION, **metadata}
                changed = True
            if changed:
                path.write_text(render_metadata(metadata) + body, encoding="utf-8")
                migrated.append(path.relative_to(project))
            continue
        modified_at = datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds")
        relations = []
        for reference in LINK.findall(body):
            target = resolve_link(project, path, reference, ids)
            if target and target != ids[path.resolve()]:
                relation = {"type": "related-to", "target": target}
                if relation not in relations:
                    relations.append(relation)
        metadata = {
            "id": ids[path.resolve()],
            "type": content_type,
            "title": title_for(path, body),
            "description": f"Maintained {content_type} card: {title_for(path, body)}.",
            "tags": tags_for(project, path, content_type),
            "source": source_for(project, path, body),
            "dates": {"added_at": modified_at, "updated_at": modified_at},
            "relations": relations,
            "aliases": [],
            "status": "active",
        }
        path.write_text(render_metadata(metadata) + body, encoding="utf-8")
        migrated.append(path.relative_to(project))
    return migrated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--refresh-types", action="store_true", help="correct inferred types on existing cards without changing other metadata")
    parser.add_argument("--upgrade-schema", action="store_true", help="add schema_version 2 to existing cards without changing other metadata")
    args = parser.parse_args()
    for path in migrate(args.project.resolve(), refresh_types=args.refresh_types, upgrade_schema=args.upgrade_schema):
        print(path)


if __name__ == "__main__":
    main()
