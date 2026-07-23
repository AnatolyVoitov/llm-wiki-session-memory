# Card Taxonomy And Quality Design

## Goal

Make every knowledge card consistently classifiable and auditable before expanding search and recommendations. The system remains local, dependency-free, Markdown-first, and compatible with existing cards.

## Scope

This phase adds:

- `schema_version: 2` to content-card metadata;
- controlled definitions for content types, tag namespaces, relation types, and statuses;
- tag aliases for query normalization without mutating canonical tags;
- a content-quality audit that reports actionable findings;
- a curation workflow that produces proposed metadata changes without overwriting human-edited cards.

This phase does not add multi-tag search, media cards, recommendation scoring, embeddings, or external services.

## Card Contract

Every card uses these fields:

```yaml
schema_version: 2
id: "skill.design-taste-frontend"
type: "skill"
title: "Design Taste Frontend"
description: "Guidance for distinctive, high-quality web interfaces."
tags: ["domain:web-design", "capability:ui-design", "workflow:implementation", "tool:figma"]
source: {"repository": "https://github.com/example/repo"}
dates: {"added_at": "2026-07-23T14:30:00+03:00", "updated_at": "2026-07-23T14:30:00+03:00"}
relations: [{"type": "complements", "target": "skill.frontend-design"}]
aliases: ["website design", "UI design"]
status: "active"
```

Canonical tags remain namespaced ASCII strings. Aliases are query-time vocabulary and never replace canonical tags.

## Controlled Vocabulary

Content types: `skill`, `article`, `repository`, `tool`, `project`, `concept`, `source`, `synthesis`, `question`, `image`, `diagram`, `document`.

Core tag namespaces: `domain`, `capability`, `workflow`, `topic`, `tool`, `platform`, `language`, `project`, `component`, `source`, `person`.

Relation types: `related-to`, `complements`, `depends-on`, `derived-from`, `applies-to`, `replaces`.

## Audit

`audit_content.py` reads cards and reports JSON and Markdown findings without changing files. It flags:

- missing or unsupported schema version;
- generic migration descriptions such as `Maintained skill card`;
- generated-only tags such as a single `topic:<slug>`;
- missing meaningful source URL/raw path for externally sourced content;
- generic `related-to` relations that should be reviewed;
- duplicate titles, aliases, and tags;
- stale `updated_at` values after manual metadata changes.

Severity is `error`, `warning`, or `suggestion`. Existing valid v1 cards remain readable; the lint accepts v1 during migration but new and curated cards emit v2.

## Curation Workflow

`propose_content_curation.py` creates a review file under `wiki/curation/` with candidate tags, descriptions, aliases, and relation refinements. It never changes cards directly.

The agent or user reviews the proposal. A separate apply command accepts only explicitly approved card IDs and writes metadata updates, refreshes `dates.updated_at`, rebuilds the index, and runs lint.

## Compatibility And Migration

`migrate_content_cards.py --upgrade-schema` adds `schema_version: 2` to existing cards without replacing their body, IDs, tags, dates, or relations. It is idempotent.

The current `content-index.jsonl` includes `schema_version`, so derived-index drift detects incomplete migrations.

## Tests

- validation rejects unsupported v2 types, namespaces, and relation types;
- v1 cards remain indexable during migration;
- schema upgrade is idempotent and preserves card bodies;
- audit catches weak generated metadata and does not modify files;
- curated application changes only approved card IDs and updates the derived index;
- regression test covers aliases such as `website design` and `web design`.

## Acceptance Criteria

- Every current card is either upgraded to v2 or explicitly reported as legacy.
- The audit produces only actionable findings and makes no writes.
- Human-approved curation is the only path that mutates existing card metadata.
- Existing `rebuild_content_index.py`, `lint_content.py`, and session-memory workflows continue to pass.
