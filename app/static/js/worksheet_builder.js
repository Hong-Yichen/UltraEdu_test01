(function () {
  const root = document.getElementById("ws-builder");
  if (!root) return;

  const worksheetId = Number(root.dataset.worksheetId);
  const pageWidth = Number(root.dataset.pageWidth);
  const pageHeight = Number(root.dataset.pageHeight);
  const csrf = window.CSRF_TOKEN || "";

  const pageEl = document.getElementById("ws-page");
  const inspector = document.getElementById("ws-inspector");
  const inspectorEmpty = document.getElementById("ws-inspector-empty");

  const elementsDataEl = document.getElementById("ws-elements-data");
  let elements = JSON.parse((elementsDataEl && elementsDataEl.textContent) || "[]");
  let selectedId = null;

  function apiFetch(url, opts) {
    opts = opts || {};
    opts.headers = Object.assign(
      { "Content-Type": "application/json", "X-CSRFToken": csrf },
      opts.headers || {}
    );
    return fetch(url, opts).then((r) => {
      if (!r.ok) return r.json().then((b) => { throw new Error(b.description || r.statusText); });
      return r.json();
    });
  }

  function elementPreview(el) {
    switch (el.element_type) {
      case "multiple_choice":
        return (el.config_json.options || [])
          .map((o) => `<div class="ws-mcq-option"><input type="radio" disabled> ${escapeHtml(o.text || "")}</div>`)
          .join("") || '<span class="muted">No options yet</span>';
      case "fill_blank":
        return '<div class="ws-handwriting-hint">Handwriting canvas — student writes the answer here</div>';
      case "matching":
        return '<span class="muted">Matching pairs (edit as JSON)</span>';
      case "label_diagram":
        return '<div class="ws-handwriting-hint">Handwriting canvas — student labels the diagram here</div>';
      case "drawing_area":
        return '<div class="ws-drawing-hint">Drawing area — student sketches here</div>';
      case "handwriting_area":
        return '<div class="ws-handwriting-hint">Handwriting area — student writes here</div>';
      case "image_upload":
        return '<span class="muted">Image upload slot</span>';
      case "text_highlight":
        return `<div class="muted">${escapeHtml((el.config_json.passage || "").slice(0, 80))}</div>`;
      default:
        return "";
    }
  }

  function escapeHtml(s) {
    return (s || "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  function renderElements() {
    pageEl.querySelectorAll(".ws-element").forEach((n) => n.remove());
    for (const el of elements) {
      const div = document.createElement("div");
      div.className = "ws-element editable" + (el.id === selectedId ? " selected" : "");
      div.style.left = el.x + "px";
      div.style.top = el.y + "px";
      div.style.width = el.width + "px";
      div.style.height = el.height + "px";
      div.dataset.id = el.id;
      div.innerHTML =
        `<span class="ws-type-badge">${el.element_type.replace('_', ' ')}</span>` +
        `<div class="ws-prompt">${escapeHtml(el.prompt_text || "(no prompt)")}</div>` +
        elementPreview(el) +
        `<div class="ws-points">${el.points} pt${el.points === 1 ? "" : "s"}</div>`;
      div.addEventListener("mousedown", (e) => startDrag(e, el));
      div.addEventListener("click", (e) => {
        e.stopPropagation();
        selectElement(el.id);
      });
      pageEl.appendChild(div);
    }
  }

  function startDrag(e, el) {
    e.preventDefault();
    selectElement(el.id);
    const startX = e.clientX, startY = e.clientY;
    const origX = el.x, origY = el.y;
    const div = pageEl.querySelector(`.ws-element[data-id="${el.id}"]`);

    function onMove(ev) {
      const dx = ev.clientX - startX, dy = ev.clientY - startY;
      el.x = Math.max(0, origX + dx);
      el.y = Math.max(0, origY + dy);
      div.style.left = el.x + "px";
      div.style.top = el.y + "px";
    }
    function onUp() {
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
      apiFetch(`/teacher/worksheets/${worksheetId}/elements/${el.id}`, {
        method: "PATCH",
        body: JSON.stringify({ x: el.x, y: el.y }),
      }).catch((err) => console.error(err));
    }
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  }

  function selectElement(id) {
    selectedId = id;
    renderElements();
    renderInspector();
  }

  function renderInspector() {
    const el = elements.find((e) => e.id === selectedId);
    if (!el) {
      inspector.hidden = true;
      inspectorEmpty.hidden = false;
      return;
    }
    inspector.hidden = false;
    inspectorEmpty.hidden = true;
    inspector.innerHTML = `
      <h3>${el.element_type.replace('_', ' ')}</h3>
      <div class="field"><label>Prompt</label><textarea id="insp-prompt" rows="2">${escapeHtml(el.prompt_text || "")}</textarea></div>
      <div class="field"><label>Points</label><input type="number" id="insp-points" min="0" value="${el.points}"></div>
      <div class="field"><label>Width</label><input type="number" id="insp-width" value="${el.width}"></div>
      <div class="field"><label>Height</label><input type="number" id="insp-height" value="${el.height}"></div>
      <div class="field"><label>Config (JSON)</label><textarea id="insp-config" rows="6">${escapeHtml(JSON.stringify(el.config_json, null, 2))}</textarea></div>
      <button type="button" id="insp-save" class="btn-primary">Save</button>
      <button type="button" id="insp-delete" class="btn-danger">Delete</button>
    `;
    document.getElementById("insp-save").addEventListener("click", () => saveInspector(el));
    document.getElementById("insp-delete").addEventListener("click", () => deleteElement(el));
  }

  function saveInspector(el) {
    let config;
    try {
      config = JSON.parse(document.getElementById("insp-config").value || "{}");
    } catch (e) {
      alert("Config JSON is invalid: " + e.message);
      return;
    }
    const payload = {
      prompt_text: document.getElementById("insp-prompt").value,
      points: Number(document.getElementById("insp-points").value),
      width: Number(document.getElementById("insp-width").value),
      height: Number(document.getElementById("insp-height").value),
      config_json: config,
    };
    apiFetch(`/teacher/worksheets/${worksheetId}/elements/${el.id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }).then((updated) => {
      Object.assign(el, updated);
      renderElements();
      renderInspector();
    }).catch((err) => alert(err.message));
  }

  function deleteElement(el) {
    if (!confirm("Delete this element?")) return;
    apiFetch(`/teacher/worksheets/${worksheetId}/elements/${el.id}`, { method: "DELETE" }).then(() => {
      elements = elements.filter((e) => e.id !== el.id);
      selectedId = null;
      renderElements();
      renderInspector();
    }).catch((err) => alert(err.message));
  }

  function addElement(elementType) {
    apiFetch(`/teacher/worksheets/${worksheetId}/elements`, {
      method: "POST",
      body: JSON.stringify({ element_type: elementType, x: 40, y: 40 }),
    }).then((el) => {
      elements.push(el);
      selectElement(el.id);
    }).catch((err) => alert(err.message));
  }

  pageEl.style.width = pageWidth + "px";
  pageEl.style.height = pageHeight + "px";
  pageEl.addEventListener("click", () => selectElement(null));

  document.querySelectorAll(".ws-add-btn").forEach((btn) => {
    btn.addEventListener("click", () => addElement(btn.dataset.type));
  });

  renderElements();
  renderInspector();
})();
