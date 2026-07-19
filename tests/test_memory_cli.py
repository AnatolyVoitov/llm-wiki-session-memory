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
                "wiki/index.md",
                "wiki/log.md",
                "wiki/session-handoff.md",
                "wiki/session-index.jsonl",
                "wiki/tag-taxonomy.yml",
                "commands/save-memory.md",
            ):
                self.assertTrue((project / item).exists(), item)

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


if __name__ == "__main__":
    unittest.main()
