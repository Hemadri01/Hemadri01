# Editing this profile README

## Build

Requires Python 3.10 or newer. The README generator has no third-party dependencies.

```sh
python3 -m src.build
```

This writes `README.md` and `assets/profile.svg`, prints the terminal preview, and saves a local copy in `README.generated.txt`. Commit the Markdown and SVG together; the text preview is ignored by Git.

## Edit

### Contact links

Fill the empty slots in `data/profile.json` under `links`:

```json
{
  "Website": "https://your-domain.example",
  "CV": "https://your-domain.example/cv.pdf",
  "Thesis": "",
  "Email": "mailto:you@example.org",
  "LinkedIn": "",
  "Scholar": ""
}
```

These are examples only. Empty slots are hidden, with no placeholder or broken
links published. Keep your existing GitHub entry. Run `python3 -m src.build`
after adding real addresses.

`navigation.contact` in `config/readme.json` controls labels, order, and
selection using generic source paths. The visible **Contact / elsewhere**
row appears immediately below the terminal panel, followed by **Repository
links**. Both contain real HTML links. The panel's footer is just the terminal
prompt; it no longer points to links absent from the PDF preview.

### Themes

Five palettes are available: `warm` (the original), `nord` (ice blue),
`tokyo` (navy and violet), `rose-pine` (rose and lavender), and
`paper` (light ivory). They share the same layout, content, and original image.

Set the top-level `"theme": "warm"` in `config/readme.json` to your preferred
name, then run `python3 -m src.build`. This selection also applies to scheduled
pin updates. Palette colors live in `config/themes.json`.

```sh
python3 -m src.build --list-themes
python3 -m src.build --preview-themes
python3 -m src.build --theme nord
```

The preview command creates `output/themes/index.html` with all five panels
without changing the README. Open it locally and click a panel for full size.
`--theme` changes the generated README for that build only; it does not save
your choice in the config. A normal build restores the configured theme.
Rebuild the optional PDF with `python3 -m src.pdf_preview` after switching.
These are generator options; the GitHub README displays the selected theme.

| File | Purpose |
| --- | --- |
| `data/profile.json` | Profile facts, skills, and detailed project descriptions |
| `data/pinned_repos.json` | Confirmed pin membership, order, and source |
| `config/readme.json` | Field selection, labels, order, wrapping, image size, and SVG colors/typography |
| `config/themes.json` | Named color palettes |
| `templates/README.md.tpl` | SVG embedding, visible repository links, and the collapsed text version |
| `assets/Deadpan Hi in Black and White.png` | The unchanged source image |
| `src/svg.py` | Generic SVG terminal layout and rendering |
| `assets/profile.svg` | Generated terminal panel; edit the JSON and rebuild |

Fields use generic dotted JSON paths. Lists support `display: "inline"` with a configurable `separator`, or `display: "multiline"` with an optional `bullet`. Adding, renaming, or reordering fields requires JSON edits only.

The visible README is one warm, dark SVG terminal panel inspired by the local mockups. It contains a fastfetch header, an about/skills area, and numbered pinned repository rows. The original PNG bytes are embedded as a data URL at their original aspect ratio. `image.width` controls display size; `svg.layout.hero_gap` controls the space before the profile facts in pixels.

Adjust the selected theme's `colors` in `config/themes.json` to change prompt, field-label, heading, rule, and body colors. Its `palette` controls the fastfetch color swatches. In `config/readme.json`, `svg.width`, `svg.font_size`, `svg.line_height`, `svg.padding`, and `svg.layout` control the layout. Height follows the content; text wraps within a fixed width. Everything is generated locally with Python's standard library using SVG primitives and the embedded PNG.

`terminal.fields` selects the fastfetch facts. `svg.overview` selects the short introduction and skill fields. `svg.projects` selects the repository source, summary, and metadata fields. The top-level `sections` configuration controls the longer text version, retaining the detailed project writeups. No profile field names need to be added to Python when these selections change.

An SVG embedded as an image has no individually clickable repository links. A visible monospace link list immediately below the panel provides direct access to all confirmed pins. The collapsed **Full text version and project details** section provides selectable text, research interests, the full skills list, and detailed writeups with links.

## Verify and preview

```sh
python3 -m unittest discover -s tests -v
```

For an optional dark PDF preview, install the `weasyprint` Python package, then run:

```sh
python3 -m src.build
python3 -m src.pdf_preview
```

The PDF is saved to `output/pdf/README-preview.pdf`. It renders the actual SVG panel, so its colors and layout come from the same artifact displayed on GitHub. Font rendering and display size can still vary by viewer. The visible HTML link list and collapsed text version are omitted from this visual preview. Rebuild it locally after content changes; the pin workflow does not generate PDFs.

## Pinned repositories

The README follows the exact membership and order in `data/pinned_repos.json`. Matching URLs receive the detailed project descriptions from `data/profile.json`; new pins use GitHub's name and description. Unpinned projects are not substituted. The initial snapshot is Hemadri's explicitly supplied list.

To refresh from GitHub, provide `GH_TOKEN` or `GITHUB_TOKEN` in your shell environment, then run:

```sh
python3 -m src.fetch_pinned
python3 -m src.build
```

The fetcher queries GraphQL's `user.pinnedItems` and records `source: "github-graphql"` after success. API failures preserve the previous snapshot. A successful empty response removes the pinned section. SSH credentials cannot authenticate GraphQL requests.

`.github/workflows/update-pinned.yml` schedules a refresh at 03:17 UTC daily and supports manual runs. It uses the workflow's `GITHUB_TOKEN` with `contents: write` and commits changed pin data, `README.md`, and `assets/profile.svg` together.

## Publish

Upload this folder's contents to the public `Hemadri01/Hemadri01` repository, including `.github/` and `.gitignore`. Keep `README.md` at the repository root. Place the workflow on the default branch and enable GitHub Actions for automatic pin updates. The workflow still needs its first successful live run.

Local previews, reference mockups, caches, environment files, and tool state are excluded by `.gitignore`. Browser uploads do not honor `.gitignore`: omit `mockups/`, `output/`, caches, and local tool folders manually.
