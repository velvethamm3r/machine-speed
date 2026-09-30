/* Machine Speed — search.
   Reads data/items.json (the open dataset the build already publishes) and
   filters it in the browser: every word typed must appear somewhere in an
   item's headline, summary, source, organisations, topics or lane. Results are
   newest first. The query lives in the URL (?q=…&lane=…), so a search can be
   shared and the header box on every page lands here. */
(function () {
  "use strict";
  var cfgEl = document.getElementById("search-config");
  var input = document.getElementById("sq");
  var out = document.getElementById("sresults");
  var count = document.getElementById("scount");
  if (!cfgEl || !input || !out) return;
  var CFG = JSON.parse(cfgEl.textContent);
  var ITEMS = [], lanes = {};
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var LIMIT = 150;

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function stamp(iso) {
    var p = iso.split("-");
    return MONTHS[+p[1] - 1] + " " + (+p[2]) + ", " + p[0];
  }
  function mark(text, words) {
    var html = esc(text);
    words.forEach(function (w) {
      if (w.length < 2) return;
      var re = new RegExp("(" + w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "gi");
      html = html.replace(re, "<mark>$1</mark>");
    });
    return html;
  }
  function snippet(core, words) {
    var lc = core.toLowerCase(), at = -1;
    words.forEach(function (w) { var i = lc.indexOf(w); if (i >= 0 && (at < 0 || i < at)) at = i; });
    if (at < 0 || core.length <= 240) return core.length > 240 ? core.slice(0, 237) + "…" : core;
    var start = Math.max(0, at - 80);
    var s = core.slice(start, start + 240);
    return (start ? "…" : "") + s + (start + 240 < core.length ? "…" : "");
  }

  function readURL() {
    var p = new URLSearchParams(location.search);
    input.value = p.get("q") || "";
    lanes = {};
    (p.get("lane") || "").split(",").forEach(function (k) { if (CFG.lanes[k]) lanes[k] = 1; });
  }
  function writeURL() {
    var p = new URLSearchParams();
    if (input.value.trim()) p.set("q", input.value.trim());
    var ls = Object.keys(lanes);
    if (ls.length) p.set("lane", ls.join(","));
    var qs = p.toString();
    try { history.replaceState(null, "", qs ? location.pathname + "?" + qs : location.pathname); } catch (e) {}
  }
  function syncChips() {
    Array.prototype.forEach.call(document.querySelectorAll(".schip"), function (b) {
      b.setAttribute("aria-pressed", String(!!lanes[b.getAttribute("data-lane")]));
    });
  }

  function run() {
    var q = input.value.trim().toLowerCase();
    var words = q ? q.split(/\s+/) : [];
    var anyLane = Object.keys(lanes).length > 0;
    var hits = ITEMS.filter(function (it) {
      if (anyLane && !lanes[it.lane]) return false;
      for (var i = 0; i < words.length; i++) if (it._hay.indexOf(words[i]) < 0) return false;
      return true;
    });
    if (!words.length && !anyLane) {
      count.textContent = ITEMS.length + " items on the board. Type to search, or pick a lane.";
      out.innerHTML = "";
      return;
    }
    count.textContent = hits.length === 0 ? "No items match." :
      hits.length + (hits.length === 1 ? " item" : " items") +
      (hits.length > LIMIT ? ", showing the newest " + LIMIT : "") + ".";
    out.innerHTML = hits.slice(0, LIMIT).map(function (it) {
      var L = CFG.lanes[it.lane] || { name: it.lane, page: "", pill: "" };
      var link = L.page + "#" + encodeURIComponent(it.id);
      var tops = (it.topics || []).map(function (t) { return CFG.topics[t]; }).filter(Boolean);
      return '<li class="sres"><div class="sm"><span class="lanepill ' + L.pill + '">' + esc(L.name) + "</span>" +
        "<time>" + stamp(it.date) + "</time>" +
        (tops.length ? '<span class="stop">' + esc(tops.join(" · ")) + "</span>" : "") + "</div>" +
        '<a class="sh" href="' + esc(link) + '">' + mark(it.headline, words) + "</a>" +
        '<p class="sc">' + mark(snippet(it.core, words), words) + "</p>" +
        '<span class="ss">' + esc(it.outlet) + " · " +
        '<a href="' + esc(it.url) + '" target="_blank" rel="noopener">source ↗</a></span></li>';
    }).join("");
  }

  var timer = null;
  input.addEventListener("input", function () {
    clearTimeout(timer);
    timer = setTimeout(function () { writeURL(); run(); }, 120);
  });
  input.form.addEventListener("submit", function (e) { e.preventDefault(); writeURL(); run(); });
  Array.prototype.forEach.call(document.querySelectorAll(".schip"), function (b) {
    b.addEventListener("click", function () {
      var k = b.getAttribute("data-lane");
      if (lanes[k]) delete lanes[k]; else lanes[k] = 1;
      syncChips(); writeURL(); run();
    });
  });

  readURL();
  syncChips();
  fetch(CFG.data).then(function (r) {
    if (!r.ok) throw new Error(r.status);
    return r.json();
  }).then(function (d) {
    ITEMS = (d.items || []).slice().sort(function (a, b) { return a.date < b.date ? 1 : a.date > b.date ? -1 : 0; });
    ITEMS.forEach(function (it) {
      var tops = (it.topics || []).map(function (t) { return CFG.topics[t] || ""; }).join(" ");
      var ents = (it.entities || []).join(" ").replace(/-/g, " ");
      var lane = (CFG.lanes[it.lane] || {}).name || "";
      it._hay = [it.headline, it.core, it.outlet, tops, ents, lane].join(" ").toLowerCase();
    });
    run();
    if (!input.value) input.focus();
  }).catch(function () {
    count.textContent = "The search index could not be loaded. Every item is also on the lane pages and the week pages.";
  });
})();
