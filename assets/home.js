/* Machine Speed — the This week banner on the front page.
   The slides are all in the HTML; without this script they simply stack.
   With it they become the same carousel as Explore's "New to the board":
   one slide at a time, arrows, numbered thumbs, a tick bar, and a seven-second
   advance that pauses on hover or focus and never runs under reduced motion. */
(function () {
  var car = document.querySelector("[data-hcar]");
  if (!car) return;
  var slides = car.querySelectorAll(".msx-carslide");
  var thumbs = car.querySelectorAll(".msx-carthumb");
  var ticks = car.querySelectorAll(".msx-carticks i");
  var count = car.querySelector(".msx-carnav .c");
  var n = slides.length, at = 0, hold = false, timer = null;
  if (!n) return;
  car.classList.add("js");

  function go(j) {
    at = ((j % n) + n) % n;
    for (var x = 0; x < n; x++) {
      var on = x === at;
      slides[x].hidden = !on;
      if (thumbs[x]) { thumbs[x].classList.toggle("on", on); thumbs[x].setAttribute("aria-current", String(on)); }
      if (ticks[x]) ticks[x].classList.toggle("on", on);
    }
    if (count) count.textContent = (at + 1) + " / " + n;
  }

  car.addEventListener("click", function (e) {
    var b = e.target.closest("button");
    if (!b) return;
    if (b.hasAttribute("data-step")) go(at + (+b.getAttribute("data-step")));
    else if (b.hasAttribute("data-i")) go(+b.getAttribute("data-i"));
  });
  car.addEventListener("mouseenter", function () { hold = true; });
  car.addEventListener("mouseleave", function () { hold = false; });
  car.addEventListener("focusin", function () { hold = true; });
  car.addEventListener("focusout", function () { hold = false; });

  var still = false;
  try { still = window.matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (e) {}
  if (!still && n > 1) {
    timer = setInterval(function () { if (!hold && !document.hidden) go(at + 1); }, 7000);
  }
  go(0);
})();
