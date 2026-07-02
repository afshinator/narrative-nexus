// Theme toggle timing test — paste into browser console
// Measures: 1) setTheme call duration  2) subscribe callback duration  3) time to next paint
(function() {
  var origToggle = document.documentElement.classList.toggle.bind(document.documentElement.classList);
  var timings = [];
  
  document.documentElement.classList.toggle = function() {
    var start = performance.now();
    var result = origToggle.apply(this, arguments);
    var elapsed = performance.now() - start;
    timings.push({ what: "classList.toggle", ms: Math.round(elapsed) });
    return result;
  };

  // Measure the subscribe callback by wrapping style.setProperty
  var origSetProp = document.documentElement.style.setProperty.bind(document.documentElement.style);
  document.documentElement.style.setProperty = function() {
    var start = performance.now();
    var result = origSetProp.apply(this, arguments);
    var elapsed = performance.now() - start;
    timings.push({ what: "style.setProperty", ms: Math.round(elapsed) });
    return result;
  };

  // Measure paint timing via rAF
  var originalRAF = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = function(cb) {
    return originalRAF(function(ts) {
      var start = performance.now();
      cb(ts);
      timings.push({ what: "paint (rAF)", ms: Math.round(performance.now() - start) });
    });
  };

  window.themeTimer = {
    reset: function() { timings = []; },
    report: function() { console.table(timings); return timings; },
    total: function() { 
      var total = timings.reduce(function(s,t) { return s + t.ms; }, 0);
      console.log("total: " + total + "ms");
      return total;
    }
  };

  console.log("[theme-timer] Ready. Toggle theme, then run themeTimer.report()");
})();
