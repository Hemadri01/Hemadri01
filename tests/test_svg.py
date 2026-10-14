import base64
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET

from src.build import build, enrich_pins
from src.svg import SVG_NS, render_svg
from src.themes import apply_theme, load_themes


ROOT = Path(__file__).resolve().parents[1]
NS = {"s": SVG_NS}


class SvgTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "config/readme.json").read_text())
        self.config = apply_theme(self.config, load_themes(ROOT))
        self.data = json.loads((ROOT / "data/profile.json").read_text())
        pins = json.loads((ROOT / "data/pinned_repos.json").read_text())["repositories"]
        self.data["pinned_repos"] = enrich_pins(pins, self.data["projects"])
        self.image = (ROOT / self.config["image"]["source"]).read_bytes()

    def test_embeds_exact_original_image_without_external_resources(self):
        svg = ET.fromstring(render_svg(self.data, self.config, self.image))
        images = svg.findall("s:image", NS)
        self.assertEqual(len(images), 1)
        url = images[0].get("href")
        self.assertTrue(url.startswith("data:image/png;base64,"))
        self.assertEqual(base64.b64decode(url.split(",", 1)[1]), self.image)
        for node in svg.iter():
            self.assertNotIn(node.tag.rsplit("}", 1)[-1], {"script", "foreignObject", "style"})
            for attribute, value in node.attrib.items():
                if attribute.endswith("href"):
                    self.assertTrue(value.startswith("data:image/png;base64,"))

    def test_new_json_field_and_colors_work_with_xml_special_characters(self):
        self.data["misc"] = {"coffee": "Tea & <script>not code</script>"}
        self.config["terminal"]["fields"] = [{"label": "drink", "source": "misc.coffee"}]
        self.config["svg"]["colors"]["key"] = "#123456"
        svg = ET.fromstring(render_svg(self.data, self.config, self.image))
        spans = svg.findall(".//s:text", NS)
        self.assertTrue(any(span.text == "drink" and span.get("fill") == "#123456" for span in spans))
        self.assertIn(self.data["misc"]["coffee"], "".join(svg.itertext()))
        self.assertFalse(svg.findall(".//s:script", NS))

    def test_canvas_expands_for_more_content_and_long_tokens(self):
        self.config["svg"]["overview"]["source"] = "notes"
        self.data["notes"] = ["A short note"]
        short = ET.fromstring(render_svg(self.data, self.config, self.image))
        self.data["notes"] = ["x" * 150] * 30
        long = ET.fromstring(render_svg(self.data, self.config, self.image))
        self.assertGreater(int(long.get("height")), int(short.get("height")))
        self.assertEqual(long.get("width"), short.get("width"))
        self.assertEqual(long.get("viewBox"), f'0 0 {long.get("width")} {long.get("height")}')

    def test_build_writes_svg_and_clickable_text_fallback_deterministically(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder in ["data", "config", "templates"]:
                shutil.copytree(ROOT / folder, root / folder)
            (root / "assets").mkdir()
            (root / self.config["image"]["source"]).write_bytes(self.image)
            readme, preview = build(root)
            first_svg = (root / "assets/profile.svg").read_bytes()
            self.assertIn('src="assets/profile.svg"', readme)
            self.assertIn("<details>", readme)
            for pin in self.data["pinned_repos"]:
                self.assertIn(f'href="{pin["url"]}"', readme)
                self.assertIn(f'href="{pin["url"]}"', readme.split("<details>", 1)[0])
            self.assertEqual((root / "README.generated.txt").read_text(), preview)
            self.assertEqual(build(root), (readme, preview))
            self.assertEqual((root / "assets/profile.svg").read_bytes(), first_svg)

    def test_new_pins_without_manual_metadata_and_empty_pins(self):
        self.data["pinned_repos"] = [
            {"name": "example/new-repository", "summary": "New description",
             "url": "https://github.com/example/new-repository"}
        ]
        svg = ET.fromstring(render_svg(self.data, self.config, self.image))
        self.assertIn("example/new-repository", "".join(svg.itertext()))
        self.data["pinned_repos"] = []
        empty = ET.fromstring(render_svg(self.data, self.config, self.image))
        self.assertNotIn("ls -l ~/pinned/", "".join(empty.itertext()))


if __name__ == "__main__":
    unittest.main()
