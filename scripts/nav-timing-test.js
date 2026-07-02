/**
 * Clean navigation test — clicks each nav link once, skips current page.
 * Paste into F12 Console, run navTest.run()
 */
(function() {
  var links = [];
  document.querySelectorAll("nav a").forEach(function(a) {
    var href = a.getAttribute("href") || "";
    if (href && href !== "#" && href !== location.pathname) {
      links.push({ el: a, path: href });
    }
  });

  if (!links.length) { console.warn("No links to test"); return; }

  var results = [];
  var i = 0;

  function next() {
    if (i >= links.length) {
      console.table(results);
      var slow = results.filter(function(r) { return r.ms > 200; });
      console.log(slow.length ? "SLOW:" + slow.map(function(r){return r.path}).join(",") : "All <200ms");
      return;
    }

    var link = links[i++];
    var start = performance.now();
    var main = document.querySelector("main");
    if (!main) { results.push({path:link.path, ms:-1, err:"no main"}); next(); return; }

    var obs = new MutationObserver(function() {
      if (location.pathname === link.path) {
        var ms = Math.round(performance.now() - start);
        obs.disconnect();
        results.push({ path: link.path, ms: ms, err: "" });
        setTimeout(next, 100);
      }
    });
    obs.observe(main, { childList: true, subtree: true });

    // Safety timeout
    setTimeout(function() {
      obs.disconnect();
      if (!results.find(function(r) { return r.path === link.path; })) {
        results.push({ path: link.path, ms: Math.round(performance.now() - start), err: "timeout" });
      }
      setTimeout(next, 50);
    }, 5000);

    link.el.click();
  }

  window.navTest = { run: next };
  console.log("[navTest] " + links.length + " links. Run navTest.run()");
})();
