(function () {
  const POLL_INTERVAL_MS = 20000;
  const bell = document.getElementById("notif-bell");
  const countEl = document.getElementById("notif-count");
  const panel = document.getElementById("notif-panel");
  if (!bell || !panel) return;

  function renderPanel(notifications) {
    if (notifications.length === 0) {
      panel.innerHTML = '<div class="notif-empty">No notifications yet.</div>';
      return;
    }
    panel.innerHTML = notifications
      .map(function (n) {
        const cls = n.is_read ? "notif-item" : "notif-item unread";
        return (
          '<div class="' + cls + '" data-id="' + n.id + '">' +
          "<strong>" + n.title + "</strong>" +
          (n.body ? "<div>" + n.body + "</div>" : "") +
          "</div>"
        );
      })
      .join("");
  }

  function refresh() {
    fetch("/api/notifications")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.unread_count > 0) {
          countEl.textContent = data.unread_count;
          countEl.hidden = false;
        } else {
          countEl.hidden = true;
        }
        renderPanel(data.notifications);
      })
      .catch(function () {});
  }

  bell.addEventListener("click", function () {
    const willShow = panel.hidden;
    panel.hidden = !panel.hidden;
    if (willShow) {
      refresh();
      fetch("/api/notifications/read-all", {
        method: "POST",
        headers: { "X-CSRFToken": window.CSRF_TOKEN || "" },
      }).then(refresh);
    }
  });

  document.addEventListener("click", function (e) {
    if (!panel.hidden && !panel.contains(e.target) && e.target !== bell) {
      panel.hidden = true;
    }
  });

  refresh();
  setInterval(refresh, POLL_INTERVAL_MS);
})();
