/* Machine Speed — Explore board.
   Vanilla, no dependencies, no build step. Reads the JSON payload build.py
   inlines into the page, so it works from a file:// copy and needs no fetch.

   Three ideas do the work:
     1. The lane x week matrix is the navigator — every cell is a two-axis
        filter (that lane, that week) and the gutter carries each lane's trend.
     2. Related items collapse into running stories. Watchlist threads from
        data.json are the primary keys; two-word proper-noun phrases are the
        fallback. A story can span weeks, which is the point.
     3. Unread is per visitor, remembered in localStorage, not a build-time date.
*/
(function () {
  "use strict";

  var root = document.getElementById("msx");
  var payload = document.getElementById("msx-data");
  if (!root || !payload) return;

  var DATA = JSON.parse(payload.textContent);
  var ITEMS = DATA.items.slice().sort(byDateDesc);
  var LANES = DATA.lanes;
  var LKEY = {};
  LANES.forEach(function (l) { LKEY[l.key] = l; });

  /* Colours come from the stylesheet, not from a table in here: board.css maps
     --x-cap … --x-mkt onto the site's own lane tokens, so the theme toggle and any
     future palette edit reach this view without a second source of truth. */
  var _cache = {};
  function cssVar(name) {
    if (!(name in _cache)) _cache[name] = getComputedStyle(root).getPropertyValue(name).trim();
    return _cache[name];
  }
  function laneColor(k) { return cssVar("--x-" + k) || "#8c8579"; }
  function _lum(c) {
    function f(v) { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]);
  }
  function _ratio(a, b) {
    var l1 = _lum(a), l2 = _lum(b);
    return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
  }
  /* A lane hue used as text over a wash of itself reads fine when the hue is
     light against a dark panel and badly when it is mid-luminance against a
     light one — the same rule inverts between the two themes. So mix the hue
     toward the page's ink until it clears 4.5:1 against whatever it actually
     sits on: lane identity survives, legibility is measured rather than hoped
     for, and both themes get their own answer from the same call. */
  /* Lane text lands on two different surfaces — the card (--x-bg) and the
     toolbar/matrix/reader panels (--x-panel) — and a colour clamped against one
     misses on the other, which is what kept happening. A custom property's
     computed value is its declaration text, not a colour, so the surfaces are
     read off real painted probes and the clamp has to satisfy the WORSE of the
     two. One colour per lane, legible wherever it is used, in either theme. */
  var _probes = null;
  function surfaces() {
    if (!_probes) {
      var mk = function (bg) {
        var p = document.createElement("span");
        p.style.cssText = "position:absolute;width:1px;height:1px;visibility:hidden;background:" + bg;
        root.appendChild(p);
        return p;
      };
      _probes = { card: mk("var(--x-bg)"), panel: mk("var(--x-panel)"), hi: mk("var(--x-hi)") };
    }
    var card = toRGB(getComputedStyle(_probes.card).backgroundColor) || [21, 23, 27];
    var panel = toRGB(getComputedStyle(_probes.panel).backgroundColor) || [27, 34, 48];
    /* --x-hi is a translucent wash used for selected rows, so it makes a third
       surface: the panel seen through it. Composite it by hand — a computed
       background-color is returned as authored, not as painted. */
    var hiRaw = String(getComputedStyle(_probes.hi).backgroundColor).match(/rgba?\(([^)]+)\)/);
    var hi = panel;
    if (hiRaw) {
      var p = hiRaw[1].split(/[,\s\/]+/).map(Number);
      var a = p[3] === undefined ? 1 : p[3];
      hi = panel.map(function (v, i) { return Math.round(a * p[i] + (1 - a) * v); });
    }
    return [card, panel, hi];
  }
  function inkRGB() { return toRGB(getComputedStyle(root).color) || [236, 235, 230]; }
  function readable(col, alpha) {
    var hue = toRGB(col) || [140, 133, 121];
    var ink = inkRGB();
    var backs = surfaces().map(function (s) {
      return alpha ? hue.map(function (v, i) { return Math.round(alpha * v + (1 - alpha) * s[i]); }) : s;
    });
    var worst = function (fg) {
      return Math.min.apply(null, backs.map(function (b) { return _ratio(fg, b); }));
    };
    var best = hue, bestR = worst(hue);
    for (var t = 0.1; t <= 1.001 && bestR < 4.7; t += 0.1) {
      var m = hue.map(function (v, i) { return Math.round(v + (ink[i] - v) * t); });
      var r = worst(m);
      if (r > bestR) { best = m; bestR = r; }
    }
    if (bestR < 4.7 && worst(ink) > bestR) best = ink;
    return "rgb(" + best.join(",") + ")";
  }
  function toRGB(c) {
    if (!c) return null;
    c = c.trim();
    var m = c.match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i);
    if (m) {
      var h = m[1];
      if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
      return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
    }
    m = c.match(/rgba?\(([^)]+)\)/i);
    if (m) {
      var p = m[1].split(/[,\s\/]+/).map(parseFloat);
      return [p[0] | 0, p[1] | 0, p[2] | 0];
    }
    return null;
  }

  var MON = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
  var MONT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

  function byDateDesc(a, b) { return a.date < b.date ? 1 : a.date > b.date ? -1 : 0; }
  function parseD(s) { var p = s.split("-"); return new Date(Date.UTC(+p[0], +p[1] - 1, +p[2])); }
  function stamp(s) { var d = parseD(s); return MON[d.getUTCMonth()] + " " + d.getUTCDate(); }
  function mondayKey(s) {
    var d = parseD(s), off = (d.getUTCDay() + 6) % 7;
    d.setUTCDate(d.getUTCDate() - off);
    return d.toISOString().slice(0, 10);
  }
  function weekLabel(k) { var d = parseD(k); return "WEEK OF " + MONT[d.getUTCMonth()].toUpperCase() + " " + d.getUTCDate(); }
  function weekRange(k) {
    var a = parseD(k), b = parseD(k);
    b.setUTCDate(b.getUTCDate() + 6);
    var left = MONT[a.getUTCMonth()] + " " + a.getUTCDate();
    var right = a.getUTCMonth() === b.getUTCMonth() ? String(b.getUTCDate())
      : MONT[b.getUTCMonth()] + " " + b.getUTCDate();
    return left + " \u2013 " + right;
  }
  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function tint(col, a) {
    var c = toRGB(col) || [140, 133, 121];
    return "rgba(" + c[0] + "," + c[1] + "," + c[2] + "," + (Math.round(a * 100) / 100) + ")";
  }
  function hi(text, q) {
    if (!q) return esc(text);
    var i = text.toLowerCase().indexOf(q);
    if (i < 0) return esc(text);
    return esc(text.slice(0, i)) + "<mark>" + esc(text.slice(i, i + q.length)) + "</mark>" + esc(text.slice(i + q.length));
  }

  /* ---- unread, per visitor ---------------------------------------------- */
  var SEEN_KEY = "ms-explore-seen";
  var since = DATA.prevRun || "";
  try {
    var stored = localStorage.getItem(SEEN_KEY);
    if (stored) since = stored;
  } catch (e) { /* private mode: fall back to the previous run date */ }
  function markRead() {
    since = (DATA.updatedISO || "").slice(0, 10) || new Date().toISOString().slice(0, 10);
    try { localStorage.setItem(SEEN_KEY, since); } catch (e) {}
    render();
  }
  function isUnread(it) { return since ? it.date > since : false; }

  /* ---- state ------------------------------------------------------------ */
  var WEEKS = [];
  (function () {
    var seen = {};
    ITEMS.forEach(function (it) {
      var k = mondayKey(it.date);
      if (!seen[k]) { seen[k] = 1; WEEKS.push(k); }
    });
    WEEKS.sort().reverse();
  })();

  var S = {
    q: "", lanes: [], week: null, range: "2", unreadOnly: false,
    open: {}, stories: {}, cur: {}, list: {}, weeksOpen: {}
  };

  (function fromURL() {
    var p = new URLSearchParams(location.search);
    if (p.get("q")) S.q = p.get("q");
    if (p.get("lane")) S.lanes = p.get("lane").split(",").filter(function (k) { return !!LKEY[k]; });
    if (p.get("week") && WEEKS.indexOf(p.get("week")) >= 0) S.week = p.get("week");
    if (p.get("range")) S.range = p.get("range");
    if (p.get("unread") === "1") S.unreadOnly = true;
  })();

  function toURL() {
    var p = new URLSearchParams();
    if (S.q) p.set("q", S.q);
    if (S.lanes.length) p.set("lane", S.lanes.join(","));
    if (S.week) p.set("week", S.week);
    if (S.range !== "2") p.set("range", S.range);
    if (S.unreadOnly) p.set("unread", "1");
    var qs = p.toString();
    history.replaceState(null, "", qs ? location.pathname + "?" + qs : location.pathname);
  }

  /* ---- filtering -------------------------------------------------------- */
  function pool() {
    var q = S.q.trim().toLowerCase();
    return ITEMS.filter(function (it) {
      if (S.lanes.length && S.lanes.indexOf(it.lane) < 0) return false;
      if (S.unreadOnly && !isUnread(it)) return false;
      if (q && (it.headline + " " + it.core + " " + it.outlet + " " + it.url).toLowerCase().indexOf(q) < 0) return false;
      return true;
    });
  }
  function scoped(list) {
    if (S.week) return list.filter(function (it) { return mondayKey(it.date) === S.week; });
    if (S.range !== "all") {
      var keep = WEEKS.slice(0, +S.range);
      return list.filter(function (it) { return keep.indexOf(mondayKey(it.date)) >= 0; });
    }
    return list;
  }

  /* ---- clustering ------------------------------------------------------- */
  var STOP = {};
  ("about above after again against allows almost along already among another anything around because become before behind being below between beyond called cannot could court cover covered daily despite during earlier early either enough every field first follow found further given going human inside instead itself known large later least level lines linked little longer looking major makes making means might month months moved never often other others public rather right rules second series shows since small start state still study taking terms testing thing think third those three through times today total under until using warns weeks where which while whose within without would years " +
   "security attacks attack model models agent agents agentic company companies government federal million billion policy cyber chinese american officials launch launches release released releases update updates report reports reported research researchers systems system frontier " +
   "finds found finding warned tells told says said adds added files filed seeks urges plans opens faces claims denies confirms confirmed announces announced unveils reveals revealed calls flags names sends signs backs blocks halts pauses drops takes puts gets sets shows including included tested flaws issues risks concerns questions details expected likely amid ahead more most less than with over into from that this these those what when will would their there here also only just even"
  ).split(/\s+/).forEach(function (w) { if (w) STOP[w] = 1; });
  var VEND = {};
  "anthropic openai microsoft google alphabet claude gemini nvidia amazon apple deepmind mistral cohere meta xai perplexity".split(" ")
    .forEach(function (w) { VEND[w] = 1; });

  function clusters(list) {
    var used = {}, out = [];

    (DATA.watchlist || []).forEach(function (t) {
      var terms = [];
      t.thread.replace(/[^A-Za-z0-9\- ]/g, " ").split(/\s+/).forEach(function (w) {
        var lw = w.toLowerCase();
        var acro = w.length >= 4 && /^[A-Z0-9]+$/.test(w);
        if (!acro && (lw.length < 5 || STOP[lw])) return;
        terms.push({ t: lw, strong: acro || lw.length >= 9 });
      });
      if (!terms.length) return;
      var items = list.filter(function (it) {
        if (used[it.id]) return false;
        var hay = (it.headline + " " + it.core).toLowerCase();
        var n = 0, strong = false;
        terms.forEach(function (x) { if (hay.indexOf(x.t) >= 0) { n++; if (x.strong) strong = true; } });
        return n >= 2 || (n === 1 && strong);
      });
      if (items.length < 2) return;
      items.forEach(function (it) { used[it.id] = 1; });
      out.push({ key: "w:" + t.thread, title: t.thread, watch: true, items: items.slice().sort(byDateDesc) });
    });

    var BI = {}, LBL = {};
    list.forEach(function (it) {
      if (used[it.id]) return;
      var toks = it.headline.replace(/[^A-Za-z0-9\-' ]/g, " ").split(/\s+/).filter(Boolean);
      var seen = {};
      for (var i = 0; i < toks.length - 1; i++) {
        var a = toks[i], b = toks[i + 1], la = a.toLowerCase(), lb = b.toLowerCase();
        if (la.length < 4 || lb.length < 4 || STOP[la] || STOP[lb]) continue;
        if (!/^[A-Za-z]/.test(a) || !/^[A-Za-z]/.test(b)) continue;
        var capA = i > 0 && a[0] === a[0].toUpperCase(), capB = b[0] === b[0].toUpperCase();
        if (!capA && !capB) continue;            /* sentence case: caps = proper noun */
        if (VEND[la] && VEND[lb]) continue;      /* "Anthropic Claude" is a masthead */
        var k = la + " " + lb;
        if (seen[k]) continue;
        seen[k] = 1;
        if (!BI[k]) { BI[k] = []; LBL[k] = a + " " + b; }
        BI[k].push(it);
      }
    });
    Object.keys(BI).filter(function (k) { return BI[k].length >= 2; }).map(function (k) {
      return { k: k, items: BI[k], score: BI[k].length * 12 + Math.min(k.length, 16) };
    }).sort(function (x, y) { return y.score - x.score; }).forEach(function (c) {
      var items = c.items.filter(function (it) { return !used[it.id]; });
      if (items.length < 2) return;
      items.forEach(function (it) { used[it.id] = 1; });
      out.push({ key: "b:" + c.k, title: LBL[c.k], watch: false, items: items.slice().sort(byDateDesc) });
    });
    return out;
  }

  /* ---- toolbar (built once, so the search field keeps focus) ------------ */
  var elBar, elMain;
  function boot() {
    root.innerHTML = "";
    elBar = document.createElement("div");
    elBar.className = "msx-bar";
    elBar.innerHTML =
      '<span class="lbl">SEARCH</span>' +
      '<input class="msx-search" type="search" placeholder="langflow, PLC, npm, CVE-2026…" aria-label="Search the board">' +
      '<span class="msx-count" data-role="count"></span>' +
      '<button class="msx-plain" data-act="reset" type="button">Reset</button>';
    root.appendChild(elBar);

    var bar2 = document.createElement("div");
    bar2.className = "msx-bar";
    var lane = LANES.map(function (l) {
      return '<button class="msx-chip lane" data-act="lane" data-lane="' + l.key + '" type="button" aria-pressed="false">' +
        '<span data-role="chip-' + l.key + '">' + esc(l.name) + "</span></button>";
    }).join("");
    var range = [["1", "This week"], ["2", "Last 2"], ["4", "Last 4"], ["all", "All " + WEEKS.length + " weeks"]]
      .map(function (r) {
        return '<button class="msx-chip" data-act="range" data-range="' + r[0] + '" type="button" aria-pressed="false">' + r[1] + "</button>";
      }).join("");
    var opts = ['<option value="">Any week in range</option>'].concat(WEEKS.map(function (k) {
      return '<option value="' + k + '">' + weekRange(k) + "</option>";
    })).join("");
    bar2.innerHTML =
      '<span class="msx-group"><span class="lbl">LANE</span>' + lane + "</span>" +
      '<span class="msx-group"><span class="lbl">WEEKS</span>' + range + "</span>" +
      '<span class="msx-group"><span class="lbl">OR ONE WEEK</span>' +
        '<select class="msx-select" data-role="weeksel" aria-label="Jump to one week">' + opts + "</select></span>" +
      '<span class="msx-group"><button class="msx-chip ghost" data-act="unread" type="button" aria-pressed="false" data-role="unread"></button>' +
        '<button class="msx-plain" data-act="markread" type="button" data-role="markread">Mark all read</button></span>' +
      '<span class="msx-scope" data-role="scope"></span>';
    root.appendChild(bar2);

    elMain = document.createElement("div");
    root.appendChild(elMain);

    var foot = document.createElement("div");
    foot.className = "msx-foot-note";
    foot.innerHTML = "<span>" + esc(DATA.coverage ? "Covering " + DATA.coverage : "") +
      "</span><span class=\"mono\">" + esc(DATA.updatedDisplay || "") + "</span>";
    root.appendChild(foot);

    var input = elBar.querySelector(".msx-search");
    input.value = S.q;
    var t;
    input.addEventListener("input", function () {
      clearTimeout(t);
      t = setTimeout(function () { S.q = input.value; render(); }, 140);
    });

    root.addEventListener("click", onClick);
    root.addEventListener("change", function (e) {
      if (!e.target.matches('[data-role="weeksel"]')) return;
      S.week = e.target.value || null;
      render();
    });
    var mo = new MutationObserver(function () { _cache = {}; render(); });  /* probes re-read live */
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  }

  function onClick(e) {
    var b = e.target.closest("[data-act]");
    if (!b || !root.contains(b)) return;
    var act = b.getAttribute("data-act");
    if (act === "lane") {
      var k = b.getAttribute("data-lane");
      var i = S.lanes.indexOf(k);
      if (i < 0) S.lanes.push(k); else S.lanes.splice(i, 1);
    } else if (act === "range") {
      S.range = b.getAttribute("data-range"); S.week = null;
    } else if (act === "unread") {
      S.unreadOnly = !S.unreadOnly;
    } else if (act === "markread") {
      markRead(); return;
    } else if (act === "reset") {
      S.q = ""; S.lanes = []; S.week = null; S.range = "2"; S.unreadOnly = false;
      elBar.querySelector(".msx-search").value = "";
      root.querySelector('[data-role="weeksel"]').value = "";
    } else if (act === "story") {
      var sk = b.getAttribute("data-story");
      S.stories[sk] = !storyOpen(sk, +b.getAttribute("data-i"));
    } else if (act === "cursor") {
      S.cur[b.getAttribute("data-story")] = +b.getAttribute("data-i");
    } else if (act === "step") {
      var key = b.getAttribute("data-story"), n = +b.getAttribute("data-n"), max = +b.getAttribute("data-max");
      var at = S.cur[key] || 0;
      S.cur[key] = Math.max(0, Math.min(max, at + n));
    } else if (act === "listmode") {
      var lk = b.getAttribute("data-story");
      S.list[lk] = !S.list[lk];
    } else if (act === "item") {
      var id = b.getAttribute("data-id");
      S.open[id] = !S.open[id];
    } else if (act === "wtoggle") {
      var wk = b.getAttribute("data-week");
      S.weeksOpen[wk] = !weekOpen(wk, +b.getAttribute("data-i"));
    } else { return; }
    e.preventDefault();
    render();
  }

  function storyOpen(key, i) {
    return key in S.stories ? S.stories[key] : i < 3;
  }
  function weekOpen(key, i) {
    return key in S.weeksOpen ? S.weeksOpen[key] : (!!S.week || i === 0);
  }

  /* ---- rows ------------------------------------------------------------- */
  function rowHTML(it, opts) {
    var q = S.q.trim().toLowerCase();
    var col = laneColor(it.lane);
    var cls = "msx-row" + (isUnread(it) ? " unread" : "") + (opts.faded ? " faded" : "") + (opts.noLane ? " nolane" : "");
    var lane = opts.noLane ? "" : '<span class="ln">' + esc((LKEY[it.lane] || {}).name.toUpperCase()) + "</span>";
    var body = "";
    if (S.open[it.id]) {
      body = '<div class="msx-body' + (opts.noLane ? " flush" : "") + '"><p>' + hi(it.core, q) + "</p>" +
        '<span class="msx-conf">' + esc(DATA.conf[it.confidence] || it.confidence) + "</span> " +
        '<a class="msx-src" href="' + esc(it.url) + '" target="_blank" rel="noopener">' + esc(it.outlet) + " &#8599;</a> " +
        '<a class="msx-src" href="' + esc(it.page) + "#" + esc(it.id) + '">on the board &#8594;</a></div>';
    }
    return '<div style="--ln:' + col + ";--ln-soft:" + tint(col, 0.18) + ";--ln-text:" + readable(col, 0) + '">' +
      '<button class="' + cls + '" data-act="item" data-id="' + esc(it.id) + '" type="button" aria-expanded="' + !!S.open[it.id] + '">' +
      '<span class="dot"></span>' + lane +
      '<span class="hl">' + hi(it.headline, q) + "</span>" +
      '<span class="out">' + esc(it.outlet) + "</span>" +
      '<span class="dt">' + stamp(it.date) + "</span>" +
      '<span class="cv">' + (S.open[it.id] ? "&#9652;" : "&#9662;") + "</span>" +
      "</button>" + body + "</div>";
  }

  /* ---- stories ---------------------------------------------------------- */
  function storyHTML(c, i, inScope) {
    var open = storyOpen(c.key, i);
    var lanes = LANES.filter(function (l) {
      return c.items.some(function (it) { return it.lane === l.key; });
    }).map(function (l) {
      var n = c.items.filter(function (it) { return it.lane === l.key; }).length;
      var lc = laneColor(l.key);
      return '<i style="background:' + tint(lc, 0.16) + ";color:" + readable(lc, 0.16) + '">' + esc(l.name.toUpperCase()) + " " + n + "</i>";
    }).join("");
    var dates = c.items.map(function (it) { return it.date; }).sort();
    var span = dates.length > 1 ? stamp(dates[0]) + " \u2013 " + stamp(dates[dates.length - 1]) : stamp(dates[0]);
    var wks = {};
    c.items.forEach(function (it) { wks[mondayKey(it.date)] = 1; });
    var nwk = Object.keys(wks).length;

    var out = ['<div class="msx-story">'];
    out.push('<button class="msx-sbtn" data-act="story" data-story="' + esc(c.key) + '" data-i="' + i + '" type="button" aria-expanded="' + open + '">' +
      '<span class="msx-shead">' +
        '<span class="msx-tag' + (c.watch ? " watch" : "") + '">' +
        (c.watch ? "WATCHLIST THREAD" : "SHARED SUBJECT") + "</span>" +
        '<span class="msx-stitle">' + esc(c.title) + "</span>" +
        '<span class="msx-lanetags">' + lanes + "</span>" +
      "</span>" +
      '<span class="msx-span">' + span + "</span>" +
      '<span class="msx-n">' + c.items.length + " items &middot; " + (nwk === 1 ? "1 week" : nwk + " weeks") + "</span>" +
      '<span class="msx-caret">' + (open ? "&#9662;" : "&#9656;") + "</span></button>");

    if (open) {
      out.push("<div>");
      var long = c.items.length > 3;
      var listMode = !!S.list[c.key];
      if (long && !listMode) {
        var cur = Math.min(Math.max(0, S.cur[c.key] || 0), c.items.length - 1);
        var it = c.items[cur];
        var times = c.items.map(function (x) { return parseD(x.date).getTime(); });
        var t0 = Math.min.apply(null, times), t1 = Math.max.apply(null, times);
        var ticks = c.items.map(function (x, j) {
          var left = t1 > t0 ? Math.round(((parseD(x.date).getTime() - t0) / (t1 - t0)) * 100) : 50;
          var act = j === cur;
          return '<button class="msx-tick" data-act="cursor" data-story="' + esc(c.key) + '" data-i="' + j + '" type="button"' +
            ' aria-label="' + esc(stamp(x.date)) + '" style="left:' + left + "%;top:" + (act ? 0 : 5) + "px;width:" +
            (act ? 3 : 2) + "px;height:" + (act ? 20 : 11) + "px;background:" +
            (act ? "var(--x-ink)" : laneColor(x.lane)) + '"></button>';
        }).join("");
        var idx = c.items.map(function (x, j) {
          var short = x.headline.length > 74 ? x.headline.slice(0, 72).replace(/[ ,;:]+$/, "") + "\u2026" : x.headline;
          return '<button class="msx-ibtn" data-act="cursor" data-story="' + esc(c.key) + '" data-i="' + j + '" type="button"' +
            ' aria-current="' + (j === cur) + '" style="--ln:' + laneColor(x.lane) + ";--ln-text:" + readable(laneColor(x.lane), 0) + '">' +
            "<time>" + stamp(x.date) + "</time><span>" + esc(short) + "</span></button>";
        }).join("");
        out.push('<div class="msx-reader">' +
          '<div class="msx-time"><span class="axis"></span>' + ticks + "</div>" +
          '<div class="msx-cols"><div class="msx-art">' +
          '<div class="msx-kicker"><i style="background:' + tint(laneColor(it.lane), 0.16) + ";color:" + readable(laneColor(it.lane), 0.16) + '">' + esc((LKEY[it.lane] || {}).name.toUpperCase()) + "</i>" +
          "<time>" + stamp(it.date) + "</time>" +
          "</div>" +
          "<h3>" + esc(it.headline) + "</h3><p>" + esc(it.core) + "</p>" +
          '<div class="msx-foot">' +
          '<button class="msx-btn" data-act="step" data-story="' + esc(c.key) + '" data-n="-1" data-max="' + (c.items.length - 1) + '" type="button"' + (cur <= 0 ? " disabled" : "") + ">&#8592; Newer</button>" +
          '<button class="msx-btn" data-act="step" data-story="' + esc(c.key) + '" data-n="1" data-max="' + (c.items.length - 1) + '" type="button"' + (cur >= c.items.length - 1 ? " disabled" : "") + ">Older &#8594;</button>" +
          '<span class="mono" style="font-size:10px;color:var(--x-faint)">' + (cur + 1) + " of " + c.items.length + ", newest first</span>" +
          '<span style="flex:1"></span>' +
          '<span class="msx-conf">' + esc(DATA.conf[it.confidence] || it.confidence) + "</span>" +
          '<a class="msx-src" href="' + esc(it.url) + '" target="_blank" rel="noopener">' + esc(it.outlet) + " &#8599;</a>" +
          '<a class="msx-src" href="' + esc(it.page) + "#" + esc(it.id) + '">on the board &#8594;</a>' +
          "</div></div>" +
          '<div class="msx-idx"><div class="h">IN THIS THREAD</div><div class="msx-ilist">' + idx + "</div></div>" +
          "</div></div>");
      } else {
        out.push(c.items.map(function (x) {
          return rowHTML(x, { faded: !inScope[x.id] });
        }).join(""));
      }
      if (long) {
        out.push('<button class="msx-more" data-act="listmode" data-story="' + esc(c.key) + '" type="button">' +
          (listMode ? "Back to one at a time" : "See all " + c.items.length + " as a list") + "</button>");
      }
      out.push("</div>");
    }
    out.push("</div>");
    return out.join("");
  }

  /* ---- ledger ----------------------------------------------------------- */
  function ledgerHTML(list) {
    var buckets = {}, order = [];
    list.forEach(function (it) {
      var k = mondayKey(it.date);
      if (!buckets[k]) { buckets[k] = []; order.push(k); }
      buckets[k].push(it);
    });
    order.sort().reverse();
    return order.map(function (k, i) {
      var items = buckets[k];
      var open = weekOpen(k, i);
      var byLane = LANES.filter(function (l) {
        return items.some(function (it) { return it.lane === l.key; });
      }).map(function (l) {
        return { lane: l, rows: items.filter(function (it) { return it.lane === l.key; }) };
      });
      var unread = items.filter(isUnread).length;
      var bar = byLane.map(function (g) {
        return '<i style="flex:' + g.rows.length + ";background:" + laneColor(g.lane.key) + '"></i>';
      }).join("");
      var out = ['<section class="msx-week">'];
      out.push('<button class="msx-wbtn" data-act="wtoggle" data-week="' + k + '" data-i="' + i + '" type="button" aria-expanded="' + open + '">' +
        '<span class="wl">' + weekLabel(k) + "</span>" +
        '<span class="bar">' + bar + "</span>" +
        '<span class="wm">' + items.length + (items.length === 1 ? " item" : " items") + (unread ? " &middot; " + unread + " unread" : "") + "</span>" +
        '<span class="msx-caret">' + (open ? "&#9662;" : "&#9656;") + "</span></button>");
      if (!open) {
        out.push('<div class="msx-wsum">' + byLane.map(function (g) {
          return g.rows.length + " " + g.lane.name.toLowerCase();
        }).join("  &middot;  ") + "</div>");
      } else {
        out.push(byLane.map(function (g) {
          return '<div class="msx-lanegroup" style="--ln:' + laneColor(g.lane.key) + ";--ln-text:" + readable(laneColor(g.lane.key), 0) + '">' +
            '<div class="msx-lanehead"><i></i>' + esc(g.lane.name.toUpperCase()) +
            '<span class="c">' + g.rows.length + (g.rows.length === 1 ? " item" : " items") + "</span></div>" +
            g.rows.map(function (it) { return rowHTML(it, { noLane: true }); }).join("") + "</div>";
        }).join(""));
      }
      out.push("</section>");
      return out.join("");
    }).join("");
  }

  /* ---- render ----------------------------------------------------------- */
  function render() {
    var p = pool();
    var inView = scoped(p);
    var q = S.q.trim();

    /* toolbar state */
    var scope = S.week ? weekLabel(S.week)
      : (S.range === "all" ? "ALL " + WEEKS.length + " WEEKS" : "LAST " + S.range + (S.range === "1" ? " WEEK" : " WEEKS"));
    root.querySelector('[data-role="scope"]').textContent =
      (S.lanes.length ? S.lanes.map(function (k) { return LKEY[k].name.toUpperCase(); }).join(" + ") + " \u00b7 " : "") + scope;
    root.querySelector('[data-role="count"]').textContent =
      inView.length === ITEMS.length ? ITEMS.length + " items on the board" : inView.length + " of " + ITEMS.length + " items";
    var nUnread = ITEMS.filter(isUnread).length;
    var ub = root.querySelector('[data-role="unread"]');
    ub.textContent = nUnread ? "Unread " + nUnread : "No unread";
    ub.setAttribute("aria-pressed", String(S.unreadOnly));
    ub.disabled = !nUnread && !S.unreadOnly;
    root.querySelector('[data-role="markread"]').hidden = !nUnread;
    LANES.forEach(function (l) {
      var btn = root.querySelector('[data-act="lane"][data-lane="' + l.key + '"]');
      btn.setAttribute("aria-pressed", String(S.lanes.indexOf(l.key) >= 0));
      btn.style.setProperty("--ln", laneColor(l.key));
      btn.style.setProperty("--ln-soft", tint(laneColor(l.key), 0.18));
      btn.style.setProperty("--ln-text", readable(laneColor(l.key), 0));
      btn.style.setProperty("--ln-text-on", readable(laneColor(l.key), 0.18));
      var total = ITEMS.filter(function (it) { return it.lane === l.key; }).length;
      var shown = inView.filter(function (it) { return it.lane === l.key; }).length;
      btn.querySelector('[data-role="chip-' + l.key + '"]').textContent =
        l.name + " " + (shown === total ? total : shown + " / " + total);
    });
    Array.prototype.forEach.call(root.querySelectorAll('[data-act="range"]'), function (b) {
      b.setAttribute("aria-pressed", String(!S.week && S.range === b.getAttribute("data-range")));
      b.disabled = !!S.week;   /* a chosen week supersedes the range */
    });
    var sel = root.querySelector('[data-role="weeksel"]');
    if (sel.value !== (S.week || "")) sel.value = S.week || "";

    if (!inView.length) {
      var parts = [];
      if (q) parts.push("the search \u201c" + q + "\u201d");
      if (S.lanes.length) parts.push(S.lanes.length === 1 ? "the " + LKEY[S.lanes[0]].name + " lane" : "those " + S.lanes.length + " lanes");
      if (S.week) parts.push(weekLabel(S.week).toLowerCase());
      else if (S.range !== "all") parts.push("the last " + S.range + (S.range === "1" ? " week" : " weeks"));
      if (S.unreadOnly) parts.push("unread only");
      elMain.innerHTML = '<div class="msx-empty"><h4>NO MATCHES</h4><p>Nothing matches ' +
        esc(parts.join(" plus ")) + '.</p><button class="msx-btn" data-act="reset" type="button">Reset</button></div>';
      toURL();
      return;
    }

    var inScope = {};
    inView.forEach(function (it) { inScope[it.id] = 1; });
    var cl = clusters(p).filter(function (c) {
      return c.items.some(function (it) { return inScope[it.id]; });
    });
    var clustered = {};
    cl.forEach(function (c) { c.items.forEach(function (it) { clustered[it.id] = 1; }); });
    var singles = inView.filter(function (it) { return !clustered[it.id]; });

    var out = [];
    if (cl.length) {
      out.push('<section class="msx-sec"><div class="msx-sechead"><span>RUNNING STORIES</span>' +
        '<span class="meta">' + cl.length + (cl.length === 1 ? " story" : " stories") + "</span></div>");
      out.push(cl.map(function (c, i) { return storyHTML(c, i, inScope); }).join(""));
      out.push("</section>");
    }
    if (singles.length) {
      out.push('<div class="msx-ledgerhead"><span>' +
        (cl.length ? "EVERYTHING ELSE, BY WEEK AND LANE" : "BY WEEK, GROUPED BY LANE") +
        '</span><span class="rule"></span></div>');
      out.push(ledgerHTML(singles));
    }
    elMain.innerHTML = out.join("");
    toURL();
  }

  boot();
  render();
})();
