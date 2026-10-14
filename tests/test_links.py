import unittest

from src.render import render_link_group


class LinkTests(unittest.TestCase):
    def test_empty_slots_are_hidden_and_email_is_clickable(self):
        config = {"label": "Contact / elsewhere", "fields": [
            {"label": "Website", "source": "links.site"},
            {"label": "Email", "source": "links.email"},
            {"label": "CV", "source": "links.cv", "optional": True},
        ]}
        data = {"links": {"site": "", "email": "mailto:person@example.org"}}
        result = render_link_group(data, config)
        self.assertIn('href="mailto:person@example.org"', result)
        self.assertNotIn("Website", result)
        self.assertNotIn("CV", result)
        data["links"]["email"] = ""
        self.assertEqual(render_link_group(data, config), "")

    def test_link_labels_are_escaped_and_executable_urls_rejected(self):
        config = {"label": "<Contact>", "fields": [{"label": "<site>", "source": "url"}]}
        result = render_link_group({"url": "https://example.org"}, config)
        self.assertIn("&lt;site&gt;", result)
        with self.assertRaises(ValueError):
            render_link_group({"url": "javascript:alert(1)"}, config)
