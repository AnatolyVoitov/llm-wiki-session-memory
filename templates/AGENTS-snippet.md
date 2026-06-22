# LLM Wiki Session Memory Snippet

Add this to `AGENTS.md` when installing the extension.

## Session Memory

- Read `wiki/session-handoff.md` after `wiki/index.md` when present.
- Treat `wiki/session-handoff.md` as active continuity for the next chat.
- Treat `wiki/log.md` as compact audit, not default startup memory.
- Do not read `raw/sessions/` by default.
- Store full transcripts or faithful session summaries under `raw/sessions/` only when saving a session.
- Treat `/save-memory`, `save memory`, `update wiki memory`, and `сохрани сессию` as end-of-chat memory save commands.

When saving memory:

1. Extract durable facts, decisions, contradictions, open tasks, changed files, commands, checks, blockers, and next actions.
2. Update relevant maintained wiki pages.
3. Rewrite `wiki/session-handoff.md`.
4. Append one compact entry to `wiki/log.md`.

