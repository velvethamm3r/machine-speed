/* Machine Speed — progressive enhancement only.
   The theme attribute is already set by the tiny inline <head> script before
   first paint; this file just wires up the toggle button and persists the
   choice. Everything else on the site is static HTML. */
(function () {
  function label(t) { return t === "dark" ? ["☀", "Light"] : ["☾", "Dark"]; }

  function apply(t) {
    document.documentElement.setAttribute("data-theme", t);
    document.querySelectorAll("[data-theme-toggle]").forEach(function (b) {
      var l = label(t);
      b.querySelector(".ico").textContent = l[0];
      b.querySelector(".lbl").textContent = l[1];
    });
    try { localStorage.setItem("ms-theme", t); } catch (e) {}
  }

  document.querySelectorAll("[data-theme-toggle]").forEach(function (b) {
    b.hidden = false; // button only appears when JS is available
    var l = label(document.documentElement.getAttribute("data-theme") || "dark");
    b.querySelector(".ico").textContent = l[0];
    b.querySelector(".lbl").textContent = l[1];
    b.addEventListener("click", function () {
      var cur = document.documentElement.getAttribute("data-theme");
      apply(cur === "dark" ? "light" : "dark");
    });
  });
})();
