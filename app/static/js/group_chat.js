(function () {
  const roots = document.querySelectorAll("[data-group-chat-root]");
  if (!roots.length) return;
  const csrf = window.CSRF_TOKEN || "";
  const POLL_INTERVAL_MS = 3000;

  function escapeHtml(s) {
    return (s || "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  function timeLabel(iso) {
    const d = new Date(iso);
    return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  }

  function initChat(root) {
    const groupId = root.dataset.groupId;
    const currentUserId = Number(root.dataset.currentUserId);
    const messagesEl = root.querySelector(".group-chat-messages");
    const form = root.querySelector(".group-chat-form");
    const input = root.querySelector(".group-chat-input");
    const closedNoticeEl = root.querySelector(".group-chat-closed-notice");

    let lastMessageCount = -1;
    let lastClosedState = null;

    function render(messages) {
      if (messages.length === lastMessageCount) return;
      lastMessageCount = messages.length;
      const wasNearBottom =
        messagesEl.scrollHeight - messagesEl.scrollTop - messagesEl.clientHeight < 80;

      if (messages.length === 0) {
        messagesEl.innerHTML = '<div class="chat-empty">No messages yet — say hello to the team!</div>';
        return;
      }
      messagesEl.innerHTML = messages
        .map((m) => {
          const mine = m.student_id === currentUserId;
          const label = m.sender_name + (m.is_teacher ? " (Teacher)" : "");
          return (
            '<div class="chat-bubble-row ' + (mine ? "mine" : "theirs") + '">' +
            '<div class="chat-bubble">' +
            (mine ? "" : '<div class="chat-bubble-sender">' + escapeHtml(label) + "</div>") +
            '<div class="chat-bubble-text">' + escapeHtml(m.body) + "</div>" +
            '<div class="chat-bubble-time">' + timeLabel(m.created_at) + "</div>" +
            "</div></div>"
          );
        })
        .join("");
      if (wasNearBottom) messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function applyClosedState(closed) {
      if (closed === lastClosedState) return;
      lastClosedState = closed;
      input.disabled = closed;
      form.querySelector("button").disabled = closed;
      if (closedNoticeEl) closedNoticeEl.hidden = !closed;
    }

    function refresh() {
      fetch(`/api/groups/${groupId}/messages`)
        .then((r) => r.json())
        .then((data) => {
          render(data.messages);
          applyClosedState(!!data.chat_closed);
        })
        .catch(() => {});
    }

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const body = input.value.trim();
      if (!body) return;
      input.value = "";
      fetch(`/api/groups/${groupId}/messages`, {
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
  }

  roots.forEach(initChat);
})();
