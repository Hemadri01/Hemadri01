# Personal website

This directory is a standalone website, separate from the parent README generator.
The parent's SVG-only profile layout rules apply to the README, not this website.

- Use accessible HTML, CSS, and small progressive enhancements in JavaScript.
- Preserve the warm terminal-inspired design, readable text, and working links.
- Factual profile content lives in data/profile.json; website-specific narrative and presentation live in data/site.json.
- Keep the original portrait bytes and aspect ratio intact.
- Do not imply research results are final or substitute publications for projects.
- Blank contact links stay hidden. Do not publish the outdated reference CV.
- Build with python3 build.py. ../docs/ is the repository-root publication directory for GitHub Pages.
- Themes and filtering must work with keyboard controls. Content stays readable without JS.
- Keep this project portable for static hosting, including GitHub Pages.

- Keep home CV-like; detailed research and projects belong on research.html. Ideas have their own index, topic pages, and individual note pages.
- Use real HTML links and vanilla CSS/JavaScript; no frameworks or client-side routing.
- Store notebook topics and entries in data/ideas.json. Do not invent personal opinions or notes.
