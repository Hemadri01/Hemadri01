"""Render a compact, data-driven terminal profile as a self-contained SVG."""

import base64
import math
import re
import struct
import textwrap
import xml.etree.ElementTree as ET
from collections.abc import Mapping

from .render import MissingValueError, field_value, interpolate, resolve


SVG_NS = "http://www.w3.org/2000/svg"
XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("", SVG_NS)


def png_size(image: bytes) -> tuple[int, int]:
    """Read dimensions without decoding or modifying the source image."""
    if len(image) < 24 or image[:8] != b"\x89PNG\r\n\x1a\n" or image[12:16] != b"IHDR":
        raise ValueError("The profile image must be a PNG")
    width, height = struct.unpack(">II", image[16:24])
    if not width or not height:
        raise ValueError("PNG dimensions must be positive")
    return width, height


def plain(value, separator=" · ") -> str:
    if isinstance(value, list):
        return separator.join(map(str, value))
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    raise ValueError("SVG fields must resolve to a scalar or list")


def optional_field(field: Mapping, data: Mapping):
    try:
        return field_value(field, data)
    except MissingValueError:
        if field.get("optional"):
            return ""
        raise


class Canvas:
    def __init__(self, config: Mapping, title: str, description: str):
        self.width = int(config["width"])
        self.font = int(config["font_size"])
        self.leading = int(config["line_height"])
        self.pad = int(config["padding"])
        if self.width < 500 or self.font < 10 or self.leading < self.font or self.pad < 12:
            raise ValueError("Invalid SVG layout dimensions")
        self.cell = self.font * 0.61
        self.colors = config["colors"]
        for color in [*self.colors.values(), *config["palette"], *config["window_dots"]]:
            if not isinstance(color, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
                raise ValueError("SVG colors must be six-digit hex values")
        self.root = ET.Element(f"{{{SVG_NS}}}svg", {
            "role": "img", "aria-labelledby": "title description",
            "font-family": config["font_family"],
            "font-size": str(self.font), f"{{{XML_NS}}}space": "preserve",
        })
        self.add("title", {"id": "title"}).text = title
        self.add("desc", {"id": "description"}).text = description
        self.back = self.add("rect", {"x": "0.5", "y": "0.5", "rx": "8",
                                      "width": str(self.width - 1), "fill": self.colors["background"],
                                      "stroke": self.colors["border"]})

    def add(self, tag: str, attrs: dict, parent=None):
        return ET.SubElement(self.root if parent is None else parent, f"{{{SVG_NS}}}{tag}", attrs)

    def rect(self, x, y, w, h, role, radius=0):
        self.add("rect", {"x": f"{x:g}", "y": f"{y:g}", "width": f"{w:g}",
                          "height": f"{h:g}", "rx": str(radius), "fill": self.colors[role]})

    def line(self, x1, y, x2, role="rule"):
        self.add("line", {"x1": f"{x1:g}", "x2": f"{x2:g}", "y1": f"{y:g}",
                          "y2": f"{y:g}", "stroke": self.colors[role], "stroke-width": "1"})

    def vertical(self, x, y1, y2, role="rule"):
        self.add("line", {"x1": f"{x:g}", "x2": f"{x:g}", "y1": f"{y1:g}",
                          "y2": f"{y2:g}", "stroke": self.colors[role], "stroke-width": "1"})

    def text(self, x, y, value, role="text", size=None, weight=None):
        attrs = {"x": f"{x:g}", "y": f"{y:g}", "fill": self.colors[role]}
        if size:
            attrs["font-size"] = str(size)
        if weight:
            attrs["font-weight"] = weight
        node = self.add("text", attrs)
        node.text = str(value)
        return node

    def wrap(self, value, width_px, *, separator=" · ") -> list[str]:
        count = max(12, int(width_px / self.cell))
        return textwrap.wrap(" ".join(plain(value, separator).split()), width=count,
                             break_long_words=True, break_on_hyphens=False) or [""]

    def finish(self, height):
        height = math.ceil(height)
        self.root.set("width", str(self.width))
        self.root.set("height", str(height))
        self.root.set("viewBox", f"0 0 {self.width} {height}")
        self.back.set("height", str(height - 1))
        self.root.text = "\n"
        for child in self.root:
            child.tail = "\n"
        return ET.tostring(self.root, encoding="unicode") + "\n"


def command(canvas: Canvas, y: float, prefix: str, instruction: str) -> float:
    canvas.text(canvas.pad, y, prefix, "prompt", weight="bold")
    canvas.text(canvas.pad + (len(prefix) + 1) * canvas.cell, y, instruction, "text")
    return y + canvas.leading


def hero(canvas: Canvas, data: Mapping, config: Mapping, image: bytes, y: float) -> float:
    svg = config["svg"]
    layout = svg["layout"]
    image_width = int(config["image"]["width"])
    source_width, source_height = png_size(image)
    if not 1 <= image_width <= 1000:
        raise ValueError("Image width must be 1..1000")
    image_height = image_width * source_height / source_width
    image_x = canvas.pad + int(layout["hero_inset"])
    image_y = y + 8
    img = canvas.add("image", {"x": str(image_x), "y": f"{image_y:g}",
                               "width": str(image_width), "height": f"{image_height:g}",
                               "preserveAspectRatio": "xMidYMid meet",
                               "href": "data:image/png;base64," + base64.b64encode(image).decode("ascii")})
    canvas.add("title", {}, img).text = config["image"]["alt"]
    right_x = image_x + image_width + int(layout["hero_gap"])
    available = canvas.width - canvas.pad - right_x
    if available < 250:
        raise ValueError("Not enough room for the fastfetch facts")
    title = interpolate(config["terminal"]["title"], data)
    cy = y + 28
    canvas.text(right_x, cy, title, "heading", size=int(svg["heading_size"]), weight="bold")
    cy += canvas.leading * 0.55
    canvas.line(right_x, cy, canvas.width - canvas.pad)
    cy += canvas.leading
    fields = config["terminal"]["fields"]
    label_w = max((len(field["label"]) for field in fields), default=0)
    value_x = right_x + (label_w + 3) * canvas.cell
    value_width = canvas.width - canvas.pad - value_x
    for field in fields:
        value = field_value(field, data)
        lines = canvas.wrap(value, value_width, separator=field.get("separator", " · "))
        canvas.text(right_x, cy, field["label"].lower(), "key")
        for line in lines:
            canvas.text(value_x, cy, line)
            cy += canvas.leading
        cy += int(layout["field_gap"])
    swatch_y = cy + 4
    for index, color in enumerate(svg["palette"]):
        canvas.add("rect", {"x": f"{right_x + index * 27:g}", "y": f"{swatch_y:g}",
                            "width": "22", "height": "11", "fill": color})
    cy = swatch_y + 23
    canvas.vertical(image_x + image_width + int(layout["hero_gap"]) / 2,
                    image_y, max(image_y + image_height, cy), "rule")
    return max(image_y + image_height, cy) + int(layout["section_gap"])


def two_columns(canvas: Canvas, data: Mapping, config: Mapping, y: float) -> float:
    section = config["svg"]["overview"]
    gap = int(config["svg"]["layout"]["column_gap"])
    left_w = int(config["svg"]["layout"]["overview_width"])
    left_x = canvas.pad
    right_x = left_x + left_w + gap
    right_w = canvas.width - canvas.pad - right_x
    if right_w < 300:
        raise ValueError("Not enough room for the skills column")
    canvas.line(canvas.pad, y, canvas.width - canvas.pad)
    y += canvas.leading * 1.1
    canvas.text(left_x, y, section["left_title"], "heading", weight="bold")
    canvas.text(right_x, y, section["right_title"], "heading", weight="bold")
    left_y = y + canvas.leading * 1.35
    for paragraph in resolve(data, section["source"]):
        for line in canvas.wrap(paragraph, left_w):
            canvas.text(left_x, left_y, line)
            left_y += canvas.leading
        left_y += canvas.leading * 0.45
    right_y = y + canvas.leading * 1.35
    labels = section["fields"]
    label_w = max((len(field["label"]) for field in labels), default=0)
    value_x = right_x + (label_w + 2) * canvas.cell
    for field in labels:
        lines = canvas.wrap(field_value(field, data),
                            canvas.width - canvas.pad - value_x,
                            separator=field.get("separator", " · "))
        canvas.text(right_x, right_y, field["label"], "key")
        for line in lines:
            canvas.text(value_x, right_y, line)
            right_y += canvas.leading
        right_y += 4
    return max(left_y, right_y) + int(config["svg"]["layout"]["section_gap"])


def projects(canvas: Canvas, data: Mapping, config: Mapping, y: float) -> float:
    section = config["svg"]["projects"]
    layout = config["svg"]["layout"]
    items = resolve(data, section["source"])
    if not items:
        return y
    canvas.line(canvas.pad, y, canvas.width - canvas.pad)
    y += canvas.leading * 1.2
    y = command(canvas, y, config["terminal"]["prefix"], section["command"])
    canvas.text(canvas.width - canvas.pad - 150, y - canvas.leading,
                f"[ {len(items):02} {section['count_label']} ]", "muted")
    y += canvas.leading * 0.25
    index_x = canvas.pad
    content_x = canvas.pad + int(layout["project_indent"])
    usable = canvas.width - canvas.pad - content_x
    item_cfg = section["item"]
    for number, item in enumerate(items, 1):
        canvas.text(index_x, y, f"{number:02}", "index")
        for title_line in canvas.wrap(resolve(item, item_cfg["title"]), usable):
            canvas.text(content_x, y, title_line, "heading", weight="bold")
            y += canvas.leading
        y += canvas.leading * 0.15
        summary = optional_field(item_cfg["summary"], item)
        if summary:
            for line in canvas.wrap(summary, usable):
                canvas.text(content_x, y, line)
                y += canvas.leading
        metadata = [optional_field(field, item) for field in item_cfg["metadata"]]
        meta = section["metadata_separator"].join(plain(part) for part in metadata if part)
        if meta:
            for line in canvas.wrap(meta, usable):
                canvas.text(content_x, y, line, "muted")
                y += canvas.leading
        y += int(layout["project_gap"])
        if number < len(items):
            canvas.line(content_x, y - int(layout["project_gap"]) / 2,
                        canvas.width - canvas.pad, "soft_rule")
    return y + int(layout["section_gap"]) // 2


def render_svg(data: Mapping, config: Mapping, image: bytes) -> str:
    svg = config["svg"]
    canvas = Canvas(svg, interpolate(svg["title"], data),
                    interpolate(svg["description"], data))
    layout = svg["layout"]
    titlebar_h = int(layout["titlebar_height"])
    canvas.rect(1, 1, canvas.width - 2, titlebar_h, "titlebar", radius=7)
    for index, color in enumerate(svg["window_dots"]):
        canvas.add("circle", {"cx": str(canvas.pad + index * 18), "cy": str(titlebar_h / 2 + 1),
                              "r": "5", "fill": color})
    canvas.text(canvas.width / 2 - 100, titlebar_h / 2 + canvas.font * 0.35,
                interpolate(svg["window_title"], data), "muted")
    canvas.line(1, titlebar_h + 1, canvas.width - 1)
    y = titlebar_h + canvas.leading * 1.6
    y = command(canvas, y, config["terminal"]["prefix"],
                config["terminal"]["prompt"].split("$", 1)[-1].strip())
    y += canvas.leading * 0.45
    y = hero(canvas, data, config, image, y)
    y = two_columns(canvas, data, config, y)
    y = projects(canvas, data, config, y)
    canvas.line(canvas.pad, y, canvas.width - canvas.pad)
    y += canvas.leading * 1.3
    canvas.text(canvas.pad, y, config["terminal"]["footer"], "prompt")
    canvas.text(canvas.width - canvas.pad - 190, y, svg["footer_note"], "muted")
    return canvas.finish(y + canvas.pad)
