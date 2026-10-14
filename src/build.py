"""Build README.md and a plain-text preview from profile data and config."""

import json
import html
import argparse
from pathlib import Path

from .render import interpolate, linked_text, render_link_group, render_markdown_sections, render_profile_html, render_sections, render_terminal
from .svg import render_svg
from .themes import apply_theme, gallery, load_themes


ROOT = Path(__file__).resolve().parents[1]


def enrich_pins(pinned: list[dict], projects: list[dict]) -> list[dict]:
    """Retain the exact pin membership/order and enrich only matching URLs."""
    selected_by_url = {item["url"]: item for item in projects}
    return [{**item, **selected_by_url.get(item["url"], {})} for item in pinned]


def load_inputs(root: Path):
    data = json.loads((root / "data/profile.json").read_text(encoding="utf-8"))
    snapshot = json.loads((root / "data/pinned_repos.json").read_text(encoding="utf-8"))
    if snapshot["username"] != data["username"]:
        raise ValueError("Pin snapshot belongs to a different GitHub user")
    data["pinned_repos"] = enrich_pins(snapshot["repositories"], data["projects"])
    config = json.loads((root / "config/readme.json").read_text(encoding="utf-8"))
    image_config = config["image"]
    source = (root / image_config["source"]).resolve()
    if not source.is_relative_to(root.resolve()) or not source.is_file():
        raise ValueError("README image must be an existing file inside the project")
    return data, config, source.read_bytes()


def build(root: Path = ROOT, theme: str | None = None) -> tuple[str, str]:
    data, config, image = load_inputs(root)
    config = apply_theme(config, load_themes(root), theme)
    image_config = config["image"]
    svg = render_svg(data, config, image)
    terminal = config["terminal"]
    profile_block = render_terminal(data, terminal)
    sections = render_sections(data, config["sections"], terminal["prefix"])
    markdown_sections = render_markdown_sections(data, config["sections"], terminal["prefix"])
    sections_output = f"{sections}\n\n{terminal['footer']}"
    preview = f"{terminal['prompt']}\n[image: {image_config['source']}]\n\n{profile_block}\n\n{sections_output}\n"
    template = (root / "templates/README.md.tpl").read_text(encoding="utf-8")
    pin_links = " · ".join(
        linked_text(f"{index:02} {item['name'].split('/')[-1]}", item["url"])
        for index, item in enumerate(data["pinned_repos"], 1)
    )
    pin_links_block = (
        "<p><samp><b>" + html.escape(
            config["navigation"]["repository_label"]
        ) + "</b><br>\n"
        + pin_links + "</samp></p>"
        if pin_links else ""
    )
    readme = (
        template.replace("{{PROFILE_COMMAND}}", html.escape(terminal["prompt"]))
        .replace("{{SVG_SOURCE}}", "assets/profile.svg")
        .replace("{{SVG_ALT}}", html.escape(interpolate(config["svg"]["title"], data), quote=True))
        .replace("{{SVG_WIDTH}}", str(int(config["svg"]["width"])))
        .replace("{{PIN_LINKS_BLOCK}}", pin_links_block)
        .replace("{{CONTACT_LINKS_BLOCK}}", render_link_group(data, config["navigation"]["contact"]))
        .replace("{{TEXT_TOGGLE}}", html.escape(config["svg"]["text_toggle"]))
        .replace("{{PROFILE_BLOCK}}", render_profile_html(data, terminal))
        .replace("{{SECTIONS_BLOCK}}", markdown_sections)
        .replace("{{FOOTER}}", html.escape(terminal["footer"]))
    )
    (root / "assets/profile.svg").write_text(svg, encoding="utf-8")
    (root / "README.md").write_text(readme, encoding="utf-8")
    (root / "README.generated.txt").write_text(preview, encoding="utf-8")
    return readme, preview


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theme", choices=load_themes(ROOT), help="Theme for this build only")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--list-themes", action="store_true", help="List available themes")
    mode.add_argument("--preview-themes", action="store_true", help="Create a local comparison gallery")
    args = parser.parse_args()
    if args.list_themes:
        for name, preset in load_themes(ROOT).items():
            print(f"{name:12} {preset['description']}")
    elif args.preview_themes:
        print(gallery(ROOT, *load_inputs(ROOT)))
    else:
        _, preview = build(theme=args.theme)
        print(preview, end="")
