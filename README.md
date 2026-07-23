# LLM Wiki Session Memory

A self-contained implementation of [Andrej Karpathy's LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f), with structured session continuity for Codex and similar agents.

It keeps evidence immutable, builds an agent-maintained Wiki, and makes past work recoverable by date, task, tag, status, or changed file — without a database or external service.

## Includes

- safe bootstrap for raw sources, Wiki pages, active handoff and local indexes;
- structured session metadata and controlled tags;
- metadata-rich knowledge cards with typed tags, dates, sources and graph relations;
- schema-v2 validation, a read-only quality audit, and explicit-ID content curation;
- `save_memory.py`, `query_memory.py`, `lint_memory.py`, `rebuild_content_index.py`, `query_content.py`, and `lint_content.py`;
- templates for `AGENTS.md`, handoff, taxonomy and Codex `/prompts:save-memory`.

## Quick start

Install the skill project-locally, then run:

```bash
python3 .agents/skills/llm-wiki-session-memory/scripts/bootstrap.py .
python3 .agents/skills/llm-wiki-session-memory/scripts/install_codex_prompt.py --codex-home ~/.codex
```

See [SKILL.md](SKILL.md) for operations and [references/session-schema.md](references/session-schema.md) for the JSON input accepted by `save_memory.py`.
