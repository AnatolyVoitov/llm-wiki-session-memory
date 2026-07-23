# Session record schema

`save_memory.py` accepts one UTF-8 JSON object. It renders a Markdown record with YAML-compatible front matter under `raw/sessions/`.

Required fields:

```json
{
  "started_at": "2026-07-19T09:00:00+03:00",
  "ended_at": "2026-07-19T10:00:00+03:00",
  "timezone": "Asia/Jerusalem",
  "agent": "codex",
  "task": "Add session search",
  "status": "completed",
  "transcript_source": "faithful-summary",
  "summary": "One concise durable outcome.",
  "files_changed": [{"path": "scripts/query_memory.py", "action": "created"}],
  "tags": ["activity:implementation", "task:session-search", "file:scripts/query_memory.py"],
  "verification": [{"command": "python3 -m unittest", "result": "passed"}]
}
```

`status` must be `completed`, `partial`, `needs-review`, `blocked`, or `abandoned`. Timestamps require ISO 8601 offsets. `files_changed` requires a path and action per item. Never include secrets, credentials, personal data, or private chain-of-thought.

Optional lists `decisions`, `open_tasks`, `blockers`, `next_actions`, and `relevant_pages` are rendered into `wiki/session-handoff.md`. Use concise durable statements; do not include private reasoning.
