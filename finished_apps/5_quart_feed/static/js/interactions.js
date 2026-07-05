// FriendFeed-style feed interactions: expandable likes/comments and URL
// linkifying. Exposes window.linkify / window.renderLikesLine so the SSE client
// (broadcast.js) renders dynamically-inserted cards identically to the server.
(function () {
  "use strict";

  function esc(str) {
    return String(str).replace(/[&<>"']/g, function (c) {
      return {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      }[c];
    });
  }

  // Escape text and turn bare http(s) URLs into truncated links.
  function linkify(text, maxLen) {
    maxLen = maxLen || 40;
    var re = /(https?:\/\/[^\s<]+)/g;
    var out = "";
    var last = 0;
    var m;
    while ((m = re.exec(text)) !== null) {
      out += esc(text.slice(last, m.index));
      var url = m[0];
      var display = url.length <= maxLen ? url : url.slice(0, maxLen - 1) + "…";
      out +=
        '<a href="' + esc(url) + '" target="_blank" rel="noopener">' +
        esc(display) +
        "</a>";
      last = m.index + url.length;
    }
    out += esc(text.slice(last));
    return out;
  }

  // Build the "A, B and C liked this" line (mirrors helpers.likes_line).
  function renderLikesLine(likers, head, collapseOver) {
    head = head || 3;
    collapseOver = collapseOver || 5;
    if (!likers || !likers.length) return "";
    var names = likers.map(esc);
    var emoji = '<span class="likes-emoji">🙂</span> ';
    if (names.length <= collapseOver) {
      var body =
        names.length === 1
          ? names[0] + " liked this"
          : names.slice(0, -1).join(", ") +
            " and " +
            names[names.length - 1] +
            " liked this";
      return emoji + body;
    }
    var shown = names.slice(0, head).join(", ");
    var others = names.length - head;
    var full = names.join(", ");
    return (
      emoji +
      '<span class="likers-collapsed">' + shown + " and " +
      '<a href="#" class="likers-more">' + others + " other people</a> liked this</span>" +
      '<span class="likers-full d-none">' + full + " liked this</span>"
    );
  }

  window.linkify = linkify;
  window.renderLikesLine = renderLikesLine;

  // Expanders: "N other people" (likes) and "N more comments" (comments).
  document.addEventListener("click", function (e) {
    var more = e.target.closest(".likers-more");
    if (more) {
      e.preventDefault();
      var likes = more.closest(".likes");
      likes.querySelector(".likers-collapsed").classList.add("d-none");
      likes.querySelector(".likers-full").classList.remove("d-none");
      return;
    }
    var cmore = e.target.closest(".comments-more");
    if (cmore) {
      e.preventDefault();
      var comments = cmore.closest(".comments");
      var hidden = comments.querySelector(".comments-hidden");
      if (hidden) hidden.classList.remove("d-none");
      cmore.closest(".comments-more-wrap").classList.add("d-none");
    }
  });
})();
