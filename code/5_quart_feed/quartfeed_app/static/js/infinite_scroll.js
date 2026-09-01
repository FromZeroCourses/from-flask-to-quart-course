// Infinite-scroll pagination for the QuartFeed home page.
// Watches #feed-sentinel; when it scrolls into view, fetches the next page of
// feed cards from /feed?offset=N and appends them to #feed. Vanilla JS.
document.addEventListener("DOMContentLoaded", function () {
  var feed = document.getElementById("feed");
  var sentinel = document.getElementById("feed-sentinel");
  // Only run on pages that have both (i.e. the home feed).
  if (!feed || !sentinel) return;

  var loading = false;
  var exhausted = false;

  function currentCount() {
    return feed.querySelectorAll(":scope > [data-post-id]").length;
  }

  function appendCards(html) {
    var temp = document.createElement("div");
    temp.innerHTML = html;

    var added = document.createDocumentFragment();
    var anyAdded = false;
    var cards = temp.querySelectorAll("[data-post-id]");
    for (var i = 0; i < cards.length; i++) {
      var card = cards[i];
      var id = card.getAttribute("data-post-id");
      // Dedupe: skip any card already present in the feed.
      if (feed.querySelector('[data-post-id="' + id + '"]')) continue;
      added.appendChild(card);
      anyAdded = true;
    }

    if (anyAdded) {
      feed.appendChild(added);
      if (window.formatTimeago) window.formatTimeago(feed);
    }
  }

  function loadMore() {
    if (loading || exhausted) return;
    loading = true;

    var offset = currentCount();
    fetch("/feed?offset=" + offset, { headers: { "X-Requested-With": "fetch" } })
      .then(function (resp) {
        return resp.text();
      })
      .then(function (html) {
        if (!html || html.trim() === "") {
          exhausted = true;
          observer.disconnect();
          return;
        }
        appendCards(html);
      })
      .catch(function () {
        // Network hiccup: allow a later retry rather than getting stuck.
      })
      .finally(function () {
        loading = false;
      });
  }

  var observer = new IntersectionObserver(
    function (entries) {
      for (var i = 0; i < entries.length; i++) {
        if (entries[i].isIntersecting) {
          loadMore();
        }
      }
    },
    { rootMargin: "200px" }
  );

  observer.observe(sentinel);
});
