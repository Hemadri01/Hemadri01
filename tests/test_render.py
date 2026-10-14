import unittest

from src.render import field_lines, render_markdown_sections, render_sections, render_terminal, resolve


class RenderTests(unittest.TestCase):
    def test_dotted_path_and_missing_path(self):
        data = {"misc": {"coffee": "black"}}
        self.assertEqual(resolve(data, "misc.coffee"), "black")
        with self.assertRaisesRegex(ValueError, "Missing profile value"):
            resolve(data, "misc.tea")

    def test_list_display_is_configured_by_field(self):
        data = {"items": ["one", "two"]}
        self.assertEqual(
            field_lines({"label": "items", "source": "items", "display": "multiline"}, data, 5, 2),
            ["items  one", "       two"],
        )
        self.assertEqual(
            field_lines({"label": "items", "source": "items", "display": "inline", "separator": " / "}, data, 5, 2),
            ["items  one / two"],
        )

    def test_terminal_fields_come_from_config(self):
        result = render_terminal({"username": "u", "misc": {"coffee": "black"}}, {
            "title": "{username}", "label_gap": 1,
            "fields": [{"label": "coffee", "source": "misc.coffee"}],
        })
        self.assertEqual(result.splitlines(), ["u", "-", "", "coffee black"])

    def test_terminal_can_rename_field_without_code_changes(self):
        result = render_terminal({"username": "u", "x": "v"}, {
            "title": "{username}", "label_gap": 1,
            "fields": [{"label": "x", "source": "x"}],
        })
        self.assertEqual(result.splitlines(), ["u", "-", "", "x v"])

    def test_skill_mapping_and_clickable_project_are_generic(self):
        data = {
            "skills": {"category": ["one", "two"]},
            "items": [{"name": "A project", "summary": "A summary", "url": "https://github.com/u/a"}],
        }
        sections = [
            {"command": "cat skills", "source": "skills", "display": "mapping"},
            {"command": "ls items", "source": "items", "display": "entries",
             "item": {"title": "name", "description": "summary", "url": "url"}},
        ]
        preview = render_sections(data, sections, "u@host:~$")
        readme = render_markdown_sections(data, sections, "u@host:~$")
        self.assertIn("category  one · two", preview)
        self.assertIn('<a href="https://github.com/u/a">A project</a>', readme)
        self.assertIn("u@host:~$ cat skills", readme)

    def test_repository_text_cannot_inject_html(self):
        data = {"items": [{"name": "<b>title</b>", "summary": "<script>bad</script>",
                            "url": "https://github.com/u/a"}]}
        sections = [{"command": "cat projects", "source": "items", "display": "entries",
                     "item": {"title": "name", "description": "summary", "url": "url"}}]
        result = render_markdown_sections(data, sections)
        self.assertIn("&lt;script&gt;bad&lt;/script&gt;", result)
        self.assertIn("&lt;b&gt;title&lt;/b&gt;", result)
        self.assertNotIn("<script>", result)

    def test_wrapped_multiline_fields_preserve_value_indentation(self):
        result = field_lines({"label": "x", "source": "values"},
                             {"values": ["one two three four five", "six seven"]},
                             1, 2, width=16)
        self.assertEqual(result, ["x  one two three", "   four five", "   six seven"])


if __name__ == "__main__":
    unittest.main()
