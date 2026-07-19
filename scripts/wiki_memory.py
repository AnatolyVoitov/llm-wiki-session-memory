"""Shared helpers for the local, dependency-free LLM Wiki memory workflow."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path


REQUIRED_FIELDS = (
    "started_at", "ended_at", "timezone", "agent", "task", "status",
    "transcript_source", "summary", "files_changed", "tags", "verification",
)
ACTIVITIES = {"research", "implementation", "debugging", "refactoring", "documentation", "testing", "planning", "review", "configuration"}
STATUSES = {"completed", "partial", "needs-review", "blocked", "abandoned"}
TAG_NAMESPACES = {"project", "task", "activity", "component", "file", "topic", "decision", "status", "source", "person"}
TAG_VALUE = re.compile(r"^[A-Za-z0-9._/@+-]+(?: [A-Za-z0-9._/@+-]+)*$")


def project_paths(project: Path) -> dict[str, Path]:
    return {
        "sessions": project / "raw" / "sessions",
        "index": project / "wiki" / "session-index.jsonl",
        "log": project / "wiki" / "log.md",
        "handoff": project / "wiki" / "session-handoff.md",
    }


def parse_time(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("timestamps must be ISO 8601 values with an offset") from exc


def validate_session(data: dict) -> None:
    missing = [field for field in REQUIRED_FIELDS if field not in data or data[field] in (None, "")]
    if missing:
        raise ValueError("missing required fields: " + ", ".join(missing))
    started, ended = parse_time(data["started_at"]), parse_time(data["ended_at"])
    if started.tzinfo is None or ended.tzinfo is None:
        raise ValueError("timestamps must include a timezone offset")
    if ended < started:
        raise ValueError("ended_at must not precede started_at")
    if data["status"] not in STATUSES:
        raise ValueError("status must be one of: " + ", ".join(sorted(STATUSES)))
    if not isinstance(data["files_changed"], list) or not all(isinstance(row, dict) and row.get("path") and row.get("action") for row in data["files_changed"]):
        raise ValueError("files_changed must be a list of {path, action} objects")
    if not isinstance(data["tags"], list) or not data["tags"]:
        raise ValueError("tags must be a non-empty list")
    for tag in data["tags"]:
        validate_tag(tag)
    if not any(tag.startswith("activity:") for tag in data["tags"]):
        raise ValueError("tags must include one activity:<value> tag")
    if not isinstance(data["verification"], list):
        raise ValueError("verification must be a list")


def validate_tag(tag: str) -> None:
    if not isinstance(tag, str) or ":" not in tag:
        raise ValueError("each tag must use namespace:value")
    namespace, value = tag.split(":", 1)
    if namespace not in TAG_NAMESPACES or not value or not TAG_VALUE.fullmatch(value):
        raise ValueError(f"invalid tag: {tag}")
    if namespace == "activity" and value not in ACTIVITIES:
        raise ValueError("activity must be one of: " + ", ".join(sorted(ACTIVITIES)))
    if namespace == "status" and value not in STATUSES:
        raise ValueError("status tag must be one of: " + ", ".join(sorted(STATUSES)))


def slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return result[:48] or "session"


def session_id(data: dict) -> str:
    return "session-" + data["ended_at"].replace(":", "-").replace("+", "plus-") + "-" + slug(data["task"])


def render_session(data: dict, identifier: str) -> str:
    metadata = {"id": identifier, **data}
    lines = ["---"]
    lines.extend(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in metadata.items())
    lines.extend(["---", "", "# Session", "", "## Outcome", "", data["summary"], "", "## Changed Files", ""])
    lines.extend(f"- `{row['path']}` — {row['action']}" for row in data["files_changed"])
    lines.extend(["", "## Tags", ""])
    lines.extend(f"- `{tag}`" for tag in data["tags"])
    lines.extend(["", "## Verification", ""])
    lines.extend(f"- `{row.get('command', 'manual')}` — {row.get('result', 'not recorded')}" for row in data["verification"])
    return "\n".join(lines) + "\n"


def read_frontmatter(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        raise ValueError(f"{path} has no metadata front matter")
    close = content.find("\n---\n", 4)
    if close < 0:
        raise ValueError(f"{path} has unclosed metadata front matter")
    parsed = {}
    for line in content[4:close].splitlines():
        key, value = line.split(": ", 1)
        parsed[key] = json.loads(value)
    return parsed


def index_record(data: dict, identifier: str, relative_path: str) -> dict:
    return {
        "id": identifier,
        "started_at": data["started_at"],
        "ended_at": data["ended_at"],
        "timezone": data["timezone"],
        "task": data["task"],
        "status": data["status"],
        "summary": data["summary"],
        "tags": data["tags"],
        "files": [row["path"] for row in data["files_changed"]],
        "source": relative_path,
    }
