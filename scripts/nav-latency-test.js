// Navigation latency test — paste into browser console at http://localhost:3015
// Logs every page transition with timing.  >500ms = main-thread blocked.
(function measure() {
  var timings = [];
  var navStart = 0;
  var currentPath = location.pathname;

  var origPush = history.pushState.bind(history);
  history.pushState = function () {
    navStart = performance.now();
    return origPush.apply(this, arguments);
  };

  window.addEventListener("popstate", function () {
    navStart = performance.now();
  });

  var main = document.querySelector("main");
  if (!main) return console.warn("[nav] No <main> found");

  var obs = new MutationObserver(function () {
    if (navStart === 0) return;
    var elapsed = performance.now() - navStart;
    var newPath = location.pathname;
    if (newPath === currentPath) return;
    timings.push({ from: currentPath, to: newPath, ms: Math.round(elapsed) });
    currentPath = newPath;

    var label = elapsed < 200 ? "OK" : elapsed < 500 ? "SLOW" : "BLOCKED";
    console.log(
      "[nav] " + label + " " + currentPath + "  " + elapsed.toFixed(0) + "ms" +
      (elapsed > 500 ? " (main-thread blocked >500ms)" : "")
    );
    navStart = 0;
  });

  obs.observe(main, { childList: true, subtree: true });

  console.log("[nav] Active. Click around. measure.report() for summary.");
  window.measure = {
    report: function () {
      console.table(timings);
      var slow = timings.filter(function (t) { return t.ms > 500; });
      if (slow.length) console.warn(slow.length + " blocked:", slow);
      else console.log("All fast (<500ms)");
    }
  };
})();
