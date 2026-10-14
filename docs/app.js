"use strict";
(() => {
  const root = document.documentElement;
  const select = document.querySelector("#theme");
  const allowed = new Set(Array.from(select.options, option => option.value));
  function applyTheme(theme) {
    if (!allowed.has(theme)) return;
    root.dataset.theme = theme;
    select.value = theme;
    document.querySelector("#theme-name").textContent = theme;
    const color = getComputedStyle(root).getPropertyValue("--background").trim();
    document.querySelector('meta[name="theme-color"]').content = color;
  }
  let stored;
  try { stored = localStorage.getItem("hemadri-theme"); } catch (_) {}
  applyTheme(allowed.has(stored) ? stored : root.dataset.theme);
  document.querySelector(".theme-control").hidden = false;
  select.addEventListener("change", () => {
    applyTheme(select.value);
    try { localStorage.setItem("hemadri-theme", select.value); } catch (_) {}
  });

  const projects = Array.from(document.querySelectorAll(".project"));
  const filters = Array.from(document.querySelectorAll("[data-filter]"));
  const filterBar = document.querySelector(".filters");
  if (filterBar) filterBar.hidden = false;
  filters.forEach(button => button.addEventListener("click", () => {
    const category = button.dataset.filter;
    let visible = 0;
    projects.forEach(project => {
      project.hidden = category !== "all" && project.dataset.category !== category;
      if (project.hidden) project.querySelectorAll("details[open]").forEach(details => details.open = false);
      else visible++;
    });
    filters.forEach(filter => filter.setAttribute("aria-pressed", String(filter === button)));
    const count = String(visible).padStart(2, "0") + (visible === 1 ? " project" : " projects");
    document.querySelector("#project-count").textContent = count;
    document.querySelector("#filter-status").textContent = count + " shown";
    document.querySelector("#no-projects").hidden = visible !== 0;
  }));

  // Keyboard theme cycling, with the same persisted preference as the select.
  const cycleTheme = () => {
    const themes = Array.from(allowed);
    select.value = themes[(themes.indexOf(root.dataset.theme) + 1) % themes.length];
    select.dispatchEvent(new Event("change"));
    document.querySelector("#theme-status").textContent = "Theme: " + select.selectedOptions[0].textContent;
  };
  document.querySelector("#cycle-theme").addEventListener("click", cycleTheme);
  document.addEventListener("keydown", event => {
    if (event.defaultPrevented || event.repeat || event.ctrlKey || event.metaKey || event.altKey) return;
    if (event.target.closest("input, textarea, select, button, [contenteditable], [role='textbox']")) return;
    if (event.key.toLowerCase() === "t") {
      event.preventDefault();
      cycleTheme();
    }
  });

  // Soft, slowly drifting pools of theme color.
  const field = document.querySelector("#ambient-field");
  const context = field ? field.getContext("2d") : null;
  const motionButton = document.querySelector("#motion-toggle");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  let motionPreference;
  try { motionPreference = localStorage.getItem("hemadri-motion"); } catch (_) {}
  let timer = null;
  let phase = 0;
  function drawField() {
    if (!context) return;
    context.clearRect(0, 0, field.width, field.height);
    const color = getComputedStyle(root).getPropertyValue("--heading").trim();
    const radius = Math.max(280, Math.min(field.width, field.height) * .7);
    const centers = [
      [.18 + Math.sin(phase * .22) * .2, .25 + Math.cos(phase * .18) * .2],
      [.78 + Math.cos(phase * .17) * .16, .72 + Math.sin(phase * .2) * .2]
    ];
    context.globalAlpha = .14;
    centers.forEach(([x, y]) => {
      const gradient = context.createRadialGradient(x * field.width, y * field.height, 0,
        x * field.width, y * field.height, radius);
      gradient.addColorStop(0, color);
      gradient.addColorStop(1, "transparent");
      context.fillStyle = gradient;
      context.fillRect(0, 0, field.width, field.height);
    });
    context.globalAlpha = 1;
  }

  function sizeField() {
    if (!context) return;
    field.width = window.innerWidth;
    field.height = window.innerHeight;
    drawField();
  }
  function syncMotion() {
    const enabled = !reducedMotion.matches && motionPreference !== "off";
    root.dataset.motion = enabled ? "on" : "off";
    motionButton.textContent = reducedMotion.matches ? "motion: reduced" : "motion: " + (enabled ? "on" : "off");
    motionButton.disabled = reducedMotion.matches;
    motionButton.setAttribute("aria-pressed", String(enabled));
    clearInterval(timer);
    timer = null;
    if (context && enabled && !document.hidden) timer = setInterval(() => { phase += .025; drawField(); }, 50);
  }
  motionButton.addEventListener("click", () => {
    motionPreference = root.dataset.motion === "on" ? "off" : "on";
    try { localStorage.setItem("hemadri-motion", motionPreference); } catch (_) {}
    syncMotion();
  });
  document.querySelector(".terminal-controls").hidden = false;
  reducedMotion.addEventListener("change", syncMotion);
  document.addEventListener("visibilitychange", syncMotion);
  window.addEventListener("resize", sizeField);
  select.addEventListener("change", drawField);
  sizeField();
  syncMotion();

})();
