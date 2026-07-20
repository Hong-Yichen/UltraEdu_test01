(function () {
  const root = document.getElementById("chat-root");
  if (!root) return;
  const conversationId = root.dataset.conversationId;
  const currentUserId = Number(root.dataset.currentUserId);
  const csrf = window.CSRF_TOKEN || "";
  const POLL_INTERVAL_MS = 3000;

  const messagesEl = document.getElementById("chat-messages");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");

  let lastMessageCount = -1;

  function escapeHtml(s) {
    return (s || "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  function timeLabel(iso) {
    const d = new Date(iso);
    return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  }

  function render(messages) {
    if (messages.length === lastMessageCount) return;
    lastMessageCount = messages.length;
    const wasNearBottom =
      messagesEl.scrollHeight - messagesEl.scrollTop - messagesEl.clientHeight < 80;

    if (messages.length === 0) {
      messagesEl.innerHTML = '<div class="chat-empty">No messages yet — say hello!</div>';
      return;
    }
    messagesEl.innerHTML = messages
      .map((m) => {
        const mine = m.sender_id === currentUserId;
        return (
          '<div class="chat-bubble-row ' + (mine ? "mine" : "theirs") + '">' +
          '<div class="chat-bubble">' +
          '<div class="chat-bubble-text">' + escapeHtml(m.body) + "</div>" +
          '<div class="chat-bubble-time">' + timeLabel(m.created_at) + "</div>" +
          "</div></div>"
        );
      })
      .join("");
    if (wasNearBottom) messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function refresh() {
    fetch(`/api/conversations/${conversationId}/messages`)
      .then((r) => r.json())
      .then((data) => render(data.messages))
      .catch(() => {});
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const body = input.value.trim();
    if (!body) return;
    input.value = "";
    fetch(`/api/conversations/${conversationId}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
      body: JSON.stringify({ body }),
    })
      .then((r) => r.json())
      .then(() => {
        lastMessageCount = -1;
        refresh();
      })
      .catch(() => {});
  });

  refresh();
  messagesEl.scrollTop = messagesEl.scrollHeight;
  setInterval(refresh, POLL_INTERVAL_MS);
})();
