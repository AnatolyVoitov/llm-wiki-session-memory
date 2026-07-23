# LLM Wiki Operating Rules

## Startup

1. Read `wiki/index.md`.
2. Read `wiki/session-handoff.md`.
3. Open only relevant linked Wiki pages.
4. Do not read all of `wiki/log.md`, `raw/sources/`, or `raw/sessions/` by default.

## Sources and Wiki

- `raw/sources/` and `raw/sessions/` are immutable evidence.
- `wiki/` is derived, maintained knowledge. Keep it concise, cross-linked, and grounded in raw evidence.
- Use `wiki/log.md` as compact audit, not as startup context.
- Give maintained knowledge pages content-card metadata and use `wiki/content-index.jsonl` only through the bundled scripts.
- Rebuild and lint the content index after adding or changing knowledge cards.

## Session memory

- Treat `/prompts:save-memory`, `$llm-wiki-session-memory`, `save memory`, and `сохрани сессию` as save triggers.
- Use the bundled scripts to write and query `wiki/session-index.jsonl`; never edit it manually.
- Validate metadata and tags with `lint_memory.py` after every saved session.
