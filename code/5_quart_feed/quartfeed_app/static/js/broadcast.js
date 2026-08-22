document.addEventListener("DOMContentLoaded", () => {
  const feed = document.getElementById("feed");
  if (!feed) return;

  const es = new EventSource("/sse");

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
            <p class="mb-1">${escapeHtml(post.message)}</p>
            ${(post.images && post.images.length)
              ? `<div class="d-flex gap-2 mb-2">${post.images
                  .map((im) => `<img src="${im.url}" alt="post image" style="height:200px;width:auto;border-radius:6px;">`)
                  .join("")}</div>`
              : ""}
            <a href="${post.permalink}" class="small text-muted">${formatWhen(post.created)}</a>
          </div>
        </div>
      </div>`;
    feed.prepend(card);
  });
});
