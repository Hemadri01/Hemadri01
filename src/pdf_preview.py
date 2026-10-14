"""Render the README's actual SVG panel as a single-page PDF preview."""

from pathlib import Path
import xml.etree.ElementTree as ET

from weasyprint import CSS, HTML

from .build import ROOT
from .svg import SVG_NS


def create_preview(root: Path = ROOT) -> Path:
    output = root / "output/pdf/README-preview.pdf"
    output.parent.mkdir(parents=True, exist_ok=True)
    svg = ET.parse(root / "assets/profile.svg").getroot()
    width, height = float(svg.get("width")), float(svg.get("height"))
    background = svg.find(f"{{{SVG_NS}}}rect").get("fill")
    css = f"""
    @page {{ size: {width + 48}px {height + 48}px; margin: 24px; background: {background}; }}
    body {{ margin: 0; padding: 0; }}
    img {{ display: block; width: {width}px; height: {height}px; }}
    """
    html = '<!doctype html><meta charset="utf-8"><body><img src="assets/profile.svg"></body>'
    document = HTML(string=html, base_url=str(root))
    document.write_pdf(output, stylesheets=[CSS(string=css)])
    return output


if __name__ == "__main__":
    print(create_preview())
