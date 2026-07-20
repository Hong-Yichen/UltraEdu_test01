(function () {
  const timerEl = document.getElementById("exam-timer");
  if (!timerEl) return;
  const dueDate = new Date(timerEl.dataset.dueDate);
  const csrf = window.CSRF_TOKEN || "";
  let submitted = false;

  function format(totalSeconds) {
    const s = Math.max(0, totalSeconds);
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    const mm = String(m).padStart(2, "0");
    const ss = String(sec).padStart(2, "0");
    return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
  }

  function autoSubmit() {
    if (submitted) return;
    submitted = true;
    timerEl.textContent = "Time's up — submitting…";
    const form = document.querySelector('form[action*="/submit"]');
    if (!form) return;
    fetch(form.action, {
      method: "POST",
      headers: { "X-CSRFToken": csrf },
      body: new FormData(form),
    }).then(() => {
      window.location.reload();
    });
  }

  function tick() {
    if (submitted) return;
    const diffSeconds = Math.floor((dueDate.getTime() - Date.now()) / 1000);
    if (diffSeconds <= 0) {
      autoSubmit();
      return;
    }
    timerEl.textContent = format(diffSeconds);
    if (diffSeconds <= 60) {
      timerEl.classList.add("exam-timer-critical");
    }
  }

  tick();
  setInterval(tick, 1000);
})();
