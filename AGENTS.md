# README generator rules

- `data/profile.json` owns factual profile content.
- `data/pinned_repos.json` stores the exact confirmed pin list and its source. It may come from the user's explicit list or GitHub GraphQL. Never infer current pins from cached popular-repository cards, or substitute curated projects for missing pins.
- When a pinned repository matches a manually selected project by URL, keep the manually written summary and follow GitHub's pin order.
- `config/readme.json` owns field selection, field order, labels, and layout.
- `src/render.py` must stay independent of semantic field names such as education, research, and tools. Resolve sources and templates generically.
- The user approved a generated SVG to preserve a single terminal panel with full colors. This supersedes the original text-only/no-SVG requirement. Keep the visible profile in one continuous `assets/profile.svg` panel; do not split sections into separate cards.
- `src/svg.py` is the SVG renderer. It must use generic JSON fields and presentation roles, with dimensions and colors in `config/readme.json`. Embed the exact `assets/Deadpan Hi in Black and White.png` bytes next to the fastfetch facts using a data URL. Display scaling is allowed; do not change the source pixels or aspect ratio. Do not add an `xdg-open` command.
- Use self-contained SVG primitives and escaped text, without scripts, external resources, or `foreignObject`. Keep a collapsed text version with working repository links in the README because an SVG embedded as an image does not provide individual clickable links.
- The ESP32 Morse controller is a hobby project. RTT-aware routing extends the user's MSc thesis. Keep coursework, hobby work, and research accurately described.
- Source reviews must distinguish inspected code from README descriptions. Local snapshots are not proof of the latest remote version. Never claim a full repository code review when access failed.
- Build with `python3 -m src.build`. Commit both `README.md` and `assets/profile.svg` when content changes. The pin workflow must regenerate and commit both. `README.generated.txt` and PDF previews in `output/` are local, ignored artifacts.
- Keep the published repository focused on profile content, assets, configuration, templates, generator code, tests, and the pin update workflow. Keep session notes, source-review helpers, caches, and duplicate images out of the repository.
- Keep profile facts and project descriptions monospaced. Keep external cards optional and separate.
