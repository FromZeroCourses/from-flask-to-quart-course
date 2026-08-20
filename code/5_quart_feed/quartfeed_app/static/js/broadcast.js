document.addEventListener("DOMContentLoaded", () => {
  const feed = document.getElementById("feed");
  if (!feed) return;

  const es = new EventSource("/sse");

  const escapeHtml = (str) =>
    String(str).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));

  es.addEventListener("post", (e) => {
    const post = JSON.parse(e.data);
    if (feed.querySelector(`[data-post-id="${post.post_id}"]`)) return;

    const card = document.createElement("div");
    card.className = "card mb-3";
    card.setAttribute("data-post-id", post.post_id);
    card.innerHTML = `
      <div class="card-body">
        <a href="/user/${encodeURIComponent(post.author_username)}" class="fw-bold">@${escapeHtml(post.author_username)}</a>
        <p class="mb-1">${escapeHtml(post.message)}</p>
        <a href="${post.permalink}" class="small text-muted">permalink</a>
      </div>`;
    feed.prepend(card);
  });
});
