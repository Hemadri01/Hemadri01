"""Check the generated static site's files, links, and source content."""

import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.references = []
        self.projects = 0
        self.images = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if tag in {"script", "img"}:
            self.references.append(attrs.get("src", ""))
        if tag in {"link", "a"}:
            self.references.append(attrs.get("href", ""))
        if tag == "img":
            assert attrs.get("alt"), "Image needs alt text"
            self.images.append(attrs)
        if tag == "article" and "project" in attrs.get("class", "").split():
            self.projects += 1


def check():
    output = ROOT.parent / "docs"
    pages = {}
    for filename in json.loads((output / "pages.json").read_text()):
        document = (output / filename).read_text()
        assert not re.search(r"\{\{[A-Z_]+\}\}", document), "Unresolved template field"
        page = Page()
        page.feed(document)
        assert len(page.ids) == len(set(page.ids)), f"Duplicate HTML IDs in {filename}"
        assert document.count('aria-current="page"') == 1, f"Missing active navigation in {filename}"
        pages[filename] = page
    for filename, page in pages.items():
        for reference in page.references:
            assert reference, "Empty link or asset URL"
            parts = urlsplit(reference)
            if parts.scheme:
                assert parts.scheme in {"https", "http", "mailto"}, reference
                continue
            target = unquote(parts.path) or filename
            asset = (output / target).resolve()
            assert asset.is_relative_to(output.resolve()), reference
            assert asset.is_file(), f"Missing file: {reference} in {filename}"
            if parts.fragment:
                assert target in pages and parts.fragment in pages[target].ids, reference
    document = (output / "research.html").read_text()
    page = pages["research.html"]
    pins = json.loads((ROOT / "data/pinned_repos.json").read_text())
    assert page.projects == len(pins["repositories"]), "Project membership differs from confirmed pins"
    for pin in pins["repositories"]:
        assert pin["url"] in document, f"Missing pinned link: {pin['url']}"
    original = (ROOT / "assets/portrait.png").read_bytes()
    assert original == (output / "assets/portrait.png").read_bytes(), "Portrait bytes changed"
    assert sum(len(p.images) for p in pages.values()) == 1, "Unexpected portrait count"
    assert not list(output.rglob("*.pdf")), "Outdated reference CV must not be published"
    print(f"Passed: {len(pages)} pages, {page.projects} confirmed projects, local assets, section links, IDs, and original portrait.")
    print("Build:", hashlib.sha256(document.encode()).hexdigest()[:16])


if __name__ == "__main__":
    check()
