<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<base href="{{BASE}}">
<title>Markdown-only README preview</title>
<style>
:root { color-scheme: light dark; --bg:#ffffff; --fg:#1f2328; --muted:#59636e; --line:#d1d9e0; --code:#f6f8fa; --link:#0969da; }
@media(prefers-color-scheme:dark) { :root { --bg:#0d1117; --fg:#f0f6fc; --muted:#9198a1; --line:#3d444d; --code:#151b23; --link:#4493f8; } }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font:16px/1.6 system-ui,sans-serif; }
aside,article { max-width:960px; margin:24px auto; padding:24px 32px; }
aside { color:var(--muted); font-size:14px; padding-bottom:0; }
article { border:1px solid var(--line); border-radius:6px; }
img { max-width:100%; height:auto; }
h3 { margin:28px 0 16px; } h4 { margin:24px 0 12px; }
pre { padding:16px; overflow-x:auto; background:var(--code); border-radius:6px; }
code { font:85%/1.6 ui-monospace,monospace; background:var(--code); border-radius:4px; padding:2px 5px; }
pre code { padding:0; background:none; }
a { color:var(--link); text-decoration:none; } a:hover { text-decoration:underline; }
hr { border:0; height:1px; background:var(--line); margin:28px 0; }
@media(max-width:600px) { article,aside { margin:12px; padding:16px; } }
</style>
<aside>Markdown-only comparison. Approximate local rendering; GitHub spacing and fonts may differ.</aside>
<article>{{CONTENT}}</article>
</html>
