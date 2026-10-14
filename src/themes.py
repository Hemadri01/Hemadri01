"""Named JSON palettes and a local comparison gallery."""

import copy
import html
import json
from pathlib import Path


def load_themes(root: Path) -> dict:
    return json.loads((root / "config/themes.json").read_text(encoding="utf-8"))


def apply_theme(config: dict, themes: dict, name: str | None = None) -> dict:
    selected = name or config.get("theme", "warm")
    if selected not in themes:
        raise ValueError(f"Unknown theme {selected!r}. Choose: {', '.join(themes)}")
    result = copy.deepcopy(config)
    preset = themes[selected]
    for key in ("colors", "palette", "window_dots"):
        result["svg"][key] = copy.deepcopy(preset[key])
    result["theme"] = selected
    return result


def gallery(root: Path, data: dict, config: dict, image: bytes) -> Path:
    from .svg import render_svg

    output = root / "output/themes"
    output.mkdir(parents=True, exist_ok=True)
    cards = []
    themes = load_themes(root)
    for name, preset in themes.items():
        # Filenames are independent of user-editable theme names.
        filename = f"theme-{len(cards) + 1}.svg"
        themed = apply_theme(config, themes, name)
        (output / filename).write_text(render_svg(data, themed, image), encoding="utf-8")
        label = html.escape(name)
        cards.append(
            f'<section><h2>{label}</h2><p>{html.escape(preset["description"])}</p>'
            f'<a href="{filename}"><img src="{filename}" alt="{label} profile"></a></section>'
        )
    template = (root / "templates/themes.html.tpl").read_text(encoding="utf-8")
    destination = output / "index.html"
    destination.write_text(template.replace("{{THEMES}}", "\n".join(cards)), encoding="utf-8")
    return destination
