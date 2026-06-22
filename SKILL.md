---
name: llm-wiki-session-memory
description: "Session continuity extension for Karpathy-style LLM Wiki systems. Use after a base LLM Wiki skill when a project needs raw session transcripts, compact audit logs, active handoff memory, and durable wiki knowledge across AI agent chats."
---

# LLM Wiki Session Memory

This skill extends the Karpathy LLM Wiki pattern:
https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

Use it together with a base `llm-wiki` skill. The base skill owns the general pattern: immutable raw sources, maintained wiki pages, source summaries, index, log, ingest, query, and lint workflows.

This extension owns session continuity. It prevents new agent chats from rereading full transcripts or long logs by separating storage, audit, active memory, and durable knowledge.

## Use When

Use this skill when a project:

- spans multiple AI agent chats;
- needs the next chat to resume from the previous state;
- saves full chat transcripts or session summaries;
- has a growing `wiki/log.md` that should not be read fully on startup;
- needs token-efficient handoffs between agents or sessions.

Do not use this skill for one-off tasks that do not need cross-session continuity.

## Required Base

Install or initialize the base LLM Wiki pattern first.

Expected base structure:

```text
raw/
wiki/
wiki/index.md
wiki/log.md
wiki/sources/
wiki/concepts/
wiki/syntheses/
AGENTS.md
```

Then add this extension:

```text
raw/sessions/
wiki/session-handoff.md
```

## Four Memory Layers

1. `raw/sessions/`: immutable full transcripts or faithful session summaries. This is storage, not startup context.
2. `wiki/log.md`: compact append-only audit log. It records what happened and where details live.
3. `wiki/session-handoff.md`: active working memory. Read on startup, rewritten on shutdown.
4. Durable wiki pages: `wiki/projects/`, `wiki/concepts/`, `wiki/syntheses/`, `wiki/questions/`, and other maintained pages.

## Startup Workflow

At the start of a new chat:

1. Read `AGENTS.md`.
2. Read `wiki/index.md`.
3. Read `wiki/session-handoff.md` if it exists.
4. Open only relevant wiki pages named by the handoff or index.
5. Do not read all of `wiki/log.md` by default.
6. Do not read `raw/sessions/` by default.

If `wiki/session-handoff.md` is missing, create it from the latest relevant project page or the last few compact entries in `wiki/log.md`. Do not reconstruct the whole project from raw transcripts unless necessary.

## Shutdown Workflow

At the end of a meaningful chat:

1. Save the full transcript to `raw/sessions/<date>-<slug>.md` if transcript export is available.
2. If full export is not available, save a faithful session summary with changed files, decisions, commands, checks, blockers, and next actions.
3. Extract durable facts, decisions, contradictions, and open tasks.
4. Update relevant maintained wiki pages.
5. Rewrite `wiki/session-handoff.md` with current active context.
6. Append one compact entry to `wiki/log.md` linking to the raw session and updated wiki pages.

## Handoff Rules

`wiki/session-handoff.md` should be short enough to read on every startup.

Target size: 100-250 lines. If it grows larger, move durable details into project, concept, synthesis, or question pages and keep only links plus active state.

Recommended structure:

```markdown
# Session Handoff

## Active Context

- Current project or topic:
- Current objective:
- Current branch/worktree, if relevant:

## Current Decisions

- Decision:
- Decision:

## Open Tasks

- Task:
- Task:

## Blockers

- Blocker:

## Next Action

- Next:

## Relevant Pages

- `wiki/projects/...`
- `wiki/syntheses/...`
```

## Log Rules

`wiki/log.md` is audit, not memory. Keep entries compact.

Recommended entry:

```markdown
## [YYYY-MM-DD] session | <short topic>

- Raw: `raw/sessions/YYYY-MM-DD-topic.md`
- Updated: `wiki/projects/...`, `wiki/session-handoff.md`
- Decisions: one-line summary
- Next: one-line next action
```

## Compression And Extraction Rules

- Raw transcripts remain source of truth. Do not replace them with compressed versions unless the user explicitly wants that.
- Headroom or another compressor may be used for model ingestion, tool output, logs, and derived summaries.
- Extract only durable value into maintained wiki pages: decisions, current state, reusable facts, contradictions, open tasks, and verification results.
- Do not dump the whole chat into maintained wiki pages.
- Use concise formatting for handoffs, logs, commits, and status updates.

## Relationship To Other Skills

- Base `llm-wiki`: owns the general raw/wiki/schema methodology.
- This skill: owns session continuity and handoff discipline.
- Karpathy-style engineering rules: guide extraction quality and prevent over-capturing noise.
- Caveman-style compression: useful for compact handoffs, logs, reviews, and status updates.
- Headroom: useful for large transcripts, tool outputs, logs, RAG chunks, and long search results.

## Success Criteria

A project is using this skill correctly when:

- a new chat can resume by reading `wiki/index.md` and `wiki/session-handoff.md`;
- `wiki/log.md` remains compact and audit-oriented;
- `raw/sessions/` stores recoverable detail without becoming default context;
- durable decisions live in maintained wiki pages;
- startup context stays small as the project grows.
