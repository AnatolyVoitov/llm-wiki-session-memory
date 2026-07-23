# LLM Wiki Session Memory

Add this to `AGENTS.md` when installing the skill.

## Session Memory

- Read `wiki/session-handoff.md` after `wiki/index.md` when present.
- Treat `wiki/session-handoff.md` as active continuity for the next chat.
- Treat `wiki/log.md` as compact audit, not default startup memory.
- Do not read `raw/sessions/` by default.
- Store full transcripts or faithful session summaries under `raw/sessions/` only when saving a session.
- Treat `/prompts:save-memory`, `$llm-wiki-session-memory`, `save memory`, `update wiki memory`, and `сохрани сессию` as memory-save triggers.
- Keep `raw/sources/` and `raw/sessions/` immutable after creation.
- Use `wiki/session-index.jsonl` only through the bundled scripts; do not edit it manually.
- Give every maintained knowledge page a content-card header with `id`, `type`, `tags`, `source`, `dates`, `relations`, `aliases`, and `status`.
- Use namespaced content tags such as `domain:web-design`, `capability:ui-design`, `workflow:implementation`, `topic:context-engineering`, and `tool:figma`.
- After adding or changing cards, run `rebuild_content_index.py` and `lint_content.py`; never edit `wiki/content-index.jsonl` manually.
- Use `audit_content.py` and `propose_content_curation.py` before broad cleanup. Apply only explicitly approved IDs through `apply_content_curation.py`.

When saving memory:

1. Extract only durable facts, decisions, contradictions, open tasks, changed files, checks, blockers and next actions; omit secrets and private data.
2. Add required metadata and typed tags according to `references/session-schema.md` and `references/tagging.md`.
3. Run `save_memory.py` and `lint_memory.py`.
4. Update relevant maintained Wiki pages.
