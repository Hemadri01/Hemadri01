import copy
import json
import unittest
import xml.etree.ElementTree as ET

from src.build import ROOT, load_inputs
from src.svg import render_svg, SVG_NS
from src.themes import apply_theme, load_themes


class ThemeTests(unittest.TestCase):
    def test_themes_change_colors_without_changing_content_or_geometry(self):
        data, config, image = load_inputs(ROOT)
        original = copy.deepcopy(config)
        snapshots = []
        backgrounds = []
        themes = load_themes(ROOT)
        for name in themes:
            themed = apply_theme(config, themes, name)
            root = ET.fromstring(render_svg(data, themed, image))
            backgrounds.append(root.find(f"{{{SVG_NS}}}rect").get("fill"))
            for node in root.iter():
                node.attrib.pop("fill", None)
                node.attrib.pop("stroke", None)
            snapshots.append(ET.tostring(root))
        self.assertEqual(len(set(backgrounds)), len(themes))
        self.assertEqual(len(set(snapshots)), 1)
        self.assertEqual(config, original)

    def test_config_default_override_and_invalid_selection(self):
        config = json.loads((ROOT / "config/readme.json").read_text())
        themes = load_themes(ROOT)
        config["theme"] = "nord"
        self.assertEqual(apply_theme(config, themes)["theme"], "nord")
        self.assertEqual(apply_theme(config, themes, "paper")["theme"], "paper")
        self.assertEqual(config["theme"], "nord")
        with self.assertRaisesRegex(ValueError, "Unknown theme"):
            apply_theme(config, themes, "missing")
