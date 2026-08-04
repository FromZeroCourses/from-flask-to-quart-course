document.addEventListener("DOMContentLoaded", () => {
  const feed = document.getElementById("feed");
  const sentinel = document.getElementById("feed-sentinel");
  if (!feed || !sentinel) return;

  let loading = false;
  let done = false;

  const observer = new IntersectionObserver(async (entries) => {
    if (!entries[0].isIntersecting || loading || done) return;
    loading = true;

    const offset = feed.querySelectorAll("[data-post-id]").length;
    const res = await fetch(`/feed?offset=${offset}`);
    const html = (await res.text()).trim();

    if (!html) {
      done = true;
      observer.disconnect();
    } else {
      feed.insertAdjacentHTML("beforeend", html);
    }

    loading = false;
  }, { rootMargin: "200px" });

  observer.observe(sentinel);
});
