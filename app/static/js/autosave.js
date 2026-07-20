(function () {
  const root = document.getElementById("ws-take-root");
  if (!root) return;
  const assignmentId = root.dataset.assignmentId;
  const storybookId = root.dataset.storybookId;
  const csrf = window.CSRF_TOKEN || "";

  function postJson(url, body) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
      body: JSON.stringify(body),
    });
  }

  function answerUrl(elementId) {
    if (assignmentId) return `/student/assignments/${assignmentId}/answers/${elementId}`;
    return `/student/storybooks/${storybookId}/answers/${elementId}`;
  }

  function saveAnswer(elementId, answerJson) {
    postJson(answerUrl(elementId), { answer_json: answerJson }).catch((err) =>
      console.error("autosave failed", err)
    );
  }

  function collectMcq(elementId) {
    const checked = root.querySelector(`input[data-kind="mcq"][data-element-id="${elementId}"]:checked`);
    return { selected_option_id: checked ? checked.value : null };
  }

  function collectMatching(elementId) {
    const selects = root.querySelectorAll(`select[data-kind="matching"][data-element-id="${elementId}"]`);
    const pairs = {};
    selects.forEach((s) => { if (s.value) pairs[s.dataset.leftId] = s.value; });
    return { pairs };
  }

  root.querySelectorAll('[data-kind="mcq"]').forEach((el) => {
    el.addEventListener("change", () => saveAnswer(el.dataset.elementId, collectMcq(el.dataset.elementId)));
  });
  root.querySelectorAll('[data-kind="matching"]').forEach((el) => {
    el.addEventListener("change", () => saveAnswer(el.dataset.elementId, collectMatching(el.dataset.elementId)));
  });

  root.querySelectorAll('[data-kind="text_highlight"]').forEach((container) => {
    if (container.dataset.mode !== "take") return;
    const elementId = container.dataset.elementId;
    container.querySelectorAll(".ws-sentence").forEach((span) => {
      span.addEventListener("click", () => {
        span.classList.toggle("highlighted");
        const ids = Array.from(container.querySelectorAll(".ws-sentence.highlighted")).map(
          (s) => s.dataset.sentenceId
        );
        saveAnswer(elementId, { highlighted_sentence_ids: ids });
      });
    });
  });

  root.querySelectorAll("[data-image-upload]").forEach((input) => {
    input.addEventListener("change", () => {
      const file = input.files[0];
      if (!file) return;
      const formData = new FormData();
      formData.append("element_id", input.dataset.elementId);
      formData.append("file", file);
      fetch(`/student/assignments/${assignmentId}/upload`, {
        method: "POST",
        headers: { "X-CSRFToken": csrf },
        body: formData,
      })
        .then((r) => r.json())
        .then(() => { input.nextElementSibling && input.nextElementSibling.remove(); })
        .catch((err) => console.error("image upload failed", err));
    });
  });

  root.querySelectorAll("[data-ai-hint]").forEach((container) => {
    const btn = container.querySelector(".ws-ai-hint-btn");
    const textEl = container.querySelector(".ws-ai-hint-text");
    btn.addEventListener("click", () => {
      btn.disabled = true;
      btn.textContent = "Thinking…";
      postJson("/api/ai/hint", {
        assignment_id: container.dataset.assignmentId ? Number(container.dataset.assignmentId) : undefined,
        storybook_id: container.dataset.storybookId ? Number(container.dataset.storybookId) : undefined,
        worksheet_element_id: Number(container.dataset.elementId),
      })
        .then((r) => r.json())
        .then((data) => {
          textEl.textContent = data.hint;
          textEl.hidden = false;
          btn.textContent = "🤖 Get another hint";
          btn.disabled = false;
        })
        .catch(() => {
          btn.textContent = "🤖 Get a hint";
          btn.disabled = false;
        });
    });
  });

  root.querySelectorAll("[data-canvas-mount]").forEach((mount) => {
    UltraEduCanvas.mount(mount, {
      documentId: Number(mount.dataset.documentId),
      mode: mount.dataset.canvasMode,
      width: Number(mount.dataset.width),
      height: Number(mount.dataset.height),
    });
  });
})();
