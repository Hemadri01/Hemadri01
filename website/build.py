"""Build the standalone static portfolio using Python's standard library."""

import argparse
import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent


def esc(value):
    return html.escape(str(value), quote=True)


def link(value):
    parts = urlsplit(value)
    if not ((parts.scheme in {"http", "https"} and parts.netloc)
            or (parts.scheme == "mailto" and "@" in parts.path)):
        raise ValueError(f"Invalid public link: {value!r}")
    return esc(value)


def build():
    profile = json.loads((ROOT / "data/profile.json").read_text())
    site = json.loads((ROOT / "data/site.json").read_text())
    themes = json.loads((ROOT / "data/themes.json").read_text())
    pins = json.loads((ROOT / "data/pinned_repos.json").read_text())
    if pins["username"] != profile["username"]:
        raise ValueError("Pin snapshot belongs to another profile")
    if site["default_theme"] not in themes:
        raise ValueError("Unknown default theme")
    selected = {item["url"]: item for item in profile["projects"]}
    projects = [{**pin, **selected.get(pin["url"], {})} for pin in pins["repositories"]]
    # GitHub Pages only publishes /docs at the repository root. This website
    # source lives in website/, so the generated site belongs one level above.
    output = ROOT.parent / "docs"
    output.mkdir(exist_ok=True)
    shutil.copytree(ROOT / "assets", output / "assets", dirs_exist_ok=True)
    for filename in ("styles.css", "app.js", "boot.js"):
        shutil.copyfile(ROOT / filename, output / filename)

    css = []
    for name, theme in themes.items():
        if not re.fullmatch(r"[a-z][a-z0-9-]*", name):
            raise ValueError("Theme names must be lowercase identifiers")
        tokens = {**theme["colors"], **{f"swatch-{i}": c for i, c in enumerate(theme["palette"])}}
        if any(not re.fullmatch(r"#[a-fA-F0-9]{6}", color) for color in tokens.values()):
            raise ValueError("Invalid palette color")
        channels = [int(tokens["background"][offset:offset + 2], 16) for offset in (1, 3, 5)]
        scheme = "light" if sum(channels) > 384 else "dark"
        css.append(f':root[data-theme="{name}"]{{color-scheme:{scheme};' + "".join(f"--{k}:{v};" for k, v in tokens.items()) + "}")
    (output / "themes.css").write_text("\n".join(css) + "\n")
    project_html = []
    for index, item in enumerate(projects, 1):
        name = item["name"].split("/")[-1]
        presentation = site["project_labels"].get(name, {"title": name, "category": "other"})
        detail_items = "".join(f"<li>{esc(detail)}</li>" for detail in item.get("details", []))
        details = (f'<details><summary>Project notes <span aria-hidden="true">+</span></summary>'
                   f'<ul>{detail_items}</ul></details>') if detail_items else ""
        tags = "".join(f"<span>{esc(tag)}</span>" for tag in item.get("stack", []))
        project_html.append(
            f'<article class="project" data-category="{esc(presentation["category"])}">'
            f'<span class="project-number">{index:02}</span><div class="project-content">'
            f'<div class="project-heading"><h3><a href="{link(item["url"])}">{esc(presentation["title"])}</a></h3>'
            f'<span class="project-kind">{esc(presentation["category"])}</span></div>'
            f'<p>{esc(item.get("summary", ""))}</p><div class="project-bottom">'
            f'<div class="project-tags">{tags}</div><a class="source-link" href="{link(item["url"])}" '
            f'aria-label="View {esc(presentation["title"])} source">source ↗</a></div>{details}</div></article>'
        )
    contact = "".join(
        f'<a href="{link(profile["links"][name])}">{esc(name)} <span aria-hidden="true">↗</span></a>'
        for name in site["contact_fields"] if profile["links"].get(name)
    )
    skills = "".join(
        f'<div><dt>{esc(field["label"])}</dt><dd>{esc(" · ".join(profile["skills"][field["source"]]))}</dd></div>'
        for field in site["skill_fields"]
    )
    degree = profile["education"]
    undergrad = degree["undergraduate"]
    research_url = next(item["url"] for item in profile["projects"] if item["name"] == "rtt-aware-routing")
    replacements = {
        "TITLE": esc(site["title"]), "DESCRIPTION": esc(site["description"]),
        "DEFAULT_THEME": esc(site["default_theme"]),
        "DEGREE": esc(degree["degree"]), "INSTITUTION": esc(degree["institution"]),
        "INSTITUTION_SHORT": esc(degree["institution_short"]), "YEAR": esc(degree["year"]),
        "UNDERGRAD_DEGREE": esc(undergrad["degree"]), "UNDERGRAD_INSTITUTION": esc(undergrad["institution"]),
        "UNDERGRAD_UNIVERSITY": esc(undergrad["university"]),
        "LOCATION": esc(profile["location"]), "GITHUB": link(profile["links"]["GitHub"]),
        "CURRENT_WORK": esc(profile["research"]["current"]),
        "ABOUT_ACADEMIC": esc(profile["bio"][0]), "ABOUT_PERSONAL": esc(profile["bio"][-1]),
        "HERO_INTRO": esc(site["hero_intro"]), "HERO_CV": "",
        "RESEARCH_TITLE": esc(site["research_title"]), "RESEARCH_INTRO": esc(site["research_intro"]),
        "RESEARCH_CURRENT": esc(site["research_current"]), "RESEARCH_LIMIT": esc(site["research_limit"]),
        "RESEARCH_URL": link(research_url),
        "INTERESTS": "".join(f"<li>{esc(value)}</li>" for value in profile["research"]["interests"]),
        "PROJECTS": "\n".join(project_html), "PROJECT_COUNT": f"{len(projects):02}",
        "CONTACT_LINKS": contact, "SKILLS": skills,
        "THEME_OPTIONS": "".join(f'<option value="{esc(name)}"'
            + (" selected" if name == site["default_theme"] else "")
            + f'>{esc(site["theme_labels"].get(name, name))}</option>' for name in themes),
    }
    if profile["links"].get("CV"):
        replacements["HERO_CV"] = f'<a class="text-link" href="{link(profile["links"]["CV"])}">CV ↗</a>'
    replacements["COURSEWORK"] = esc(" · ".join(profile.get("coursework", [])))
    layout = (ROOT / "templates/layout.html").read_text()
    generated = []

    def render(filename, template, title, section, extra=None):
        values = {**replacements, "PAGE_TITLE": esc(title),
                  "SESSION_PATH": "~/" + esc(section), **(extra or {})}
        values["NAVIGATION"] = "".join(
            f'<a href="{url}"' + (' aria-current="page"' if key == section.split("/")[0] else '')
            + f'><span aria-hidden="true">{i:02} / </span>{label}</a>'
            for i, (key, label, url) in enumerate([
                ("home", "home", "index.html"),
                ("research", "research &amp; projects", "research.html"),
                ("ideas", "ideas", "ideas.html")])
        )
        document = layout.replace("{{CONTENT}}", (ROOT / "templates" / template).read_text())
        document = re.sub(r"\{\{([A-Z_]+)\}\}", lambda match: values[match[1]], document)
        (output / filename).write_text(document, encoding="utf-8")
        generated.append(filename)

    render("index.html", "index.html", "Home", "home")
    render("research.html", "research.html", "Research & projects", "research")
    ideas = json.loads((ROOT / "data/ideas.json").read_text())
    topic_rows = []
    slugs = set()
    note_slugs = set()
    for topic in ideas["topics"]:
        slug = topic["slug"]
        if not re.fullmatch(r"[a-z][a-z0-9-]*", slug) or slug in slugs:
            raise ValueError("Topic slugs must be unique lowercase identifiers")
        slugs.add(slug)
        notes = topic.get("notes", [])
        topic_rows.append(f'<a class="topic-row" href="ideas-{slug}.html"><div><h3>{esc(topic["title"])}</h3>'
                         f'<p>{esc(topic["description"])}</p></div><span>{len(notes):02} notes ↗</span></a>')
        note_rows = []
        for note in notes:
            note_slug = note["slug"]
            if not re.fullmatch(r"[a-z][a-z0-9-]*", note_slug) or note_slug in note_slugs:
                raise ValueError("Note slugs must be unique lowercase identifiers")
            note_slugs.add(note_slug)
            filename = f"note-{note_slug}.html"
            note_rows.append(f'<a class="topic-row" href="{filename}"><div><h3>{esc(note["title"])}</h3>'
                             f'<p>{esc(note.get("summary", ""))}</p></div><span>read ↗</span></a>')
            render(filename, "note.html", note["title"], "ideas/" + slug, {
                "TOPIC_SLUG": slug, "TOPIC_TITLE": esc(topic["title"]),
                "NOTE_TITLE": esc(note["title"]),
                "NOTE_BODY": "".join(f"<p>{esc(paragraph)}</p>" for paragraph in note["paragraphs"])})
        render(f"ideas-{slug}.html", "topic.html", topic["title"], "ideas/" + slug, {
            "TOPIC_SLUG": slug, "TOPIC_TITLE": esc(topic["title"]),
            "TOPIC_DESCRIPTION": esc(topic["description"]), "NOTE_COUNT": str(len(notes)),
            "NOTES": "".join(note_rows) or '<p class="empty-notes"><span class="dim">[ empty ]</span> No notes published here yet.</p>'})
    render("ideas.html", "ideas.html", "Ideas & notes", "ideas", {"TOPICS": "".join(topic_rows)})
    # Delete only pages produced by a previous build, when a topic or note is removed.
    manifest = output / "pages.json"
    if manifest.exists():
        for old in json.loads(manifest.read_text()):
            if old not in generated and re.fullmatch(r"[a-z0-9-]+\.html", old):
                (output / old).unlink(missing_ok=True)
    manifest.write_text(json.dumps(generated, indent=2) + "\n")
    (output / ".nojekyll").touch()
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sync-profile", type=Path, help="Copy an explicitly selected profile JSON before building")
    args = parser.parse_args()
    if args.sync_profile:
        source = args.sync_profile.resolve()
        json.loads(source.read_text())
        shutil.copyfile(source, ROOT / "data/profile.json")
    print(build())
