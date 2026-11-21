/* Machine Speed — weekly layer. Everything here is an enhancement: with this file
   missing, every alert, case, topic and summary is still on the page and readable. */
(function () {
  "use strict";
  function all(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }

  /* Filter chips: a [data-wk-group] holds buttons [data-wk-show] and rows [data-wk-key]. */
  all("[data-wk-group]").forEach(function (group) {
    var chips = group.querySelector(".wk-chips");
    if (!chips) return;
    chips.hidden = false;
    all("button[data-wk-show]", chips).forEach(function (btn) {
      btn.addEventListener("click", function () {
        var want = btn.getAttribute("data-wk-show");
        all("button[data-wk-show]", chips).forEach(function (b) {
          b.setAttribute("aria-pressed", b === btn ? "true" : "false");
        });
        all("[data-wk-key]", group).forEach(function (row) {
          row.hidden = want !== "all" && row.getAttribute("data-wk-key") !== want;
        });
      });
    });
  });

  /* Tabs: one panel at a time, chosen by its link or by the URL's #… — which may
     also name something inside a panel (an item id on the full record). */
  function tabs(nav, panels) {
    if (!nav || !panels.length) return;
    var links = all("a", nav);
    function show(id) {
      var target = id && document.getElementById(id);
      var panel = target && panels.filter(function (p) { return p === target || p.contains(target); })[0];
      if (!panel) return false;
      panels.forEach(function (p) { p.hidden = p !== panel; });
      links.forEach(function (a) {
        if (a.getAttribute("href") === "#" + panel.id) a.setAttribute("aria-current", "true");
        else a.removeAttribute("aria-current");
      });
      return true;
    }
    panels[0].parentNode.classList.add("wk-tabs");
    if (!show(location.hash.slice(1))) show(panels[0].id);
    links.forEach(function (a) {
      a.addEventListener("click", function (e) {
        e.preventDefault();
        var id = a.getAttribute("href").slice(1);
        show(id);
        if (history.replaceState) history.replaceState(null, "", "#" + id);
      });
    });
    window.addEventListener("hashchange", function () {
      var id = location.hash.slice(1);
      if (show(id)) document.getElementById(id).scrollIntoView();
    });
  }
  tabs(document.querySelector(".wk-topicnav"), all(".wk-topic"));
  tabs(document.querySelector(".wk-lanenav"), all(".wk-lanesec"));

  /* Full record: open or close every summary in a lane. */
  all("[data-wk-expand]").forEach(function (btn) {
    var sec = btn.closest("section");
    btn.hidden = !sec.querySelector("details.wk-sum");
    btn.addEventListener("click", function () {
      var boxes = all("details.wk-sum", sec);
      var open = boxes.some(function (d) { return !d.open; });
      boxes.forEach(function (d) { d.open = open; });
      btn.textContent = open ? "Collapse all summaries" : "Expand all summaries";
    });
  });
})();
