// Vanilla JS SSE client for the QuartFeed home page.
// Listens for "post" / "comment" / "like" events and renders them into the
// #feed container using template literals (no framework).
document.addEventListener("DOMContentLoaded", () => {
  const feed = document.getElementById("feed");
  if (!feed) return;

  const es = new EventSource("/sse");

  // Reuse the CSRF token already rendered on the page (from the post form)
  // so dynamically-created comment/like forms for posts that arrived over
  // SSE still submit successfully.
  const csrfInput = document.querySelector('#post-form input[name="csrf_token"]');
  const csrfToken = csrfInput ? csrfInput.value : "";

  const escapeHtml = (str) =>
    String(str).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[c]));

  es.addEventListener("post", (e) => {
    const post = JSON.parse(e.data);
    if (feed.querySelector(`[data-post-id="${post.post_id}"]`)) return;

    const card = document.createElement("div");
    card.className = "card mb-3";
    card.setAttribute("data-post-id", post.post_id);
    card.innerHTML = `
      <div class="card-body">
        <div class="d-flex align-items-center mb-2">
          <img src="${post.avatar_url}" class="rounded-circle me-2" width="40" height="40" alt="avatar" onerror="this.onerror=null;this.src='/static/default_profile.png';">
          <a href="/user/${encodeURIComponent(post.author_username)}">@${escapeHtml(post.author_username)}</a>
        </div>
        <p class="mb-1">${window.linkify ? window.linkify(post.message) : escapeHtml(post.message)}</p>
        ${(post.images && post.images.length)
          ? `<div class="d-flex gap-2 mb-2" style="overflow-x: auto;">${post.images
              .map((im) => `<img src="${im.url}" alt="post image" style="height:200px;width:auto;border-radius:6px;">`)
              .join("")}</div>`
          : ""}
        <div class="ff-meta small text-muted mt-1">
          <a href="${post.permalink}" class="ff-meta-time"><time class="timeago" datetime="${post.created}">${new Date(post.created).toLocaleString()}</time></a>
          - <a href="#" class="ff-comment">Comment</a>
          - <form method="POST" action="/like/${post.post_id}" class="d-inline"><input type="hidden" name="csrf_token" value="${csrfToken}"><button type="submit" class="ff-action-link">Like</button></form>
          - <a href="#" class="ff-hide">Hide</a>
        </div>

        <div class="likes small text-muted mt-1"></div>

        <div class="comments mt-2"></div>

        <form method="POST" action="/comment/${post.post_id}" class="comment-form mt-2 d-flex d-none">
          <input type="hidden" name="csrf_token" value="${csrfToken}">
          <input type="text" name="comment" class="form-control form-control-sm me-2" placeholder="Add a comment...">
          <button type="submit" class="btn btn-sm btn-outline-secondary">Send</button>
        </form>
      </div>
    `;
    feed.prepend(card);
    if (window.formatTimeago) window.formatTimeago(card);
  });

  es.addEventListener("comment", (e) => {
    const comment = JSON.parse(e.data);
    const card = feed.querySelector(`[data-post-id="${comment.post_id}"]`);
    if (!card) return;

    const commentsDiv = card.querySelector(".comments");
    const commentEl = document.createElement("div");
    commentEl.className = "comment small";
    commentEl.innerHTML = `<span class="comment-bubble">💬</span> ${window.linkify ? window.linkify(comment.comment) : escapeHtml(comment.comment)} - <a href="/user/${encodeURIComponent(comment.author_username)}" class="comment-author">@${escapeHtml(comment.author_username)}</a>`;
    commentsDiv.appendChild(commentEl);
  });

  es.addEventListener("like", (e) => {
    const like = JSON.parse(e.data);
    const card = feed.querySelector(`[data-post-id="${like.post_id}"]`);
    if (!card) return;

    const likesDiv = card.querySelector(".likes");
    if (likesDiv && window.renderLikesLine)
      likesDiv.innerHTML = window.renderLikesLine(like.likers || []);
  });
});
