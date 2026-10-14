import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.build import enrich_pins
from src.fetch_pinned import main, parse_pinned_response
from src.render import render_sections


class PinnedRepositoriesTests(unittest.TestCase):
    def test_parses_repository_order_and_empty_descriptions(self):
        payload = {"data": {"user": {"pinnedItems": {"nodes": [
            {"nameWithOwner": "u/first", "url": "https://github.com/u/first", "description": "First repo"},
            {"nameWithOwner": "u/second", "url": "https://github.com/u/second", "description": None},
        ]}}}}
        self.assertEqual(parse_pinned_response(payload), [
            {"name": "u/first", "summary": "First repo", "url": "https://github.com/u/first"},
            {"name": "u/second", "summary": "", "url": "https://github.com/u/second"},
        ])

    def test_section_uses_manual_fallback_only_when_no_pins(self):
        section = [{"command": "ls projects/", "source": "pinned_repos", "fallback_source": "projects",
                    "display": "entries", "item": {"title": "name", "description": "summary", "url": "url"}}]
        project = {"name": "manual", "summary": "Manual choice", "url": "https://github.com/u/manual"}
        pin = {"name": "pinned", "summary": "Pinned choice", "url": "https://github.com/u/pinned"}
        self.assertIn("manual", render_sections({"pinned_repos": [], "projects": [project]}, section))
        result = render_sections({"pinned_repos": [pin], "projects": [project]}, section)
        self.assertIn("pinned", result)
        self.assertNotIn("manual", result)

    def test_graphql_errors_do_not_clear_existing_pins(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            (root / "data/profile.json").write_text('{"username":"u"}')
            output = root / "data/pinned_repos.json"
            previous = '{"username":"u","source":"user-confirmed","repositories":[{"url":"https://github.com/u/a"}]}'
            output.write_text(previous)
            with patch.dict("os.environ", {"GH_TOKEN": "test-only"}), \
                    patch("src.fetch_pinned.fetch_pinned", side_effect=ValueError("GitHub GraphQL error")):
                with self.assertRaisesRegex(ValueError, "GitHub GraphQL error"):
                    main(root)
            self.assertEqual(output.read_text(), previous)

    def test_enrichment_keeps_exact_pin_membership_and_order(self):
        projects = [{"url": "https://github.com/u/a", "summary": "Detailed A"},
                    {"url": "https://github.com/u/b", "summary": "Detailed B"},
                    {"url": "https://github.com/u/c", "summary": "Unpinned"}]
        pins = [{"url": "https://github.com/u/b", "name": "b", "summary": "Short B"},
                {"url": "https://github.com/u/new", "name": "new", "summary": "New"},
                {"url": "https://github.com/u/a", "name": "a", "summary": "Short A"}]
        result = enrich_pins(pins, projects)
        self.assertEqual([p["url"] for p in result], [p["url"] for p in pins])
        self.assertEqual([p["summary"] for p in result], ["Detailed B", "New", "Detailed A"])
        self.assertEqual(enrich_pins([], projects), [])

    def test_real_configuration_does_not_substitute_curated_projects_for_pins(self):
        root = Path(__file__).resolve().parents[1]
        config = json.loads((root / "config/readme.json").read_text())
        section = next(s for s in config["sections"] if s.get("source") == "pinned_repos")
        data = {"pinned_repos": [], "projects": [{"name": "Not pinned"}]}
        self.assertEqual(render_sections(data, [section]), "")


if __name__ == "__main__":
    unittest.main()
