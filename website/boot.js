"use strict";
// Set the initial state before parsing the body to prevent a flash of output.
(() => {
  const root = document.documentElement;
  if (root.dataset.page !== "~/home" || window.location.hash) return;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
  let paused = false;
  try { paused = localStorage.getItem("hemadri-motion") === "off"; } catch (_) {}
  if (reduced.matches || paused) return;
  root.dataset.boot = "waiting";
  let done = false;
  const pending = [];
  const textRuns = [];
  const later = (fn, delay) => pending.push(setTimeout(() => { if (!done) fn(); }, delay));
  function finish() {
    done = true;
    pending.forEach(clearTimeout);
    textRuns.forEach(run => run.wrapper.replaceWith(run.original));
    delete root.dataset.boot;
    const command = document.querySelector("#boot-command");
    if (command) command.textContent = "fastfetch";
    const log = document.querySelector("#boot-log");
    if (log) log.querySelectorAll("div").forEach(row => { row.textContent = "[ ok ] " + row.dataset.label; });
    const skip = document.querySelector("#skip-intro");
    if (skip && document.activeElement === skip) {
      const heading = document.querySelector("#hero-title");
      heading.tabIndex = -1;
      heading.focus({ preventScroll: true });
    }
  }
  // Bounded fallback, including when DOM parsing or another script stalls.
  later(finish, 8000);
  reduced.addEventListener("change", () => { if (reduced.matches) finish(); });
  window.addEventListener("pageshow", event => { if (event.persisted) finish(); });

  function prepareText() {
    const nodes = [];
    document.querySelectorAll(".portrait-column, .hero-copy, .home-panes, .footer").forEach(container => {
      const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
      while (walker.nextNode()) {
        const original = walker.currentNode;
        if (original.textContent.trim() && !original.parentElement.closest('[aria-hidden="true"], .sr-only')) nodes.push(original);
      }
    });
    nodes.forEach(original => {
      const wrapper = document.createElement("span");
      const accessible = document.createElement("span");
      accessible.className = "sr-only";
      accessible.textContent = original.textContent;
      const visible = document.createElement("span");
      visible.setAttribute("aria-hidden", "true");
      const tail = document.createElement("span");
      tail.setAttribute("aria-hidden", "true");
      tail.className = "typing-tail";
      tail.textContent = original.textContent;
      wrapper.append(accessible, visible, tail);
      original.replaceWith(wrapper);
      textRuns.push({original, wrapper, visible, tail, characters: Array.from(original.textContent)});
    });
  }
  function typeOutput() {
    root.dataset.boot = "output";
    const total = textRuns.reduce((sum, run) => sum + run.characters.length, 0);
    const duration = 2800;
    const started = performance.now();
    function tick() {
      const progress = Math.min(1, (performance.now() - started) / duration);
      let remaining = Math.floor(total * progress);
      textRuns.forEach(run => {
        const count = Math.max(0, Math.min(run.characters.length, remaining));
        run.visible.textContent = run.characters.slice(0, count).join("");
        run.tail.textContent = run.characters.slice(count).join("");
        remaining -= run.characters.length;
      });
      if (progress < 1) later(tick, 16);
      else finish();
    }
    tick();
  }
  document.addEventListener("DOMContentLoaded", () => {
    if (done) return;
    const command = document.querySelector("#boot-command");
    const log = document.querySelector("#boot-log");
    if (!command || !log) { finish(); return; }
    command.textContent = "";
    root.dataset.boot = "startup";
    document.querySelector("#skip-intro").addEventListener("click", finish);
    document.querySelector("#motion-toggle").addEventListener("click", finish);
    document.addEventListener("focusin", event => {
      if (!done && event.target.closest(".hero-copy, .home-panes, .footer")) finish();
    });
    document.addEventListener("keydown", event => {
      if (!done && (event.key === "Escape" || event.key === "Enter") &&
          !event.target.closest("button, input, select, textarea, a")) finish();
    });
    prepareText();
    // Match the mockup's ten-cell bars and 28ms steps. These are intro effects,
    // not measurements of network loading or shell operations.
    const labels = ["loading profile", "mounting ~/research & ~/ideas", "starting session"];
    labels.forEach((label, index) => {
      const row = document.createElement("div");
      row.dataset.label = label;
      log.append(row);
      for (let step = 0; step <= 10; step++) later(() => {
        row.textContent = "[" + "█".repeat(step) + "░".repeat(10 - step) + "] " + label;
      }, index * 336 + step * 28);
      later(() => { row.textContent = "[ ok ] " + label; }, index * 336 + 308);
    });
    later(() => { root.dataset.boot = "typing"; }, 1200);
    [..."fastfetch"].forEach((letter, index) => later(() => { command.textContent += letter; }, 1200 + index * 70));
    later(typeOutput, 2000);
  }, { once: true });
})();
