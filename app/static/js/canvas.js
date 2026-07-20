/* UltraEduCanvas — handwriting/drawing engine.
   Modes: "readonly" (view only), "edit" (single editable base layer),
   "overlay" (base layer read-only + a second editable annotation layer on top). */
(function (global) {
  const SYNC_DEBOUNCE_MS = 2000;
  const SHAPE_TOOLS = ["line", "rectangle", "circle", "arrow"];
  const CSRF = () => window.CSRF_TOKEN || "";

  function jsonFetch(url, opts) {
    opts = opts || {};
    opts.headers = Object.assign(
      { "Content-Type": "application/json", "X-CSRFToken": CSRF() },
      opts.headers || {}
    );
    return fetch(url, opts).then(function (r) {
      if (!r.ok) return r.json().then(function (b) { throw new Error(b.description || r.statusText); });
      return r.json();
    });
  }

  function drawArrowHead(ctx, a, b, width) {
    const angle = Math.atan2(b.y - a.y, b.x - a.x);
    const headLen = Math.max(8, width * 3);
    ctx.beginPath();
    ctx.moveTo(b.x, b.y);
    ctx.lineTo(b.x - headLen * Math.cos(angle - Math.PI / 6), b.y - headLen * Math.sin(angle - Math.PI / 6));
    ctx.moveTo(b.x, b.y);
    ctx.lineTo(b.x - headLen * Math.cos(angle + Math.PI / 6), b.y - headLen * Math.sin(angle + Math.PI / 6));
    ctx.stroke();
  }

  function drawStroke(ctx, stroke) {
    const pts = stroke.points;
    if (!pts || pts.length === 0) return;
    ctx.save();
    ctx.globalAlpha = stroke.opacity != null ? stroke.opacity : 1;
    ctx.strokeStyle = stroke.color;
    ctx.lineWidth = stroke.width || 2;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    if (stroke.tool === "highlighter") ctx.globalAlpha = Math.min(ctx.globalAlpha, 0.35);

    if (SHAPE_TOOLS.includes(stroke.tool)) {
      const a = pts[0], b = pts[pts.length - 1];
      if (stroke.tool === "rectangle") {
        ctx.strokeRect(Math.min(a.x, b.x), Math.min(a.y, b.y), Math.abs(b.x - a.x), Math.abs(b.y - a.y));
      } else if (stroke.tool === "circle") {
        const cx = (a.x + b.x) / 2, cy = (a.y + b.y) / 2;
        const rx = Math.max(Math.abs(b.x - a.x) / 2, 1), ry = Math.max(Math.abs(b.y - a.y) / 2, 1);
        ctx.beginPath();
        ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
        ctx.stroke();
      } else {
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.stroke();
        if (stroke.tool === "arrow") drawArrowHead(ctx, a, b, stroke.width || 2);
      }
    } else {
      ctx.beginPath();
      ctx.moveTo(pts[0].x, pts[0].y);
      for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
      ctx.stroke();
    }
    ctx.restore();
  }

  function pointFromEvent(e, canvas) {
    const rect = canvas.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  }

  function distanceToSegment(p, a, b) {
    const dx = b.x - a.x, dy = b.y - a.y;
    const lenSq = dx * dx + dy * dy;
    let t = lenSq === 0 ? 0 : ((p.x - a.x) * dx + (p.y - a.y) * dy) / lenSq;
    t = Math.max(0, Math.min(1, t));
    const projX = a.x + t * dx, projY = a.y + t * dy;
    return Math.hypot(p.x - projX, p.y - projY);
  }

  function strokeHit(stroke, point, threshold) {
    const pts = stroke.points;
    for (let i = 1; i < pts.length; i++) {
      if (distanceToSegment(point, pts[i - 1], pts[i]) <= threshold) return true;
    }
    return pts.length === 1 && Math.hypot(point.x - pts[0].x, point.y - pts[0].y) <= threshold;
  }

  class CanvasLayer {
    constructor(canvasEl, editable, layerName, session) {
      this.canvas = canvasEl;
      this.ctx = canvasEl.getContext("2d");
      this.editable = editable;
      this.layerName = layerName;
      this.session = session;
      this.strokes = [];
      this.currentStroke = null;
      this.startedAt = 0;
      if (editable) this._bindEvents();
    }

    setStrokes(strokes) {
      this.strokes = strokes;
      this.render();
    }

    render() {
      const ctx = this.ctx;
      ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
      for (const s of this.strokes) drawStroke(ctx, s);
      if (this.currentStroke) drawStroke(ctx, this.currentStroke);
    }

    _bindEvents() {
      const canvas = this.canvas;
      canvas.style.touchAction = "none";
      canvas.addEventListener("pointerdown", (e) => this._onDown(e));
      canvas.addEventListener("pointermove", (e) => this._onMove(e));
      canvas.addEventListener("pointerup", (e) => this._onUp(e));
      canvas.addEventListener("pointercancel", (e) => this._onUp(e));
      canvas.addEventListener("pointerleave", (e) => {
        if (this.currentStroke) this._onUp(e);
      });
    }

    _onDown(e) {
      const tool = this.session.currentTool;
      const point = pointFromEvent(e, this.canvas);
      if (tool === "sticky") {
        this.session._placeStickyNote(this.layerName, point);
        return;
      }
      this.startedAt = performance.now();
      if (tool === "eraser") {
        this._eraseAt(point);
        this.canvas.setPointerCapture(e.pointerId);
        this._erasing = true;
        return;
      }
      this.currentStroke = {
        layer: this.layerName,
        tool: tool,
        color: this.session.currentColor,
        width: this.session.currentWidth,
        opacity: tool === "highlighter" ? 0.35 : 1,
        points: SHAPE_TOOLS.includes(tool)
          ? [{ x: point.x, y: point.y, t: 0 }, { x: point.x, y: point.y, t: 0 }]
          : [{ x: point.x, y: point.y, t: 0 }],
      };
      this.canvas.setPointerCapture(e.pointerId);
    }

    _onMove(e) {
      if (this._erasing) {
        this._eraseAt(pointFromEvent(e, this.canvas));
        return;
      }
      if (!this.currentStroke) return;
      const point = pointFromEvent(e, this.canvas);
      const t = Math.round(performance.now() - this.startedAt);
      if (SHAPE_TOOLS.includes(this.currentStroke.tool)) {
        this.currentStroke.points[1] = { x: point.x, y: point.y, t: t };
      } else {
        this.currentStroke.points.push({ x: point.x, y: point.y, t: t });
      }
      this.render();
    }

    _onUp(e) {
      if (this._erasing) {
        this._erasing = false;
        return;
      }
      if (!this.currentStroke) return;
      if (this.currentStroke.points.length > 1) {
        this.strokes.push(this.currentStroke);
        this.session._queueNewStroke(this.currentStroke);
      }
      this.currentStroke = null;
      this.render();
    }

    _eraseAt(point) {
      const threshold = 10;
      const remaining = [];
      let erasedAny = false;
      for (const s of this.strokes) {
        if (s.layer === this.layerName && strokeHit(s, point, threshold)) {
          erasedAny = true;
          if (s.id) {
            this.session._queueDeletedStroke(s.id);
          } else {
            this.session._discardUnsyncedStroke(s);
          }
        } else {
          remaining.push(s);
        }
      }
      if (erasedAny) {
        this.strokes = remaining;
        this.render();
      }
    }
  }

  class CanvasSession {
    constructor(container, opts) {
      this.container = container;
      this.documentId = opts.documentId;
      this.mode = opts.mode || "edit";
      this.width = opts.width || 800;
      this.height = opts.height || 400;
      this.currentTool = "pen";
      this.currentColor = "#1a1a1a";
      this.currentWidth = 2.5;
      this._pendingNew = [];
      this._pendingDeleted = [];
      this._syncTimer = null;

      this._buildDom();
      this._load();
    }

    _buildDom() {
      this.container.classList.add("uec-container");
      this.container.style.width = this.width + "px";
      this.container.style.height = this.height + "px";

      this.baseCanvas = document.createElement("canvas");
      this.baseCanvas.width = this.width;
      this.baseCanvas.height = this.height;
      this.baseCanvas.className = "uec-layer uec-layer-base";
      this.container.appendChild(this.baseCanvas);

      this.baseLayer = new CanvasLayer(
        this.baseCanvas,
        this.mode === "edit",
        "base",
        this
      );

      if (this.mode === "overlay" || this.mode === "readonly") {
        this.annotationCanvas = document.createElement("canvas");
        this.annotationCanvas.width = this.width;
        this.annotationCanvas.height = this.height;
        this.annotationCanvas.className = "uec-layer uec-layer-annotation";
        this.container.appendChild(this.annotationCanvas);
        this.annotationLayer = new CanvasLayer(
          this.annotationCanvas,
          this.mode === "overlay",
          "annotation",
          this
        );
      }

      if (this.mode !== "readonly") {
        this.toolbar = this._buildToolbar();
        this.container.parentElement.insertBefore(this.toolbar, this.container);
      }
    }

    _buildToolbar() {
      const bar = document.createElement("div");
      bar.className = "uec-toolbar";

      const buttons = [
        this._toolButton("pen", "Pen"),
        this._toolButton("highlighter", "Highlighter"),
        this._toolButton("eraser", "Eraser"),
        this._toolButton("line", "Line"),
        this._toolButton("rectangle", "Rectangle"),
        this._toolButton("circle", "Circle"),
        this._toolButton("arrow", "Arrow"),
        this._toolButton("sticky", "Sticky Note"),
      ];
      buttons.forEach((b) => bar.appendChild(b));

      const colorInput = document.createElement("input");
      colorInput.type = "color";
      colorInput.value = this.currentColor;
      colorInput.className = "uec-color";
      colorInput.addEventListener("input", () => { this.currentColor = colorInput.value; });
      bar.appendChild(colorInput);

      const widthInput = document.createElement("input");
      widthInput.type = "range";
      widthInput.min = "1";
      widthInput.max = "12";
      widthInput.value = String(this.currentWidth);
      widthInput.className = "uec-width";
      widthInput.addEventListener("input", () => { this.currentWidth = Number(widthInput.value); });
      bar.appendChild(widthInput);

      const saveBtn = document.createElement("button");
      saveBtn.type = "button";
      saveBtn.textContent = "Save";
      saveBtn.className = "uec-save";
      saveBtn.addEventListener("click", () => this._flushSync());
      bar.appendChild(saveBtn);

      this._toolButtons = buttons;
      this._setActiveTool(buttons[0]);
      return bar;
    }

    _toolButton(tool, label) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = label;
      btn.className = "uec-tool-btn";
      btn.addEventListener("click", () => {
        this.currentTool = tool;
        this._setActiveTool(btn);
      });
      return btn;
    }

    _setActiveTool(activeBtn) {
      if (!this._toolButtons) return;
      for (const b of this._toolButtons) b.classList.toggle("active", b === activeBtn);
    }

    _placeStickyNote(layer, point) {
      const editor = document.createElement("div");
      editor.className = "uec-sticky-editor";
      editor.style.left = point.x + "px";
      editor.style.top = point.y + "px";

      const textarea = document.createElement("textarea");
      textarea.placeholder = "Write a note…";
      editor.appendChild(textarea);

      const actions = document.createElement("div");
      actions.className = "uec-sticky-editor-actions";
      const addBtn = document.createElement("button");
      addBtn.type = "button";
      addBtn.textContent = "Add";
      const cancelBtn = document.createElement("button");
      cancelBtn.type = "button";
      cancelBtn.textContent = "Cancel";
      actions.appendChild(addBtn);
      actions.appendChild(cancelBtn);
      editor.appendChild(actions);

      this.container.appendChild(editor);
      textarea.focus();

      cancelBtn.addEventListener("click", () => editor.remove());
      addBtn.addEventListener("click", () => {
        const text = textarea.value.trim();
        editor.remove();
        if (!text) return;
        const note = { x: point.x, y: point.y, width: 170, height: 110, text: text, color: "#fff3b0", layer: layer };
        jsonFetch(`/api/canvas/documents/${this.documentId}/sync`, {
          method: "POST",
          body: JSON.stringify({ new_strokes: [], deleted_stroke_ids: [], sticky_notes: [note] }),
        })
          .then((data) => {
            const id = data.created_sticky_note_ids && data.created_sticky_note_ids[0];
            this._renderStickyNote(Object.assign({ id: id }, note));
          })
          .catch((err) => console.error("sticky note save failed", err));
      });
    }

    _renderStickyNote(note) {
      const el = document.createElement("div");
      el.className = "uec-sticky-note";
      el.style.left = note.x + "px";
      el.style.top = note.y + "px";
      el.style.width = note.width + "px";
      el.style.minHeight = note.height + "px";
      el.style.background = note.color || "#fff3b0";
      el.textContent = note.text;
      this.container.appendChild(el);
    }

    _load() {
      jsonFetch(`/api/canvas/documents/${this.documentId}`)
        .then((data) => {
          const baseStrokes = data.strokes.filter((s) => s.layer === "base");
          this.baseLayer.setStrokes(baseStrokes);
          if (this.annotationLayer) {
            const annStrokes = data.strokes.filter((s) => s.layer === "annotation");
            this.annotationLayer.setStrokes(annStrokes);
          }
          (data.sticky_notes || []).forEach((n) => this._renderStickyNote(n));
        })
        .catch((err) => console.error("UltraEduCanvas load failed", err));
    }

    _queueNewStroke(stroke) {
      this._pendingNew.push(stroke);
      this._scheduleSync();
    }

    _queueDeletedStroke(id) {
      this._pendingDeleted.push(id);
      this._scheduleSync();
    }

    _discardUnsyncedStroke(strokeRef) {
      const idx = this._pendingNew.indexOf(strokeRef);
      if (idx !== -1) this._pendingNew.splice(idx, 1);
    }

    _scheduleSync() {
      if (this._syncTimer) clearTimeout(this._syncTimer);
      this._syncTimer = setTimeout(() => this._flushSync(), SYNC_DEBOUNCE_MS);
    }

    _flushSync() {
      if (this._syncTimer) {
        clearTimeout(this._syncTimer);
        this._syncTimer = null;
      }
      if (this._pendingNew.length === 0 && this._pendingDeleted.length === 0) return;
      const payload = {
        new_strokes: this._pendingNew,
        deleted_stroke_ids: this._pendingDeleted,
        sticky_notes: [],
      };
      this._pendingNew = [];
      this._pendingDeleted = [];
      jsonFetch(`/api/canvas/documents/${this.documentId}/sync`, {
        method: "POST",
        body: JSON.stringify(payload),
      }).catch((err) => console.error("UltraEduCanvas sync failed", err));
    }
  }

  global.UltraEduCanvas = {
    mount(container, opts) {
      return new CanvasSession(container, opts);
    },
  };
})(window);
