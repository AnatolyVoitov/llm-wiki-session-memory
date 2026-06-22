---
description: "Save durable session knowledge into the project wiki memory"
---

# /save-memory

Save this session into project memory.

Follow the local memory workflow:

1. Read `AGENTS.md`.
2. Read `wiki/index.md`.
3. Read `wiki/session-handoff.md` if present.
4. Read `PROGRESS.md` and `PLAN.md` if present.
5. Extract only durable knowledge from the current chat:
   - new sources
   - decisions
   - architecture or workflow changes
   - current status
   - next steps
   - reusable explanations
   - changed files
   - commands and verification results
6. Ignore raw chat, temporary reasoning, secrets, credentials, and private data.
7. Save a full transcript or faithful session summary under `raw/sessions/` when available.
8. Update the smallest relevant maintained files:
   - `wiki/session-handoff.md` for active continuity
   - `PROGRESS.md` for status and next step
   - `PLAN.md` for plan changes
   - `AGENTS.md` for working rules
   - `wiki/sources/` for source summaries
   - `wiki/concepts/` for reusable concepts
   - `wiki/entities/` for entities
   - `wiki/syntheses/` for integrated understanding
   - `wiki/dev/decisions.md` or `wiki/decisions.md` for durable decisions
9. Update `wiki/index.md` if pages were added.
10. Append one compact entry to `wiki/log.md`.
11. Run available project self-checks.
12. Report changed files and what was intentionally ignored.

