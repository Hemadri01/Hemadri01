# Hemadri's personal website

A standalone static portfolio with a warm terminal style, research, projects,
education, and contact links. Built using Python's standard library, HTML, CSS,
and vanilla JavaScript. It has no external font, analytics, or runtime API dependencies.

## License

The generator and website code are available under the [MIT License](LICENSE).
The portrait, personal biography, CV information, project descriptions, and
other personal content are not included in that license; do not reuse them
without permission.

## Open

Open `../docs/index.html` in a browser. The page also works directly from a local file.
Theme selection, project filters, and project notes work without a backend.
All content is available without JavaScript.

## Terminal controls

- Home opens with a short `fastfetch` sequence above the portrait and profile.
  Three startup progress bars run first, followed by the typed command. The portrait
  appears and all home-page text types out in document order. The entire intro
  takes about five seconds; these bars are decorative, not network measurements.
- Use **skip intro**, Escape, or Enter outside controls to reveal everything immediately.
- Motion-off and system reduced-motion settings bypass the introduction.
  Deep links also bypass it. Without JavaScript, all content is visible immediately.
- Soft pools of theme color slowly drift behind the content. The background follows
  the selected theme, pauses in hidden tabs, and becomes still with motion off
  or reduced-motion preferences.
- Press **T** outside form controls to cycle themes, or use the theme selector.
- The bottom session bar shows the current page or notebook topic.
- The portrait is unchanged. The layout uses compact terminal panes inspired by
  `mockups/index (3).html`; the command sequence follows the earlier mockups.

## Build and check

```sh
cd /media/hsd/Storage/Profile/website
python3 build.py
python3 check.py
```

For a local HTTP preview on your own machine:

```sh
python3 -m http.server 8765 --directory ../docs
```

Then open `http://localhost:8765`.

## Pages

- `../docs/index.html`: CV-style overview, education, skills, current work, and contact.
- `../docs/research.html`: thesis context, ongoing work, and the confirmed project list.
- `../docs/ideas.html`: topic directory.
- `../docs/ideas-<topic>.html`: notes belonging to a topic.
- `../docs/note-<slug>.html`: an individual note, generated when content is added.

These are ordinary linked HTML pages. There is no client-side router, framework,
package manager, or runtime dependency. Python only assembles static templates;
the deployed site uses vanilla CSS and JavaScript. Navigation works without JS.

## Add an idea

Edit `data/ideas.json`. Topics have `slug`, `title`, `description`, and `notes`.
The initial topics are editable organisational headings with no invented entries.
Add an object like this to a topic's `notes` array, replacing the example text:

```json
{
  "slug": "my-first-note",
  "title": "My first note",
  "summary": "A short description for the topic index.",
  "paragraphs": ["First paragraph.", "Another paragraph."]
}
```

Run `python3 build.py`. This creates `note-my-first-note.html` and links it from
its topic. Slugs must be unique lowercase words separated with hyphens. Text is
escaped automatically. Removing an entry removes its generated page on rebuild.
Edit `templates/note.html` to change the layout shared by all entries.

## Edit

- `data/profile.json`: profile facts, skills, project summaries, and contact URLs.
- `data/pinned_repos.json`: confirmed repository membership and order.
- `data/site.json`: website introduction, research narrative, labels, and presentation.
- `data/themes.json`: five color palettes. Set `default_theme` in `data/site.json`.
- `templates/layout.html`: shared navigation, footer, and document shell.
- Other `templates/*.html` files: home, research, ideas, topic, and note layouts.
- `styles.css`, `app.js`: plain CSS and JavaScript for layout and progressive enhancements.
- `assets/portrait.png`: exact copy of the supplied Deadpan Hi image.

Website content is an independent snapshot of the README's profile data. To
explicitly import later changes while this folder is inside the profile workspace:

```sh
python3 build.py --sync-profile ../data/profile.json
```

Website-specific introductory and research prose is edited separately in
`data/site.json`. Refresh the local pin snapshot separately when your confirmed
pins change.

Fill `links.CV`, `links.Thesis`, `links.Email`, `links.LinkedIn`, or
`links.Scholar` in the website's profile JSON to expose those links.
Use HTTPS URLs, or `mailto:you@example.org` for email. Empty entries are hidden.
The older reference CV is deliberately not included in the published files.

## Static hosting

The contents of the repository-root `docs/` folder are the complete deployable website. All assets use
relative paths, so it can be hosted at a domain root or a GitHub Pages project path.
For GitHub Pages, commit this entire folder and choose the `main` branch and
the `/docs` folder in the repository's Pages settings.

A private Sites project has been registered in `.openai/hosting.json`, but it
has **not been deployed**. Publication requires the Sites source helper, a Node
runtime, and network access. Those are unavailable in the current execution
environment. Reuse the saved project ID when continuing publication.

## Verification limits

Static asset, internal link, content, and JavaScript behavior checks were run.
Full browser and responsive visual QA could not run here: local server sockets
are blocked and the installed browser cannot start in this sandbox.
