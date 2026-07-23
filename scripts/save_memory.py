#!/usr/bin/env python3
"""Validate and store one structured session summary from a JSON input file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from bootstrap import bootstrap
from wiki_memory import index_record, project_paths, render_session, session_id, slug, validate_session


def handoff_section(title: str, items: list[str], fallback: str) -> list[str]:
    lines = [f"## {title}", ""]
    lines.extend(f"- {item}" for item in items) if items else lines.append(f"- {fallback}")
    lines.append("")
    return lines


def render_handoff(data: dict, relative: str) -> str:
    lines = ["# Session Handoff", "", "## Active Context", "", f"- Last session: `{relative}`", f"- Current objective: {data['task']}", ""]
    lines.extend(handoff_section("Current Decisions", data.get("decisions", []), "No new decisions recorded."))
    lines.extend(handoff_section("Open Tasks", data.get("open_tasks", []), "No open tasks recorded."))
    lines.extend(handoff_section("Blockers", data.get("blockers", []), "No blockers recorded."))
    lines.extend(handoff_section("Next Action", data.get("next_actions", []), "Review the latest session and continue only with verified context."))
    lines.extend(handoff_section("Relevant Pages", data.get("relevant_pages", ["`wiki/index.md`"]), "`wiki/index.md`"))
    return "\n".join(lines)


def save(project: Path, payload: Path) -> Path:
    data = json.loads(payload.read_text(encoding="utf-8"))
    validate_session(data)
    bootstrap(project)
    identifier = session_id(data)
    filename = f"{data['ended_at'][:10]}-{slug(data['task'])}.md"
    paths = project_paths(project)
    target = paths["sessions"] / filename
    if target.exists():
        raise ValueError(f"session already exists: {target.relative_to(project)}")
    target.write_text(render_session(data, identifier), encoding="utf-8")
    relative = target.relative_to(project).as_posix()
    with paths["index"].open("a", encoding="utf-8") as index:
        index.write(json.dumps(index_record(data, identifier, relative), ensure_ascii=False) + "\n")
    paths["log"].open("a", encoding="utf-8").write(
        f"\n## [{data['ended_at'][:10]}] session | {data['task']}\n\n"
        f"- Raw: `{relative}`\n- Tags: {', '.join(f'`{tag}`' for tag in data['tags'])}\n"
        f"- Status: `{data['status']}`\n"
    )
    paths["handoff"].write_text(render_handoff(data, relative), encoding="utf-8")
    return target.relative_to(project)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("payload", type=Path, help="JSON session metadata produced by the agent")
    args = parser.parse_args()
    try:
        print(save(args.project.resolve(), args.payload.resolve()))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
