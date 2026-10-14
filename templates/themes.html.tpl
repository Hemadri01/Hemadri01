<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Profile themes</title>
<style>
body { margin: 0; padding: 32px; background: #181818; color: #eeeeee; font: 16px/1.5 monospace; }
h1 { margin: 0; } p { color: #bbbbbb; }
main { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 480px), 1fr)); gap: 32px; }
section { min-width: 0; } h2 { margin-bottom: 0; }
img { width: 100%; height: auto; display: block; }
</style>
<h1>Profile themes</h1>
<p>Click a panel to view it at full size. Select the default with "theme" in config/readme.json.</p>
<main>{{THEMES}}</main>
</html>
