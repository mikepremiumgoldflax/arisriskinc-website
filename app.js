/* ARIS Risk Inc. — interactions */
(function () {
  "use strict";

  // Sticky nav background on scroll
  var nav = document.getElementById("nav");
  function onScroll() {
    if (window.scrollY > 24) nav.classList.add("scrolled");
    else nav.classList.remove("scrolled");
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // Mobile menu
  var toggle = document.getElementById("navToggle");
  var menu = document.getElementById("mobileMenu");
  function closeMenu() {
    menu.classList.remove("open");
    toggle.setAttribute("aria-expanded", "false");
  }
  toggle.addEventListener("click", function () {
    var open = menu.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(open));
  });
  menu.querySelectorAll("a").forEach(function (a) {
    a.addEventListener("click", closeMenu);
  });
  window.addEventListener("resize", function () {
    if (window.innerWidth > 940) closeMenu();
  });
})();

/* ARIS Risk Inc. — conversion layer interactions */
(function () {
  "use strict";

  /* ---------- Interactive parcel maps ---------- */
  var legacy = document.getElementById("mapLegacy");
  var aris = document.getElementById("mapAris");
  var tip = document.getElementById("parcelTip");

  // Legacy: one uniform score smeared across the whole area.
  if (legacy) {
    for (var q = 0; q < 4; q++) {
      var big = document.createElement("div");
      big.className = "pcell";
      big.style.background = "#d98327";
      var s = document.createElement("span");
      s.className = "pscore";
      s.textContent = "0.41";
      big.appendChild(s);
      legacy.appendChild(big);
    }
  }

  // ARIS: deterministic per-parcel risk so the same picture renders every load.
  if (aris) {
    var N = 14;
    var streets = ["Ridge", "Canyon", "Summit", "Vista", "Pine", "Mesa", "Oak", "Crest"];
    var hash = function (x, y) {
      var h = (x * 73856093) ^ (y * 19349663);
      h = (h ^ (h >> 13)) * 1274126177;
      return ((h ^ (h >> 16)) >>> 0) / 4294967295; // 0..1
    };
    var riskAt = function (x, y) {
      // a wind/terrain corridor running diagonally, plus local variation
      var corridor = Math.exp(-Math.pow((x - y) / 4.2, 2));
      var ridge = 0.35 + 0.5 * Math.sin((x + y) / 3.1);
      var local = hash(x, y);
      var r = 0.30 * corridor + 0.34 * Math.max(0, ridge) + 0.46 * local;
      return Math.max(0, Math.min(1, r));
    };
    var colorFor = function (r) {
      if (r < 0.30) return "#1f9d55";
      if (r < 0.55) return "#ffb43a";
      if (r < 0.78) return "#ff6a1a";
      return "#e02424";
    };
    var tierFor = function (r) {
      if (r < 0.30) return "Lower";
      if (r < 0.55) return "Elevated";
      if (r < 0.78) return "High";
      return "Extreme";
    };
    var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    for (var y = 0; y < N; y++) {
      for (var x = 0; x < N; x++) {
        var r = riskAt(x, y);
        var cell = document.createElement("div");
        cell.className = "pcell" + (r >= 0.78 ? " ignite" : "");
        cell.style.background = colorFor(r);
        if (!reduce) cell.style.animationDelay = ((x + y) * 14) + "ms";
        else cell.style.animation = "none", cell.style.opacity = "1", cell.style.transform = "none";
        cell.setAttribute("tabindex", "0");
        var id = (100 + y) + " " + streets[(x + y) % streets.length] + " " + (r < 0.30 ? "Ln" : "Dr");
        cell.setAttribute("data-id", id);
        cell.setAttribute("data-score", r.toFixed(2));
        cell.setAttribute("data-tier", tierFor(r));
        aris.appendChild(cell);
      }
    }

    // Tooltip
    if (tip) {
      var showTip = function (el, cx, cy) {
        tip.innerHTML = el.getAttribute("data-id") + " &middot; <b>" +
          el.getAttribute("data-tier") + "</b> (" + el.getAttribute("data-score") + ")";
        tip.style.left = cx + "px";
        tip.style.top = cy + "px";
        tip.classList.add("show");
      };
      var hideTip = function () { tip.classList.remove("show"); };
      aris.addEventListener("mousemove", function (e) {
        var el = e.target.closest(".pcell");
        if (el) showTip(el, e.clientX, e.clientY); else hideTip();
      });
      aris.addEventListener("mouseleave", hideTip);
      aris.addEventListener("focusin", function (e) {
        var el = e.target.closest(".pcell");
        if (!el) return;
        var rct = el.getBoundingClientRect();
        showTip(el, rct.left + rct.width / 2, rct.top);
      });
      aris.addEventListener("focusout", hideTip);
    }
  }
})();
