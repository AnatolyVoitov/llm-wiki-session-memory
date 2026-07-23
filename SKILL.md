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
6. `wiki/content-index.jsonl`: derived index for knowledge-card recall; never edit it manually.

## Knowledge cards

Every maintained knowledge page represents one searchable item. Add JSON-compatible YAML front matter matching [the content-card schema](references/content-card-schema.md): stable `id`, `type`, title, description, typed tags, source, dates, relations, aliases, and status.

Use `type` for the kind of material: `skill`, `article`, `repository`, `tool`, `project`, `entity`, `concept`, `source`, `synthesis`, `question`, `image`, `diagram`, or `document`. Use namespaced tags for facets such as `domain:web-design`, `capability:ui-design`, `workflow:implementation`, `topic:context-engineering`, and `tool:figma`.

Relations create the local knowledge graph. Use stable card IDs with relationship types such as `references`, `contains`, `describes`, `supports`, `complements`, `depends-on`, `derived-from`, `replaces`, and `applies-to`. `added_at` means when the item entered this Wiki; it supports questions about materials added last week. Keep original publication time separately as `published_at` when known.

`complements` and legacy `related-to` are symmetric and must be explicitly stored on both cards; strict lint reports missing reverse links but never creates them. All other current relation types are directed. `replaces` reports the absent future `replaced-by` inverse as a diagnostic until that vocabulary entry is added.

New and curated cards use `schema_version: 2`. Existing v1 cards remain readable until they are upgraded with `migrate_content_cards.py --upgrade-schema`.

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

For knowledge cards, rebuild and query the separate content index:

```text
python3 .agents/skills/llm-wiki-session-memory/scripts/rebuild_content_index.py .
python3 .agents/skills/llm-wiki-session-memory/scripts/lint_content.py .
python3 .agents/skills/llm-wiki-session-memory/scripts/query_content.py . --type skill --tag domain:web-design
python3 .agents/skills/llm-wiki-session-memory/scripts/query_content.py . --text "context engineering" --added-since 2026-07-16
python3 .agents/skills/llm-wiki-session-memory/scripts/query_content.py . --related-to projects.example
python3 .agents/skills/llm-wiki-session-memory/scripts/query_content.py . --complements skill.example
```

Audit and curate card quality without broad rewrites:

```text
python3 .agents/skills/llm-wiki-session-memory/scripts/audit_content.py . --format markdown
python3 .agents/skills/llm-wiki-session-memory/scripts/propose_content_curation.py . --output wiki/curation/proposal.json
python3 .agents/skills/llm-wiki-session-memory/scripts/apply_content_curation.py . wiki/curation/proposal.json --approve skill.design-taste-frontend
python3 .agents/skills/llm-wiki-session-memory/scripts/lint_content.py . --strict
```

`propose_content_curation.py` never changes cards. Review and edit its JSON proposal before applying. `apply_content_curation.py` changes only IDs passed through `--approve`.

For a pre-existing Wiki without card metadata, run `migrate_content_cards.py` once before rebuilding the index. It adds baseline metadata only to pages without front matter and turns existing `[[Wiki links]]` into `related-to` relations.

## Ingest, query, lint

- **Ingest:** preserve new evidence under `raw/sources/`; summarize it, update linked Wiki pages and `wiki/index.md`, then append `wiki/log.md`.
- **Query:** search `wiki/index.md` and maintained pages first. Use session queries for questions about past work, such as “what did I do yesterday?”
- **Lint:** run `lint_memory.py` after saving a session, then run `rebuild_content_index.py` and `lint_content.py` after adding or changing knowledge cards.

## Non-negotiable rules

- Raw evidence and saved session records are immutable after creation.
- The Wiki is derived, editable knowledge; cite raw evidence in it.
- Do not overwrite user-owned files during bootstrap.
- Do not create external databases, embeddings, network services or secret files for this workflow.
