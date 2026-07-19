---
name: llm-wiki-session-memory
description: Use when a project needs a persistent LLM-maintained knowledge wiki, session continuity across agent chats, durable source ingest, or recall of past work by date, task, tag, file, or status.
---

# LLM Wiki Session Memory

Implement Andrej Karpathy's [LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f): immutable raw sources, a maintained Wiki, and `AGENTS.md` as the operating schema. This skill adds structured session memory and dependency-free local tools.

## Install

Copy this skill into `.agents/skills/llm-wiki-session-memory/`, then run:

```text
python3 .agents/skills/llm-wiki-session-memory/scripts/bootstrap.py .
```

For Codex, run `python3 .agents/skills/llm-wiki-session-memory/scripts/install_codex_prompt.py --codex-home ~/.codex`, restart Codex, then use `/prompts:save-memory`. Custom prompts are user-local; the project workflow remains available through `$llm-wiki-session-memory` and natural-language triggers.

## Memory layers

1. `raw/sources/`: immutable evidence.
2. `raw/sessions/`: immutable session summaries or transcript exports.
3. `wiki/`: maintained knowledge, sources, concepts, syntheses, index and log.
4. `wiki/session-handoff.md`: short active context for the next chat.
5. `wiki/session-index.jsonl`: derived index for deterministic recall; never edit it manually.

## Startup

1. Read `AGENTS.md`, `wiki/index.md`, then `wiki/session-handoff.md`.
2. Read only linked relevant Wiki pages.
3. Do not read every log entry, raw session, or raw source by default.

## Save a session

At the end of meaningful work, extract facts and create a JSON payload matching [the schema](references/session-schema.md). Do not put secrets, credentials, private data, or chain-of-thought in it. Then run:

```text
python3 .agents/skills/llm-wiki-session-memory/scripts/save_memory.py . /path/to/session.json
python3 .agents/skills/llm-wiki-session-memory/scripts/lint_memory.py .
```

The tool writes the raw session record, append-only index and log, and rewrites the active handoff. Update durable Wiki pages only for reusable knowledge, decisions, contradictions, and open work.

## Tags and recall

Follow [tagging rules](references/tagging.md). Tags have the form `namespace:value`. Every session needs exactly one valid `activity:` tag and one `status:` field; use `file:` for each materially changed file.

```text
python3 .agents/skills/llm-wiki-session-memory/scripts/query_memory.py . --yesterday --timezone Asia/Jerusalem
python3 .agents/skills/llm-wiki-session-memory/scripts/query_memory.py . --file src/runtime.py
python3 .agents/skills/llm-wiki-session-memory/scripts/query_memory.py . --tag component:runtime --status blocked
```

## Ingest, query, lint

- **Ingest:** preserve new evidence under `raw/sources/`; summarize it, update linked Wiki pages and `wiki/index.md`, then append `wiki/log.md`.
- **Query:** search `wiki/index.md` and maintained pages first. Use session queries for questions about past work, such as “what did I do yesterday?”
- **Lint:** run `lint_memory.py` after saving a session and periodically inspect Wiki links, stale claims, contradictions and orphan pages.

## Non-negotiable rules

- Raw evidence and saved session records are immutable after creation.
- The Wiki is derived, editable knowledge; cite raw evidence in it.
- Do not overwrite user-owned files during bootstrap.
- Do not create external databases, embeddings, network services or secret files for this workflow.
