(function () {
  const POLL_INTERVAL_MS = 15000;
  const countEl = document.getElementById("chat-count");
  if (!countEl) return;

  function refresh() {
    fetch("/api/conversations/unread-count")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.unread_count > 0) {
          countEl.textContent = data.unread_count;
          countEl.hidden = false;
        } else {
          countEl.hidden = true;
        }
      })
      .catch(function () {});
  }

  refresh();
  setInterval(refresh, POLL_INTERVAL_MS);
})();
