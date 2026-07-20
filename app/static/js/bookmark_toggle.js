(function () {
  const btn = document.getElementById("bookmark-toggle");
  if (!btn) return;
  const csrf = window.CSRF_TOKEN || "";

  btn.addEventListener("click", () => {
    const bookmarkId = btn.dataset.bookmarkId;
    if (bookmarkId) {
      fetch(`/student/bookmarks/${bookmarkId}`, {
        method: "DELETE",
        headers: { "X-CSRFToken": csrf },
      })
        .then((r) => r.json())
        .then(() => {
          btn.dataset.bookmarkId = "";
          btn.textContent = "☆ Bookmark";
        });
    } else {
      fetch("/student/bookmarks", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
        body: JSON.stringify({
          subject_id: Number(btn.dataset.subjectId),
          assignment_id: Number(btn.dataset.assignmentId),
        }),
      })
        .then((r) => r.json())
        .then((data) => {
          btn.dataset.bookmarkId = data.id;
          btn.textContent = "★ Bookmarked";
        });
    }
  });
})();
