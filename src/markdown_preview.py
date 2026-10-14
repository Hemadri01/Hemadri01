"""Create a separate pure Markdown comparison without changing README.md."""

import copy
import html
import re
from pathlib import Path

from .build import ROOT, load_inputs
from .render import field_lines, field_value, render_terminal, resolve, wrap_value
from .svg import optional_field, plain


def code(value: str) -> str:
    runs = re.findall(r"`+", value)
    fence = "`" * (1 + max(map(len, runs), default=0))
    return f"{fence} {value} {fence}"


def create_preview(root: Path = ROOT) -> Path:
    data, config, _ = load_inputs(root)
    terminal = copy.deepcopy(config["terminal"])
    terminal["palette"] = ""
    terminal["width"] = 88
    overview = config["svg"]["overview"]
    fields = overview["fields"]
    label_width = max(len(field["label"]) for field in fields)
    skills = "\n".join(
        line
        for field in fields
        for line in field_lines({**field, "display": "inline"}, data, label_width, 2, 88)
    )
    section = config["svg"]["projects"]
    item_config = section["item"]
    projects = []
    # The confirmed pins supply the link targets; presentation comes from config.
    for index, item in enumerate(resolve(data, section["source"]), 1):
        heading = plain(resolve(item, item_config["title"]))
        summary = plain(field_value(item_config["summary"], item))
        metadata = [optional_field(field, item) for field in item_config["metadata"]]
        meta = section["metadata_separator"].join(plain(value) for value in metadata if value)
        projects.append(
            f"#### [{code(f'{index:02} {heading}')}](<{item['url']}>)\n\n"
            + code(summary) + "\n\n" + code(meta)
        )
    contact_config = config["navigation"]["contact"]
    links = []
    for field in contact_config["fields"]:
        value = optional_field(field, data)
        if value:
            links.append(f"[{code(field['label'])}](<{value}>)")
    contact = ("### " + code(contact_config["label"]) + "\n\n" + " · ".join(links)) if links else ""
    replacements = {
        "PROMPT": terminal["prompt"],
        "IMAGE_ALT": config["image"]["alt"],
        "IMAGE_SOURCE": config["image"]["source"],
        "FACTS": render_terminal(data, terminal),
        "ABOUT_TITLE": overview["left_title"],
        "ABOUT": "\n\n".join("\n".join(wrap_value(value, "", "", 88))
                                for value in resolve(data, overview["source"])),
        "SKILLS_TITLE": overview["right_title"],
        "SKILLS": skills,
        "PROJECTS_TITLE": terminal["prefix"] + " " + section["command"],
        "PROJECTS": "\n\n".join(projects),
        "CONTACT": contact,
        "FOOTER": terminal["footer"],
    }
    document = (root / "templates/README.markdown.md.tpl").read_text(encoding="utf-8")
    for key, value in replacements.items():
        document = document.replace("{{" + key + "}}", value)
    destination = root / "README.markdown-preview.md"
    destination.write_text(document, encoding="utf-8")

    # Optional local HTML viewer; styling belongs to the viewer, not the Markdown.
    import markdown
    output = root / "output/markdown-preview"
    output.mkdir(parents=True, exist_ok=True)
    body = markdown.markdown(document, extensions=["fenced_code"])
    template = (root / "templates/markdown-viewer.html.tpl").read_text(encoding="utf-8")
    (output / "index.html").write_text(
        template.replace("{{BASE}}", html.escape(root.as_uri() + "/", quote=True))
                .replace("{{CONTENT}}", body),
        encoding="utf-8",
    )
    return destination


if __name__ == "__main__":
    print(create_preview())
