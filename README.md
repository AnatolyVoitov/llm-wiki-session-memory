# LLM Wiki Session Memory

Token-efficient session handoffs for Karpathy-style LLM Wiki agents.

This repository contains a skill extension for the Karpathy LLM Wiki pattern:
https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

It does not replace a base LLM Wiki skill. It extends one with a practical session-memory layer for projects that span many AI agent chats.

## What It Adds

- `raw/sessions/` for full transcripts or faithful session summaries.
- `wiki/session-handoff.md` as the small active memory file read at the start of each new chat.
- Compact `wiki/log.md` entries for audit rather than full startup context.
- A shutdown workflow that extracts durable decisions into maintained wiki pages.

## Why

Many LLM Wiki projects save full chat transcripts and append logs after each session. That preserves history, but if every new chat reads all previous logs or transcripts, context grows quickly and the agent wastes tokens on stale detail.

This skill separates:

- storage: full raw sessions;
- audit: compact chronological log;
- active memory: current handoff;
- durable knowledge: maintained wiki pages.

The result is a project memory system that remains recoverable without making every new agent pay for the whole past.

## Install Order

1. Install or initialize a base Karpathy-style LLM Wiki skill.
2. Add this skill as the session continuity extension.

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

This extension adds:

```text
raw/sessions/
wiki/session-handoff.md
```

## Skill

The skill is defined in [`SKILL.md`](SKILL.md).
