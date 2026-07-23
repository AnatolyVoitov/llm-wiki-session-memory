import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run(script, *args, check=True):
    return subprocess.run(
        [PYTHON, str(ROOT / "scripts" / script), *map(str, args)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=check,
    )


class MemoryCliTests(unittest.TestCase):
    def write_card(self, project, identifier, card_type, relations):
        path = project / "wiki" / "cards" / f"{identifier.replace('.', '-')}.md"
        path.parent.mkdir(exist_ok=True)
        path.write_text(
            "---\n"
            "schema_version: 2\n"
            f'id: "{identifier}"\n'
            f'type: "{card_type}"\n'
            f'title: "{identifier}"\n'
            'description: "A test knowledge card with a specific purpose."\n'
            'tags: ["topic:testing"]\n'
            f'source: {{"wiki_path": "{path.relative_to(project).as_posix()}"}}\n'
            'dates: {"added_at": "2026-07-20T10:00:00+03:00", "updated_at": "2026-07-20T10:00:00+03:00"}\n'
            f"relations: {json.dumps(relations)}\n"
            "aliases: []\n"
            'status: "active"\n'
            "---\n\n# Card\n",
            encoding="utf-8",
        )

    def test_strict_lint_reports_duplicate_and_missing_symmetric_relations(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            self.write_card(project, "skill.first", "skill", [
                {"type": "complements", "target": "skill.second"},
                {"type": "complements", "target": "skill.second"},
            ])
            self.write_card(project, "skill.second", "skill", [])
            run("rebuild_content_index.py", project)
            result = run("lint_content.py", project, "--strict", check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duplicate-relation: duplicate relation from skill.first to skill.second", result.stderr)
            self.assertIn("missing-symmetric-relation: missing complements relation from skill.second to skill.first", result.stderr)
            self.assertEqual(result.stderr.count("missing-symmetric-relation: missing complements relation from skill.second to skill.first"), 1)

    def test_strict_lint_reports_missing_replaced_by_inverse(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            self.write_card(project, "skill.new", "skill", [{"type": "replaces", "target": "skill.old"}])
            self.write_card(project, "skill.old", "skill", [])
            run("rebuild_content_index.py", project)
            result = run("lint_content.py", project, "--strict", check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing-inverse-relation: replaces relation from skill.new to skill.old has no replaced-by inverse", result.stderr)

    def test_strict_lint_accepts_reciprocal_replacement_relations(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            self.write_card(project, "skill.new", "skill", [{"type": "replaces", "target": "skill.old"}])
            self.write_card(project, "skill.old", "skill", [{"type": "replaced-by", "target": "skill.new"}])
            run("rebuild_content_index.py", project)
            result = run("lint_content.py", project, "--strict", check=False)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_strict_lint_reports_missing_replaces_inverse(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            self.write_card(project, "skill.old", "skill", [{"type": "replaced-by", "target": "skill.new"}])
            self.write_card(project, "skill.new", "skill", [])
            run("rebuild_content_index.py", project)
            result = run("lint_content.py", project, "--strict", check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing-inverse-relation: replaced-by relation from skill.old to skill.new has no replaces inverse", result.stderr)

    def test_strict_lint_reports_isolated_important_card_but_not_entity(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            self.write_card(project, "skill.isolated", "skill", [])
            self.write_card(project, "entities.isolated", "entity", [])
            run("rebuild_content_index.py", project)
            result = run("lint_content.py", project, "--strict", check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("isolated-important-card: important card has no relations (skill.isolated)", result.stderr)
            self.assertNotIn("entities.isolated", result.stderr)

    def test_related_to_query_returns_incoming_and_outgoing_neighbors(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            self.write_card(project, "project.target", "project", [{"type": "depends-on", "target": "concept.outgoing"}])
            self.write_card(project, "concept.outgoing", "concept", [])
            self.write_card(project, "source.incoming", "source", [{"type": "supports", "target": "project.target"}])
            run("rebuild_content_index.py", project)
            result = run("query_content.py", project, "--related-to", "project.target")
            self.assertEqual(result.stdout.splitlines(), ["outgoing | depends-on | concept.outgoing", "incoming | supports | source.incoming"])

    def test_complements_query_includes_reciprocal_relation(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            self.write_card(project, "skill.requested", "skill", [])
            self.write_card(project, "skill.recommends", "skill", [{"type": "complements", "target": "skill.requested"}])
            run("rebuild_content_index.py", project)
            result = run("query_content.py", project, "--complements", "skill.requested")
            self.assertEqual(result.stdout.splitlines(), ["incoming | complements | skill.recommends"])

    def test_graph_query_rejects_unknown_card_and_malformed_relation_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            self.write_card(project, "skill.valid", "skill", [])
            run("rebuild_content_index.py", project)
            unknown = run("query_content.py", project, "--related-to", "skill.missing", check=False)
            self.assertNotEqual(unknown.returncode, 0)
            self.assertIn("unknown card id: skill.missing", unknown.stderr)
            index = project / "wiki" / "content-index.jsonl"
            record = json.loads(index.read_text(encoding="utf-8"))
            record["relations"] = [{"type": "complements"}]
            index.write_text(json.dumps(record) + "\n", encoding="utf-8")
            malformed = run("query_content.py", project, "--complements", "skill.valid", check=False)
            self.assertNotEqual(malformed.returncode, 0)
            self.assertIn("malformed relation on card skill.valid", malformed.stderr)

    def test_v2_card_accepts_entity_type_and_semantic_relation(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            card = project / "wiki" / "entities" / "design.md"
            card.parent.mkdir()
            card.write_text(
                "---\n"
                'schema_version: 2\n'
                'id: "entities.design"\n'
                'type: "entity"\n'
                'title: "Design"\n'
                'description: "Metadata for the Design skill."\n'
                'tags: ["domain:web-design"]\n'
                'source: {"wiki_path": "wiki/entities/design.md"}\n'
                'dates: {"added_at": "2026-07-20T10:00:00+03:00", "updated_at": "2026-07-20T10:00:00+03:00"}\n'
                'relations: [{"type": "describes", "target": "skill.design"}]\n'
                'aliases: []\n'
                'status: "active"\n'
                "---\n\n# Design\n",
                encoding="utf-8",
            )
            run("rebuild_content_index.py", project)

    def test_audit_allows_same_title_for_distinct_documents(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            for identifier, source in (("skill.design", "wiki/skills/design.md"), ("skill.design-copy", "wiki/skills/design-copy.md")):
                path = project / source
                path.parent.mkdir(exist_ok=True)
                path.write_text(
                    "---\n"
                    'schema_version: 2\n'
                    f'id: "{identifier}"\n'
                    'type: "skill"\n'
                    'title: "Design"\n'
                    'description: "Website design guidance."\n'
                    'tags: ["domain:web-design"]\n'
                    f'source: {{"wiki_path": "{source}"}}\n'
                    'dates: {"added_at": "2026-07-20T10:00:00+03:00", "updated_at": "2026-07-20T10:00:00+03:00"}\n'
                    'relations: []\n'
                    'aliases: []\n'
                    'status: "active"\n'
                    "---\n\n# Design\n",
                    encoding="utf-8",
                )
            findings = json.loads(run("audit_content.py", project, "--format", "json").stdout)
            self.assertNotIn("duplicate-title", {item["code"] for item in findings})

    def test_v2_card_rejects_unknown_relation_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            card = project / "wiki" / "skills" / "design.md"
            card.parent.mkdir()
            card.write_text(
                "---\n"
                'schema_version: 2\n'
                'id: "source.design"\n'
                'type: "source"\n'
                'title: "Design"\n'
                'description: "Website design guidance."\n'
                'tags: ["domain:web-design"]\n'
                'source: {"url": "https://example.com/design"}\n'
                'dates: {"added_at": "2026-07-20T10:00:00+03:00", "updated_at": "2026-07-20T10:00:00+03:00"}\n'
                'relations: [{"type": "guesses-about", "target": "skill.other"}]\n'
                'aliases: []\n'
                'status: "active"\n'
                "---\n\n# Design\n",
                encoding="utf-8",
            )
            result = run("rebuild_content_index.py", project, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("relation type", result.stderr)

    def test_v1_card_remains_indexable_with_explicit_v1_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            card = project / "wiki" / "skills" / "design.md"
            card.parent.mkdir()
            card.write_text(
                "---\n"
                'id: "source.design"\n'
                'type: "source"\n'
                'title: "Design"\n'
                'description: "Website design guidance."\n'
                'tags: ["domain:web-design"]\n'
                'source: {"url": "https://example.com/design"}\n'
                'dates: {"added_at": "2026-07-20T10:00:00+03:00", "updated_at": "2026-07-20T10:00:00+03:00"}\n'
                'relations: []\n'
                'aliases: []\n'
                'status: "active"\n'
                "---\n\n# Design\n",
                encoding="utf-8",
            )
            run("rebuild_content_index.py", project)
            record = json.loads((project / "wiki" / "content-index.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(record["schema_version"], 1)

    def test_schema_upgrade_adds_v2_without_rewriting_card_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            body = "# Design\n\nExisting content.\n"
            card = project / "wiki" / "skills" / "design.md"
            card.parent.mkdir()
            card.write_text(
                "---\n"
                'id: "source.design"\n'
                'type: "source"\n'
                'title: "Design"\n'
                'description: "Website design guidance."\n'
                'tags: ["domain:web-design"]\n'
                'source: {"url": "https://example.com/design"}\n'
                'dates: {"added_at": "2026-07-20T10:00:00+03:00", "updated_at": "2026-07-20T10:00:00+03:00"}\n'
                'relations: []\n'
                'aliases: []\n'
                'status: "active"\n'
                "---\n\n" + body,
                encoding="utf-8",
            )
            run("migrate_content_cards.py", project, "--upgrade-schema")
            content = card.read_text(encoding="utf-8")
            self.assertIn("schema_version: 2", content)
            self.assertTrue(content.endswith(body))

    def test_schema_upgrade_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            card = project / "wiki" / "skills" / "design.md"
            card.parent.mkdir()
            card.write_text(
                "---\n"
                'id: "skill.design"\n'
                'type: "skill"\n'
                'title: "Design"\n'
                'description: "Website design guidance."\n'
                'tags: ["domain:web-design"]\n'
                'source: {"url": "https://example.com/design"}\n'
                'dates: {"added_at": "2026-07-20T10:00:00+03:00", "updated_at": "2026-07-20T10:00:00+03:00"}\n'
                'relations: []\n'
                'aliases: []\n'
                'status: "active"\n'
                "---\n\n# Design\n",
                encoding="utf-8",
            )
            run("migrate_content_cards.py", project, "--upgrade-schema")
            first = card.read_text(encoding="utf-8")
            run("migrate_content_cards.py", project, "--upgrade-schema")
            self.assertEqual(card.read_text(encoding="utf-8"), first)

    def test_audit_reports_weak_metadata_without_mutating_card(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            card = project / "wiki" / "skills" / "design.md"
            card.parent.mkdir()
            card.write_text(
                "---\n"
                'schema_version: 2\n'
                'id: "source.design"\n'
                'type: "source"\n'
                'title: "Design"\n'
                'description: "Maintained source card: Design."\n'
                'tags: ["topic:design"]\n'
                'source: {"wiki_path": "wiki/sources/design.md"}\n'
                'dates: {"added_at": "2026-07-20T10:00:00+03:00", "updated_at": "2026-07-20T10:00:00+03:00"}\n'
                'relations: [{"type": "related-to", "target": "skill.other"}]\n'
                'aliases: []\n'
                'status: "active"\n'
                "---\n\n# Design\n",
                encoding="utf-8",
            )
            before = card.read_text(encoding="utf-8")
            result = run("audit_content.py", project, "--format", "json")
            findings = json.loads(result.stdout)
            codes = {finding["code"] for finding in findings}
            self.assertTrue({"generic-description", "generated-only-tags", "generic-relation", "missing-external-source"} <= codes)
            self.assertEqual(card.read_text(encoding="utf-8"), before)
            strict = run("lint_content.py", project, "--strict", check=False)
            self.assertNotEqual(strict.returncode, 0)
            self.assertIn("missing-external-source", strict.stderr)

    def test_curation_proposal_does_not_modify_cards(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            card = project / "wiki" / "skills" / "design.md"
            card.parent.mkdir()
            card.write_text(
                "---\n"
                'schema_version: 2\n'
                'id: "skill.design"\n'
                'type: "skill"\n'
                'title: "Design"\n'
                'description: "Maintained skill card: Design."\n'
                'tags: ["topic:design"]\n'
                'source: {"url": "https://example.com/design"}\n'
                'dates: {"added_at": "2026-07-20T10:00:00+03:00", "updated_at": "2026-07-20T10:00:00+03:00"}\n'
                'relations: []\n'
                'aliases: []\n'
                'status: "active"\n'
                "---\n\n# Design\n",
                encoding="utf-8",
            )
            before = card.read_text(encoding="utf-8")
            proposal = project / "wiki" / "curation" / "proposal.json"
            run("propose_content_curation.py", project, "--output", proposal)
            self.assertTrue(proposal.exists())
            self.assertIn("skill.design", proposal.read_text(encoding="utf-8"))
            self.assertEqual(card.read_text(encoding="utf-8"), before)

    def test_apply_curation_changes_only_explicitly_approved_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            skills = project / "wiki" / "skills"
            skills.mkdir()
            for identifier in ("design", "other"):
                (skills / f"{identifier}.md").write_text(
                    "---\n"
                    'schema_version: 2\n'
                    f'id: "skill.{identifier}"\n'
                    'type: "skill"\n'
                    f'title: "{identifier.title()}"\n'
                    'description: "Useful guidance."\n'
                    'tags: ["topic:skills"]\n'
                    f'source: {{"wiki_path": "wiki/skills/{identifier}.md"}}\n'
                    'dates: {"added_at": "2026-07-20T10:00:00+03:00", "updated_at": "2026-07-20T10:00:00+03:00"}\n'
                    'relations: []\n'
                    'aliases: []\n'
                    'status: "active"\n'
                    "---\n\n# Card\n",
                    encoding="utf-8",
                )
            proposal = project / "proposal.json"
            proposal.write_text(
                json.dumps(
                    {
                        "proposal_version": 1,
                        "updates": [
                            {"id": "skill.design", "tags": ["domain:web-design"], "aliases": ["website design"]},
                            {"id": "skill.other", "tags": ["domain:ai-agents"]},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            run("apply_content_curation.py", project, proposal, "--approve", "skill.design")
            design = (skills / "design.md").read_text(encoding="utf-8")
            other = (skills / "other.md").read_text(encoding="utf-8")
            self.assertIn("domain:web-design", design)
            self.assertIn("website design", design)
            self.assertNotIn("domain:ai-agents", other)
            run("lint_content.py", project)

    def test_content_index_query_and_lint(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            skills = project / "wiki" / "skills"
            skills.mkdir()
            (skills / "design.md").write_text(
                "---\n"
                'id: "skill.design-taste"\n'
                'type: "skill"\n'
                'title: "Design Taste"\n'
                'description: "Website design guidance."\n'
                'tags: ["domain:web-design", "capability:ui-design", "tool:figma", "topic:context-engineering"]\n'
                'source: {"url": "https://example.com/design"}\n'
                'dates: {"added_at": "2026-07-20T10:00:00+03:00", "updated_at": "2026-07-20T10:00:00+03:00"}\n'
                'relations: []\n'
                'aliases: ["website design"]\n'
                'status: "active"\n'
                "---\n\n# Design Taste\n",
                encoding="utf-8",
            )
            (skills / "broken.md").write_text(
                "---\n"
                'id: "skill.broken"\n'
                'type: "skill"\n'
                'title: "Broken Relation"\n'
                'description: "A card with an unresolved relation."\n'
                'tags: ["domain:web-design"]\n'
                'source: {"raw_path": "raw/sources/broken.md"}\n'
                'dates: {"added_at": "2026-07-21T10:00:00+03:00", "updated_at": "2026-07-21T10:00:00+03:00"}\n'
                'relations: [{"type": "related-to", "target": "skill.missing"}]\n'
                'aliases: []\n'
                'status: "active"\n'
                "---\n\n# Broken Relation\n",
                encoding="utf-8",
            )
            run("rebuild_content_index.py", project)
            result = run(
                "query_content.py", project, "--type", "skill", "--tag", "domain:web-design", "--added-since", "2026-07-21"
            )
            self.assertIn("Broken Relation", result.stdout)
            self.assertNotIn("Design Taste", result.stdout)
            text_result = run("query_content.py", project, "--text", "context engineering")
            self.assertIn("Design Taste", text_result.stdout)
            lint = run("lint_content.py", project, check=False)
            self.assertNotEqual(lint.returncode, 0)
            self.assertIn("unresolved relation", lint.stderr)

    def test_migration_adds_metadata_without_rewriting_card_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            card = project / "wiki" / "skills" / "design.md"
            card.parent.mkdir()
            card.write_text("# Design Skill\n\nUseful interface guidance.\n", encoding="utf-8")
            run("migrate_content_cards.py", project)
            content = card.read_text(encoding="utf-8")
            self.assertTrue(content.startswith("---\n"))
            self.assertIn('type: "skill"', content)
            self.assertTrue(content.endswith("# Design Skill\n\nUseful interface guidance.\n"))

    def test_migration_keeps_nested_index_pages_as_knowledge_cards(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            card = project / "wiki" / "skills" / "index.md"
            card.parent.mkdir()
            card.write_text("# Skills\n", encoding="utf-8")
            run("migrate_content_cards.py", project)
            self.assertTrue(card.read_text(encoding="utf-8").startswith("---\n"))

    def test_migration_classifies_skill_entities_as_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            card = project / "wiki" / "entities" / "design.md"
            card.parent.mkdir()
            card.write_text("# Design\n\nType: skill / interface design\n", encoding="utf-8")
            run("migrate_content_cards.py", project)
            self.assertIn('type: "skill"', card.read_text(encoding="utf-8"))

    def test_migration_refresh_types_repairs_existing_card_without_rewriting_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            card = project / "wiki" / "entities" / "design.md"
            card.parent.mkdir()
            card.write_text(
                "---\n"
                'id: "entities.design"\n'
                'type: "concept"\n'
                'title: "Design"\n'
                'description: "Existing card."\n'
                'tags: ["domain:web-design"]\n'
                'source: {"wiki_path": "wiki/entities/design.md"}\n'
                'dates: {"added_at": "2026-07-20T10:00:00+03:00", "updated_at": "2026-07-20T10:00:00+03:00"}\n'
                'relations: []\n'
                'aliases: []\n'
                'status: "active"\n'
                "---\n\n# Design\n\nType: skill / interface design\n",
                encoding="utf-8",
            )
            run("migrate_content_cards.py", project, "--refresh-types")
            content = card.read_text(encoding="utf-8")
            self.assertIn('type: "skill"', content)
            self.assertIn('description: "Existing card."', content)
            self.assertTrue(content.endswith("# Design\n\nType: skill / interface design\n"))

    def test_repo_scoped_install_smoke(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            skill = project / ".agents" / "skills" / "llm-wiki-session-memory"
            shutil.copytree(ROOT, skill, ignore=shutil.ignore_patterns(".git", "tests", "__pycache__"))
            subprocess.run(
                [PYTHON, str(skill / "scripts" / "bootstrap.py"), str(project)],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertTrue((project / "AGENTS.md").exists())
            self.assertTrue((project / "wiki" / "tag-taxonomy.yml").exists())
            self.assertTrue((project / "commands" / "save-memory.md").exists())
            self.assertTrue((skill / "templates" / "prompts" / "save-memory.md").exists())

    def test_prompt_installer_creates_codex_prompt_without_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            codex_home = Path(tmp) / "codex"
            run("install_codex_prompt.py", "--codex-home", codex_home)
            prompt = codex_home / "prompts" / "save-memory.md"
            self.assertTrue(prompt.exists())
            prompt.write_text("custom\n", encoding="utf-8")
            result = run("install_codex_prompt.py", "--codex-home", codex_home, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(prompt.read_text(encoding="utf-8"), "custom\n")

    def test_bootstrap_creates_wiki_without_overwriting_agents(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "AGENTS.md").write_text("keep me\n", encoding="utf-8")
            run("bootstrap.py", project)
            self.assertEqual((project / "AGENTS.md").read_text(encoding="utf-8"), "keep me\n")
            for item in (
                "AGENTS.md",
                "raw/sources",
                "raw/sessions",
                "wiki/sources",
                "wiki/concepts",
                "wiki/syntheses",
                "wiki/curation",
                "wiki/index.md",
                "wiki/log.md",
                "wiki/session-handoff.md",
                "wiki/session-index.jsonl",
                "wiki/tag-taxonomy.yml",
                "commands/save-memory.md",
            ):
                self.assertTrue((project / item).exists(), item)
            self.assertIn("schema_version: 2", (project / "wiki/tag-taxonomy.yml").read_text(encoding="utf-8"))

    def test_save_creates_tagged_session_and_lint_accepts_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            payload = {
                "started_at": "2026-07-18T10:00:00+03:00",
                "ended_at": "2026-07-18T11:00:00+03:00",
                "timezone": "Asia/Jerusalem",
                "agent": "codex",
                "task": "Add memory validation",
                "status": "completed",
                "transcript_source": "faithful-summary",
                "summary": "Added and checked metadata validation.",
                "files_changed": [{"path": "scripts/lint_memory.py", "action": "created"}],
                "tags": ["activity:implementation", "component:memory", "file:scripts/lint_memory.py"],
                "verification": [{"command": "python -m unittest", "result": "passed"}],
                "decisions": ["Keep raw evidence immutable."],
                "open_tasks": ["Add project cards."],
                "blockers": [],
                "next_actions": ["Review the generated handoff."],
                "relevant_pages": ["wiki/index.md"],
            }
            payload_file = project / "session.json"
            payload_file.write_text(json.dumps(payload), encoding="utf-8")
            result = run("save_memory.py", project, payload_file)
            session = project / result.stdout.strip()
            self.assertTrue(session.exists())
            self.assertIn("activity:implementation", session.read_text(encoding="utf-8"))
            index_rows = (project / "wiki/session-index.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(index_rows), 1)
            self.assertEqual(json.loads(index_rows[0])["status"], "completed")
            run("lint_memory.py", project)
            handoff = (project / "wiki" / "session-handoff.md").read_text(encoding="utf-8")
            self.assertIn("Keep raw evidence immutable.", handoff)
            self.assertIn("Add project cards.", handoff)
            self.assertIn("Review the generated handoff.", handoff)

    def test_save_rejects_invalid_closed_tag_and_missing_required_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            invalid = {"task": "Incomplete", "tags": ["activity:inventing"]}
            payload_file = project / "invalid.json"
            payload_file.write_text(json.dumps(invalid), encoding="utf-8")
            result = run("save_memory.py", project, payload_file, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("started_at", result.stderr)

    def test_save_rejects_multiple_activity_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            payload = {
                "started_at": "2026-07-18T10:00:00+03:00",
                "ended_at": "2026-07-18T11:00:00+03:00",
                "timezone": "Asia/Jerusalem",
                "agent": "codex",
                "task": "Validate activities",
                "status": "completed",
                "transcript_source": "faithful-summary",
                "summary": "Attempted invalid activity tags.",
                "files_changed": [],
                "tags": ["activity:testing", "activity:review"],
                "verification": [],
            }
            payload_file = project / "session.json"
            payload_file.write_text(json.dumps(payload), encoding="utf-8")
            result = run("save_memory.py", project, payload_file, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("exactly one activity:<value> tag", result.stderr)

    def test_memory_lint_reports_stale_and_duplicate_index_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            payload = {
                "started_at": "2026-07-18T10:00:00+03:00",
                "ended_at": "2026-07-18T11:00:00+03:00",
                "timezone": "Asia/Jerusalem",
                "agent": "codex",
                "task": "Check index integrity",
                "status": "completed",
                "transcript_source": "faithful-summary",
                "summary": "Created a valid session.",
                "files_changed": [],
                "tags": ["activity:testing"],
                "verification": [],
            }
            payload_file = project / "session.json"
            payload_file.write_text(json.dumps(payload), encoding="utf-8")
            run("save_memory.py", project, payload_file)
            index = project / "wiki/session-index.jsonl"
            valid_row = index.read_text(encoding="utf-8")
            index.write_text(valid_row + valid_row + '{"id":"ghost"}\n', encoding="utf-8")
            result = run("lint_memory.py", project, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duplicate index record for", result.stderr)
            self.assertIn("stale index record for ghost", result.stderr)

    def test_query_filters_yesterday_tag_file_and_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            now = datetime.now(timezone(timedelta(hours=3)))
            yesterday = (now - timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
            payload = {
                "started_at": yesterday.isoformat(),
                "ended_at": (yesterday + timedelta(minutes=30)).isoformat(),
                "timezone": "Asia/Jerusalem",
                "agent": "codex",
                "task": "Fix search",
                "status": "completed",
                "transcript_source": "faithful-summary",
                "summary": "Fixed session search.",
                "files_changed": [{"path": "scripts/query_memory.py", "action": "modified"}],
                "tags": ["activity:debugging", "component:search", "file:scripts/query_memory.py"],
                "verification": [],
            }
            payload_file = project / "session.json"
            payload_file.write_text(json.dumps(payload), encoding="utf-8")
            run("save_memory.py", project, payload_file)
            for args in (
                ("--yesterday", "--timezone", "Asia/Jerusalem"),
                ("--tag", "component:search"),
                ("--file", "scripts/query_memory.py"),
                ("--status", "completed"),
            ):
                result = run("query_memory.py", project, *args)
                self.assertIn("Fix search", result.stdout)


    def test_bootstrap_creates_media_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            self.assertTrue((project / "raw/assets").is_dir())
            self.assertTrue((project / "wiki/assets").is_dir())

    def test_media_proposal_discovers_markdown_html_and_youtube_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            source = project / "raw/sources/media.md"
            source.write_text("# Context\n\n![Layers](figures/layers.png)\n\n<img src=\"figures/html.png\" alt=\"HTML figure\">\n\nhttps://youtu.be/dQw4w9WgXcQ\n", encoding="utf-8")
            proposal = project / "wiki/curation/media.json"
            run("propose_media_curation.py", project, source, "--output", proposal)
            data = json.loads(proposal.read_text(encoding="utf-8"))
            self.assertEqual([item["kind"] for item in data["candidates"]], ["image", "image", "youtube"])
            self.assertEqual(list((project / "wiki/assets").glob("*.md")), [])

    def test_apply_media_curation_creates_asset_card_and_article_embed(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            run("bootstrap.py", project)
            self.write_card(project, "concepts.media", "concept", [])
            article = project / "wiki/cards/concepts-media.md"
            article.write_text(article.read_text(encoding="utf-8") + "\n## Context\n\nText.\n", encoding="utf-8")
            source = project / "raw/sources/media.md"
            source.write_text("# Context\n\n![Layers](figures/layers.png)\n", encoding="utf-8")
            figure = project / "raw/sources/figures/layers.png"
            figure.parent.mkdir()
            figure.write_bytes(b"png")
            proposal = project / "wiki/curation/media.json"
            run("propose_media_curation.py", project, source, "--output", proposal)
            data = json.loads(proposal.read_text(encoding="utf-8"))
            data["updates"] = [{"article_id": "concepts.media", "asset_id": "assets.media-layers", "candidate_id": "media-001", "placement": "inline", "caption": "Memory layers.", "tags": ["topic:memory"]}]
            proposal.write_text(json.dumps(data), encoding="utf-8")
            run("apply_media_curation.py", project, proposal, "--approve", "assets.media-layers")
            self.assertTrue((project / "raw/assets/media/layers.png").exists())
            self.assertTrue((project / "wiki/assets/media-layers.md").exists())
            self.assertIn("![[raw/assets/media/layers.png|680]]", article.read_text(encoding="utf-8"))
            run("lint_content.py", project, "--strict")


if __name__ == "__main__":
    unittest.main()
