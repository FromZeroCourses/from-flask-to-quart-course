document.addEventListener("DOMContentLoaded", () => {
  const feed = document.getElementById("feed");
  if (!feed) return;

  const es = new EventSource("/sse");

  // Reuse the CSRF token already rendered on the page (from the post form)
  // so dynamically-created comment forms for posts that arrived over
  // SSE still submit successfully.
  const csrfInput = document.querySelector('#post-form input[name="csrf_token"]');
  const csrfToken = csrfInput ? csrfInput.value : "";

  const escapeHtml = (str) =>
    String(str).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));

  const formatWhen = (iso) => {
    const d = new Date(iso);
    const month = d.toLocaleString("en-US", { month: "short" });
    const pad = (n) => String(n).padStart(2, "0");
    return `${month} ${pad(d.getDate())}, ${d.getFullYear()} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  };

  es.addEventListener("post", (e) => {
    const post = JSON.parse(e.data);
    if (feed.querySelector(`[data-post-id="${post.post_id}"]`)) return;

    const card = document.createElement("div");
    card.className = "card mb-3";
    card.setAttribute("data-post-id", post.post_id);
    card.innerHTML = `
      <div class="card-body">
        <div class="d-flex">
          <img src="${post.avatar_url}" class="rounded-circle me-2 flex-shrink-0" width="40" height="40" alt="avatar">
          <div class="flex-grow-1">
            <a href="/user/${encodeURIComponent(post.author_username)}" class="fw-bold">@${escapeHtml(post.author_username)}</a>
            ${(post.reason_type === "comment" && post.reason_username)
              ? ` <span class="text-muted small ms-1">(<a href="/user/${encodeURIComponent(post.reason_username)}">${escapeHtml(post.reason_username)}</a> commented on this)</span>`
              : ""}
            <p class="mb-1">${escapeHtml(post.message)}</p>
            ${(post.images && post.images.length)
              ? `<div class="d-flex gap-2 mb-2">${post.images
                  .map((im) => `<img src="${im.url}" alt="post image" style="height:200px;width:auto;border-radius:6px;">`)
                  .join("")}</div>`
              : ""}
            <a href="${post.permalink}" class="small text-muted">${formatWhen(post.created)}</a>
            <div class="comments mt-2"></div>
            <form method="POST" action="/comment/${post.post_id}" class="comment-form mt-2 d-flex">
              <input type="hidden" name="csrf_token" value="${csrfToken}">
              <input type="text" name="comment" class="form-control form-control-sm me-2" placeholder="Add a comment...">
              <button type="submit" class="btn btn-sm btn-outline-secondary">Send</button>
            </form>
          </div>
        </div>
      </div>`;
    feed.prepend(card);
  });

  es.addEventListener("comment", (e) => {
    const comment = JSON.parse(e.data);
    const card = feed.querySelector(`[data-post-id="${comment.post_id}"]`);
    if (!card) return;

    const commentsDiv = card.querySelector(".comments");
    const commentEl = document.createElement("div");
    commentEl.className = "comment small";
    commentEl.innerHTML = `<span class="comment-bubble">💬</span> ${escapeHtml(comment.comment)} - <a href="/user/${encodeURIComponent(comment.author_username)}" class="comment-author">@${escapeHtml(comment.author_username)}</a>`;
    commentsDiv.appendChild(commentEl);
  });
});
