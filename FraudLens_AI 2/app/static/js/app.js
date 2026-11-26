(() => {
  const html = document.documentElement;
  const saved = localStorage.getItem("fraudlens-theme");
  if (saved) html.setAttribute("data-theme", saved);
  const toggle = document.getElementById("themeToggle");
  if (toggle) toggle.addEventListener("click", () => {
    const next = html.getAttribute("data-theme") === "dark" ? "light" : "dark";
    html.setAttribute("data-theme", next);
    localStorage.setItem("fraudlens-theme", next);
  });
  const input = document.getElementById("mediaInput");
  const zone = document.getElementById("dropzone");
  const selected = document.getElementById("selectedFile");
  const form = document.getElementById("uploadForm");
  const btn = document.getElementById("analyzeBtn");
  const showFile = file => {
    if (!file) return;
    selected.textContent = `${file.name} · ${(file.size / 1024 / 1024).toFixed(2)} MB`;
  };
  if (input) input.addEventListener("change", () => showFile(input.files[0]));
  if (zone) {
    ["dragenter","dragover"].forEach(evt => zone.addEventListener(evt, e => {
      e.preventDefault(); zone.classList.add("dragover");
    }));
    ["dragleave","drop"].forEach(evt => zone.addEventListener(evt, e => {
      e.preventDefault(); zone.classList.remove("dragover");
    }));
    zone.addEventListener("drop", e => {
      const f = e.dataTransfer.files[0];
      if (f) { input.files = e.dataTransfer.files; showFile(f); }
    });
  }
  if (form) form.addEventListener("submit", () => {
    if (btn) { btn.disabled = true; btn.innerHTML = "Analyzing media…"; }
  });
})();
