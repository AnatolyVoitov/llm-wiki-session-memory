---
description: Save a validated, tagged session into the active project's LLM Wiki
argument-hint: TASK="" TAGS=""
---

Use `$llm-wiki-session-memory` to save this session. The project is the current working directory. Use `$TASK` as the task when supplied. Treat `$TAGS` as suggested tags, validate them against the taxonomy, create a JSON payload outside the project if it is transient, run `save_memory.py`, then run `lint_memory.py`. Report the created session path, selected tags and any intentionally omitted sensitive data.
