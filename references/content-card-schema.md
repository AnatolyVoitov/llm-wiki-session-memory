# Knowledge-card schema

Every maintained content page uses JSON-compatible YAML front matter. This keeps the Markdown readable while allowing the dependency-free scripts to parse it safely.

```yaml
---
schema_version: 2
id: "skill.design-taste-frontend"
type: "skill"
title: "Design Taste Frontend"
description: "Guidance for distinctive, high-quality web interfaces."
tags: ["domain:web-design", "capability:ui-design", "workflow:implementation", "tool:figma"]
source: {"repository": "https://github.com/example/repo", "raw_path": "raw/sources/design-taste.md"}
dates: {"added_at": "2026-07-23T14:30:00+03:00", "updated_at": "2026-07-23T14:30:00+03:00", "published_at": "2026-07-19"}
relations: [{"type": "complements", "target": "skill.frontend-design"}]
aliases: ["website design", "UI design"]
status: "active"
---
```

Required fields are `id`, `type`, `title`, `description`, `tags`, `source`, `dates`, `relations`, `aliases`, and `status`.

Cards without `schema_version` are treated as legacy v1 cards during migration. New and curated cards must use `schema_version: 2`.

`type` must be one of: `skill`, `article`, `repository`, `tool`, `project`, `concept`, `source`, `synthesis`, `question`, `image`, `diagram`, `document`. Version 2 relation types are `related-to`, `complements`, `depends-on`, `derived-from`, `applies-to`, and `replaces`.

`status` must be one of: `active`, `draft`, `archived`, `superseded`.

`source` needs at least one of `url`, `raw_path`, `repository`, or `wiki_path` for internally authored pages. `dates` needs `added_at` and `updated_at` with ISO 8601 timezone offsets. `published_at` and `last_verified_at` are optional.

Use stable namespaced tags. The core namespaces are `domain`, `capability`, `workflow`, `topic`, `tool`, `platform`, `language`, `project`, `component`, `source`, and `person`.
