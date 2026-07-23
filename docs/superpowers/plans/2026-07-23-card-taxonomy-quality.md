# Card Taxonomy Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade knowledge cards to an auditable v2 taxonomy and add a review-first curation workflow without mutating unapproved content.

**Architecture:** `scripts/wiki_memory.py` remains the single validation and index-model module. Thin CLI scripts audit cards, write review proposals, and apply only explicitly named card IDs. `wiki/tag-taxonomy.yml` supplies the controlled vocabulary and aliases; the derived JSONL index remains rebuilt rather than edited directly.

**Tech Stack:** Python 3 standard library, JSON-compatible YAML front matter, JSONL, `unittest`.

---

## File Structure

- Modify: `scripts/wiki_memory.py` — v1/v2 parsing, controlled vocabulary, metadata validation, index records, and reusable metadata renderer.
- Modify: `scripts/migrate_content_cards.py` — idempotent `--upgrade-schema` migration.
- Modify: `scripts/rebuild_content_index.py` — emit v2 index records.
- Modify: `scripts/lint_content.py` — validate schema, relation types, duplicate metadata, and index drift.
- Create: `scripts/audit_content.py` — read-only quality findings in JSON or Markdown.
- Create: `scripts/propose_content_curation.py` — write review proposals only.
- Create: `scripts/apply_content_curation.py` — apply a reviewed proposal only for explicit card IDs.
- Modify: `templates/wiki/tag-taxonomy.yml` — v2 vocabulary and aliases.
- Modify: `templates/wiki/content-index.jsonl` — unchanged empty derived-index placeholder.
- Modify: `references/content-card-schema.md` — v2 contract and migration guidance.
- Modify: `SKILL.md`, `README.md`, `templates/AGENTS.md`, `templates/AGENTS-snippet.md` — commands and review-first workflow.
- Modify: `tests/test_memory_cli.py` — behaviour-first coverage for every CLI and migration path.

### Task 1: Define The V2 Contract

**Files:**
- Modify: `tests/test_memory_cli.py`
- Modify: `scripts/wiki_memory.py`
- Modify: `templates/wiki/tag-taxonomy.yml`
- Modify: `references/content-card-schema.md`

- [ ] **Step 1: Write failing validation tests**

```python
def test_v2_card_rejects_unknown_relation_type(self):
    card = valid_card(schema_version=2, relations=[{"type": "guesses-about", "target": "skill.other"}])
    with self.assertRaisesRegex(ValueError, "relation type"):
        validate_content(card)

def test_v1_card_remains_indexable_during_migration(self):
    write_card_without_schema_version(project)
    run("rebuild_content_index.py", project)
    self.assertEqual(read_index(project)[0]["schema_version"], 1)
```

- [ ] **Step 2: Run the focused tests**

Run: `python3 tests/test_memory_cli.py`  
Expected: failure because `schema_version` and controlled relation validation do not exist.

- [ ] **Step 3: Implement minimal schema helpers**

```python
SCHEMA_VERSION = 2
SUPPORTED_SCHEMA_VERSIONS = {1, 2}
RELATION_TYPES = {"related-to", "complements", "depends-on", "derived-from", "applies-to", "replaces"}

def content_schema_version(data: dict) -> int:
    return data.get("schema_version", 1)
```

Validate v2 tags and relations against the parsed taxonomy; retain v1 compatibility. Add `schema_version` to `content_record`.

- [ ] **Step 4: Run tests and lint**

Run: `python3 tests/test_memory_cli.py && git diff --check`  
Expected: all tests pass and no whitespace errors.

- [ ] **Step 5: Commit**

```bash
git add scripts/wiki_memory.py templates/wiki/tag-taxonomy.yml references/content-card-schema.md tests/test_memory_cli.py
git commit -m "feat: define card taxonomy v2"
```

### Task 2: Upgrade Existing Cards Safely

**Files:**
- Modify: `tests/test_memory_cli.py`
- Modify: `scripts/migrate_content_cards.py`
- Modify: `scripts/rebuild_content_index.py`

- [ ] **Step 1: Write failing migration tests**

```python
def test_schema_upgrade_adds_v2_without_rewriting_card_body(self):
    original_body = "# Design\n\nExisting content.\n"
    write_v1_card(project, original_body)
    run("migrate_content_cards.py", project, "--upgrade-schema")
    self.assertIn('schema_version: 2', read_card(project))
    self.assertTrue(read_card(project).endswith(original_body))

def test_schema_upgrade_is_idempotent(self):
    run("migrate_content_cards.py", project, "--upgrade-schema")
    first = read_card(project)
    run("migrate_content_cards.py", project, "--upgrade-schema")
    self.assertEqual(read_card(project), first)
```

- [ ] **Step 2: Run tests to confirm RED**

Run: `python3 tests/test_memory_cli.py`  
Expected: failure because `--upgrade-schema` is unsupported.

- [ ] **Step 3: Implement only the upgrade path**

Add `--upgrade-schema`; preserve every existing field and Markdown body, insert `schema_version: 2`, and do not infer or replace tags or relations. Rebuild output gains the version through `content_record`.

- [ ] **Step 4: Verify GREEN**

Run: `python3 tests/test_memory_cli.py && git diff --check`  
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/migrate_content_cards.py scripts/rebuild_content_index.py tests/test_memory_cli.py
git commit -m "feat: add safe card schema upgrade"
```

### Task 3: Add A Read-Only Quality Audit

**Files:**
- Modify: `tests/test_memory_cli.py`
- Create: `scripts/audit_content.py`
- Modify: `scripts/lint_content.py`

- [ ] **Step 1: Write failing audit tests**

```python
def test_audit_reports_generic_description_without_mutating_card(self):
    write_v2_card(project, description="Maintained skill card: Design.", tags=["topic:design"])
    before = read_card(project)
    result = run("audit_content.py", project, "--format", "json")
    findings = json.loads(result.stdout)
    self.assertIn("generic-description", {row["code"] for row in findings})
    self.assertEqual(read_card(project), before)
```

- [ ] **Step 2: Run tests to confirm RED**

Run: `python3 tests/test_memory_cli.py`  
Expected: failure because `audit_content.py` does not exist.

- [ ] **Step 3: Implement deterministic findings**

Emit records with `severity`, `code`, `card_id`, `path`, and `message`. Detect unsupported/missing versions, generic descriptions, one generated-only tag, duplicate tags or aliases, generic `related-to`, and external source cards lacking URL or raw path. Keep audit read-only.

- [ ] **Step 4: Add optional lint escalation**

`lint_content.py --strict` fails only on audit `error` findings; default lint preserves compatibility and checks structural validity/index drift.

- [ ] **Step 5: Verify GREEN**

Run: `python3 tests/test_memory_cli.py && python3 scripts/audit_content.py /tmp/fixture --format markdown`  
Expected: tests pass; audit emits findings and leaves fixture hashes unchanged.

- [ ] **Step 6: Commit**

```bash
git add scripts/audit_content.py scripts/lint_content.py tests/test_memory_cli.py
git commit -m "feat: audit knowledge card quality"
```

### Task 4: Propose And Apply Reviewed Curation

**Files:**
- Modify: `tests/test_memory_cli.py`
- Create: `scripts/propose_content_curation.py`
- Create: `scripts/apply_content_curation.py`
- Modify: `scripts/wiki_memory.py`

- [ ] **Step 1: Write failing proposal and apply tests**

```python
def test_curation_proposal_does_not_modify_cards(self):
    write_v2_card(project, tags=["topic:design"], description="Maintained skill card: Design.")
    before = read_card(project)
    proposal = run("propose_content_curation.py", project, "--output", project / "wiki/curation/proposal.json")
    self.assertTrue((project / "wiki/curation/proposal.json").exists())
    self.assertEqual(read_card(project), before)

def test_apply_curation_changes_only_approved_ids(self):
    write_two_v2_cards(project)
    write_proposal(project, updates=[{"id": "skill.design", "tags": ["domain:web-design"]}])
    run("apply_content_curation.py", project, proposal_path, "--approve", "skill.design")
    self.assertIn("domain:web-design", read_card("skill.design"))
    self.assertNotIn("domain:web-design", read_card("skill.other"))
```

- [ ] **Step 2: Run tests to confirm RED**

Run: `python3 tests/test_memory_cli.py`  
Expected: failure because proposal and apply CLIs do not exist.

- [ ] **Step 3: Implement proposal format**

The proposal is JSON with `schema_version`, `generated_at`, `findings`, and `updates`. Generate deterministic candidates only from audit findings: replace generic descriptions with a review placeholder, add aliases from taxonomy aliases, and mark relation review. Do not guess domain tags from prose.

- [ ] **Step 4: Implement explicit apply**

Require one or more `--approve <card-id>` flags. Reject proposals without matching IDs, validate the resulting metadata, update `dates.updated_at`, rebuild `content-index.jsonl`, and run structural lint. Leave all unapproved cards byte-identical.

- [ ] **Step 5: Verify GREEN**

Run: `python3 tests/test_memory_cli.py && git diff --check`  
Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add scripts/propose_content_curation.py scripts/apply_content_curation.py scripts/wiki_memory.py tests/test_memory_cli.py
git commit -m "feat: add reviewed content curation"
```

### Task 5: Document And Apply The Phase To The Active Vault

**Files:**
- Modify: `SKILL.md`
- Modify: `README.md`
- Modify: `templates/AGENTS.md`
- Modify: `templates/AGENTS-snippet.md`
- Modify: `references/content-card-schema.md`
- Modify: `docs/superpowers/specs/2026-07-23-card-taxonomy-quality-design.md`
- Modify: `/Users/anatoly/My Database/AGENTS.md`
- Modify: `/Users/anatoly/My Database/wiki/index.md`
- Modify: `/Users/anatoly/My Database/wiki/log.md`

- [ ] **Step 1: Write documentation assertions into tests**

```python
def test_bootstrap_includes_v2_taxonomy_and_curation_directory(self):
    run("bootstrap.py", project)
    taxonomy = (project / "wiki/tag-taxonomy.yml").read_text(encoding="utf-8")
    self.assertIn("schema_version: 2", taxonomy)
    self.assertTrue((project / "wiki/curation").exists())
```

- [ ] **Step 2: Run tests to confirm RED**

Run: `python3 tests/test_memory_cli.py`  
Expected: failure because bootstrap does not create the curation directory or v2 taxonomy.

- [ ] **Step 3: Implement docs and bootstrap changes**

Document `--upgrade-schema`, audit, proposal generation, approval-only apply, and strict lint. Add `wiki/curation/` to bootstrap and v2 taxonomy template.

- [ ] **Step 4: Apply to active vault without automatic curation**

```bash
python3 .agents/skills/llm-wiki-session-memory/scripts/migrate_content_cards.py . --upgrade-schema
python3 .agents/skills/llm-wiki-session-memory/scripts/rebuild_content_index.py .
python3 .agents/skills/llm-wiki-session-memory/scripts/lint_content.py .
python3 .agents/skills/llm-wiki-session-memory/scripts/audit_content.py . --format markdown
```

Keep the generated proposal under review. Do not run `apply_content_curation.py` against the active vault until explicit card IDs are approved.

- [ ] **Step 5: Verify and commit**

Run: `python3 tests/test_memory_cli.py && git diff --check`  
Expected: all tests pass.

```bash
git add SKILL.md README.md templates references scripts tests docs
git commit -m "docs: document card quality workflow"
git push origin main
```

## Final Verification

- [ ] Run `python3 tests/test_memory_cli.py` from the repository.
- [ ] Run `lint_memory.py`, `rebuild_content_index.py`, and `lint_content.py` in `/Users/anatoly/My Database`.
- [ ] Confirm an audit of the active vault is read-only by comparing card hashes before and after.
- [ ] Confirm only reviewed and explicitly approved card IDs can change through `apply_content_curation.py`.
- [ ] Record the completed phase in the active vault `wiki/log.md` and save the session handoff.
