# Tagging rules

Tags are searchable `namespace:value` strings. Use a small, meaningful set; never add speculative synonyms.

| Namespace | Use | Rule |
| --- | --- | --- |
| `activity` | work performed | Exactly one; `research`, `implementation`, `debugging`, `refactoring`, `documentation`, `testing`, `planning`, `review`, or `configuration`. |
| `status` | session result | Match the session `status` when useful. |
| `task` | concrete outcome | Prefer a stable kebab-case phrase. |
| `component` | subsystem | Use a stable project term. |
| `file` | materially changed file | Add one per changed file. |
| `topic` | durable subject | Add only when it aids later recall. |
| `project`, `decision`, `source`, `person` | optional context | Use only when relevant. |

Examples: `activity:debugging`, `component:runtime`, `file:src/runtime/validator.py`, `task:artifact-validation`.
