"""Generic field resolution and monospace rendering for the profile README."""

import html
import re
import textwrap
from collections.abc import Mapping
from urllib.parse import urlsplit

PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_.]*)\}")
SCALARS = (str, int, float, bool)


class MissingValueError(ValueError):
    """A configured path is absent from the input data."""


def resolve(data: Mapping, path: str):
    """Follow object keys only: paths never evaluate expressions or Python."""
    if not path or any(not part for part in path.split(".")):
        raise ValueError(f"Invalid source path: {path!r}")
    value = data
    for part in path.split("."):
        if not isinstance(value, Mapping) or part not in value:
            raise MissingValueError(f"Missing profile value: {path}")
        value = value[part]
    return value


def interpolate(template: str, data: Mapping) -> str:
    def replacement(match):
        path = match.group(1)
        value = resolve(data, path)
        if not isinstance(value, SCALARS):
            raise ValueError(f"Template value must be scalar: {path}")
        return str(value)
    return PLACEHOLDER.sub(replacement, template)


def field_value(field: Mapping, data: Mapping):
    if ("source" in field) == ("template" in field):
        raise ValueError("Each field needs exactly one of 'source' or 'template'")
    return resolve(data, field["source"]) if "source" in field else interpolate(field["template"], data)


def wrap_value(value: str, prefix: str, continuation: str, width: int) -> list[str]:
    return textwrap.wrap(
        " ".join(value.split()), width=width,
        initial_indent=prefix, subsequent_indent=continuation,
        break_long_words=False, break_on_hyphens=False,
    ) or [prefix.rstrip()]


def field_lines(field: Mapping, data: Mapping, label_width: int, label_gap: int,
                width: int = 88, indent: str = "") -> list[str]:
    label = field["label"]
    try:
        value = field_value(field, data)
    except MissingValueError:
        if field.get("optional", False):
            return []
        raise
    if (value is None or value == "" or value == []) and field.get("optional", False):
        return []
    prefix = indent + label.ljust(label_width) + " " * label_gap
    continuation = " " * len(prefix)
    if isinstance(value, list):
        if not all(isinstance(item, SCALARS) for item in value):
            raise ValueError(f"List field {label!r} must contain scalar values")
        if not value:
            return []
        display = field.get("display", "multiline")
        if display == "inline":
            value = field.get("separator", " · ").join(map(str, value))
        elif display == "multiline":
            lines = []
            bullet = field.get("bullet", "")
            for index, item in enumerate(value):
                item_prefix = (prefix if index == 0 else continuation) + bullet
                lines.extend(wrap_value(str(item), item_prefix,
                                        continuation + " " * len(bullet), width))
            return lines
        else:
            raise ValueError(f"Invalid list display for {label!r}")
    if not isinstance(value, SCALARS):
        raise ValueError(f"Field {label!r} must resolve to a scalar or list")
    return wrap_value(str(value), prefix, continuation, width)


def render_terminal(data: Mapping, config: Mapping) -> str:
    title = interpolate(config["title"], data)
    fields = config["fields"]
    label_width = max((len(field["label"]) for field in fields), default=0)
    lines = [title, "-" * len(title), ""]
    for field in fields:
        lines.extend(field_lines(field, data, label_width, config.get("label_gap", 2),
                                 config.get("width", 88)))
    if config.get("palette"):
        lines.extend(["", config["palette"]])
    return "\n".join(lines)


def linked_text(label: str, url: str) -> str:
    """Escape repository text and URLs before using anchors inside a pre block."""
    parsed = urlsplit(url)
    web = parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    email = parsed.scheme == "mailto" and "@" in parsed.path and not parsed.netloc
    if not (web or email) or any(char.isspace() for char in url):
        raise ValueError(f"Expected an HTTP(S) or mailto link: {url!r}")
    return f'<a href="{html.escape(url, quote=True)}">{html.escape(label)}</a>'


def render_link_group(data: Mapping, config: Mapping) -> str:
    """Render configured links, omitting empty or optional missing values."""
    links = []
    for field in config["fields"]:
        try:
            value = field_value(field, data)
        except MissingValueError:
            if field.get("optional"):
                continue
            raise
        if value is None or value == "":
            continue
        links.append(linked_text(f"[ {field['label']} ]", str(value)))
    if not links:
        return ""
    return (f'<p><samp><b>{html.escape(config["label"])}</b><br>\n'
            + " · ".join(links) + "</samp></p>")


def render_profile_html(data: Mapping, config: Mapping, indent: str = "") -> str:
    lines = render_terminal(data, config).splitlines()
    title = html.escape(lines[0])
    if config.get("title_link"):
        title = linked_text(lines[0], resolve(data, config["title_link"]))
    rendered = [title, *(html.escape(line) for line in lines[1:])]
    return "\n".join(html.escape(indent) + line if line else "" for line in rendered)


def section_value(section: Mapping, data: Mapping):
    value = field_value(section, data)
    if not value and "fallback_source" in section:
        value = resolve(data, section["fallback_source"])
    return value


def entry_fields(item_config: Mapping) -> list[Mapping]:
    if "fields" in item_config:
        return item_config["fields"]
    return [{"label": "", "source": item_config["description"]}]


def render_entries(value: list, section: Mapping, html_links: bool = False) -> str:
    item_config = section["item"]
    fields = entry_fields(item_config)
    label_width = max((len(field["label"]) for field in fields), default=0)
    entries = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, Mapping):
            raise ValueError("Entry values must be objects")
        title = str(resolve(item, item_config["title"]))
        url = str(resolve(item, item_config["url"]))
        heading = linked_text(title, url) if html_links else title
        lines = [f"[{index:02}] {heading}"]
        for field in fields:
            content = "\n".join(field_lines(field, item, label_width, 2,
                                            section.get("width", 88), indent="     "))
            if content:
                lines.append(html.escape(content) if html_links else content)
        if not html_links:
            lines.append("     " + url)
        entries.append("\n".join(lines))
    return "\n\n".join(entries)


def section_body(section: Mapping, value) -> str:
    display = section["display"]
    width = section.get("width", 88)
    if display == "paragraph" and isinstance(value, SCALARS):
        return "\n".join(wrap_value(str(value), "", "", width))
    if display == "paragraphs" and isinstance(value, list):
        return "\n\n".join("\n".join(wrap_value(str(item), "", "", width)) for item in value)
    if display == "bullets" and isinstance(value, list):
        return "\n".join("\n".join(wrap_value(str(item), "  - ", "    ", width)) for item in value)
    if display == "inline" and isinstance(value, list):
        return "\n".join(wrap_value(section.get("separator", " · ").join(map(str, value)), "", "", width))
    if display == "mapping" and isinstance(value, Mapping):
        label_width = max((len(str(label)) for label in value), default=0)
        rows = []
        for label, item in value.items():
            field = {"label": str(label), "source": "value", "display": "inline",
                     "separator": section.get("separator", " · ")}
            rows.extend(field_lines(field, {"value": item}, label_width, 2, width))
        return "\n".join(rows)
    if display == "links" and isinstance(value, Mapping):
        return "\n".join(f"{label.lower():<10} {url}" for label, url in value.items() if url)
    if display == "entries" and isinstance(value, list):
        return render_entries(value, section)
    raise ValueError(f"Invalid section display or value for {section['command']!r}")


def render_sections(data: Mapping, sections: list[Mapping], prefix: str = "$") -> str:
    blocks = []
    for section in sections:
        body = section_body(section, section_value(section, data))
        if body:
            blocks.append(f"{prefix} {section['command']}\n{body}")
    return "\n\n".join(blocks)


def render_markdown_sections(data: Mapping, sections: list[Mapping], prefix: str = "$") -> str:
    """Render escaped content inside the template's single terminal pre block."""
    blocks = []
    for section in sections:
        value = section_value(section, data)
        body = section_body(section, value)
        if not body:
            continue
        command = html.escape(f"{prefix} {section['command']}")
        if section["display"] == "entries":
            output = render_entries(value, section, html_links=True)
        elif section["display"] == "links":
            output = "\n".join(f"{html.escape(label.lower().ljust(10))} {linked_text(url, url)}"
                               for label, url in value.items() if url)
        else:
            output = html.escape(body)
        blocks.append(f"<b>{command}</b>\n\n{output}")
    return "\n\n".join(blocks)
