// Relative-time formatting for <time class="timeago" datetime="..."> elements.
// Zero dependencies: uses the native Intl.RelativeTimeFormat. Timestamps are
// stored as UTC (the datetime attribute carries a UTC offset), so parsing is
// unambiguous. Safe to call repeatedly and on newly-inserted nodes.
(function () {
  "use strict";

  var rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });

  // Ordered largest-first so we pick the coarsest sensible unit.
  var UNITS = [
    ["year", 60 * 60 * 24 * 365],
    ["month", 60 * 60 * 24 * 30],
    ["week", 60 * 60 * 24 * 7],
    ["day", 60 * 60 * 24],
    ["hour", 60 * 60],
    ["minute", 60],
    ["second", 1],
  ];

  // Return a relative-time string like "2 minutes ago" / "in 3 days" for the
  // given ISO timestamp, relative to now.
  function relative(iso) {
    var then = new Date(iso).getTime();
    if (isNaN(then)) return null;

    var diffSeconds = (then - Date.now()) / 1000; // negative = in the past
    var abs = Math.abs(diffSeconds);

    if (abs < 45) return rtf.format(0, "second"); // "now" / "just now"

    for (var i = 0; i < UNITS.length; i++) {
      var unit = UNITS[i][0];
      var secondsInUnit = UNITS[i][1];
      if (abs >= secondsInUnit) {
        var value = Math.round(diffSeconds / secondsInUnit);
        return rtf.format(value, unit);
      }
    }
    return rtf.format(0, "second");
  }

  // Format every <time class="timeago"> under `root` (default: whole document).
  function formatTimeago(root) {
    root = root || document;
    var scope = root.querySelectorAll ? root : document;
    var nodes = scope.querySelectorAll("time.timeago");
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      var iso = el.getAttribute("datetime");
      if (!iso) continue;
      var text = relative(iso);
      if (text) el.textContent = text;
      el.title = new Date(iso).toLocaleString();
    }
  }

  window.formatTimeago = formatTimeago;

  document.addEventListener("DOMContentLoaded", function () {
    formatTimeago(document);
    // Keep them fresh (e.g. "just now" -> "1 minute ago") without a reload.
    setInterval(function () {
      formatTimeago(document);
    }, 60000);
  });
})();
