const constructors = {
  Red_bull: [
    { start: 2010, end: 2024, name: "Red Bull Racing", color: "#3671C6", logo: "/static/images/constructors/redbull.png" }
  ],
  Mercedes: [
    { start: 2010, end: 2024, name: "Mercedes", color: "#00D2BE", logo: "/static/images/constructors/mercedes.png" }
  ],
  Ferrari: [
    { start: 2010, end: 2024, name: "Ferrari", color: "#DC0000", logo: "/static/images/constructors/ferrari.png" }
  ],
  Mclaren: [
    { start: 2010, end: 2024, name: "McLaren", color: "#FF8000", logo: "/static/images/constructors/mclaren.png" }
  ],
  Williams: [
    { start: 2010, end: 2024, name: "Williams", color: "#005AFF", logo: "/static/images/constructors/williams.png" }
  ],
  Sauber: [
    { start: 2010, end: 2018, name: "Sauber F1 Team", color: "#9B0000", logo: "/static/images/constructors/sauber.png" },
    { start: 2024, end: 2024, name: "Kick Sauber", color: "#52E252", logo: "/static/images/constructors/kicksauber.png" }
  ],
  Alfa: [
    { start: 2019, end: 2023, name: "Alfa Romeo", color: "#9B0000", logo: "/static/images/constructors/alfaromeo.png" }
  ],
  Toro_rosso: [
    { start: 2010, end: 2019, name: "Toro Rosso", color: "#00008B", logo: "/static/images/constructors/tororosso.png" }
  ],
  Alphatauri: [
    { start: 2020, end: 2023, name: "AlphaTauri", color: "#2B4562", logo: "/static/images/constructors/alphatauri.png" }
  ],
  Rb: [
    { start: 2024, end: 2024, name: "Visa Cash App RB", color: "#2B4562", logo: "/static/images/constructors/visacashapprb.png" }
  ],
  Force_india: [
    { start: 2010, end: 2018, name: "Force India", color: "#ffe6ddff", logo: "/static/images/constructors/forceindia.png" }
  ],
  Racing_point: [
    { start: 2018, end: 2020, name: "Racing Point", color: "#F596C8", logo: "/static/images/constructors/racingpoint.png" }
  ],
  Aston_martin: [
    { start: 2021, end: 2024, name: "Aston Martin", color: "#006F62", logo: "/static/images/constructors/astonmartin.png" }
  ],
  Renault: [
    { start: 2010, end: 2011, name: "Renault", color: "#FFD700", logo: "/static/images/constructors/renault.png" },
    { start: 2016, end: 2020, name: "Renault", color: "#FFD700", logo: "/static/images/constructors/renault.png" }
  ],
  Lotus: [
    { start: 2010, end: 2011, name: "Lotus Racing", color: "#006400", logo: "/static/images/constructors/lotusracing.png" },
    { start: 2012, end: 2015, name: "Lotus F1 Team", color: "#000", logo: "/static/images/constructors/lotus.png" }
  ],
  Lotus_racing: [
    { start: 2010, end: 2011, name: "Lotus Racing", color: "#006400", logo: "/static/images/constructors/lotusracing.png" },
  ],
  Lotus_f1: [
    { start: 2012, end: 2015, name: "Lotus F1 Team", color: "#000", logo: "/static/images/constructors/lotus.png" }
  ],
  Alpine: [
    { start: 2021, end: 2024, name: "Alpine", color: "#2293D1", logo: "/static/images/constructors/alpine.png" }
  ],
  Haas: [
    { start: 2016, end: 2024, name: "Haas", color: "#f0e9e9ff", logo: "/static/images/constructors/haas.png" }
  ],
  Caterham: [
    { start: 2012, end: 2014, name: "Caterham", color: "#006400", logo: "/static/images/constructors/caterham.png" }
  ],
  Virgin: [
    { start: 2010, end: 2011, name: "Virgin Racing", color: "#FF0000", logo: "/static/images/constructors/virgin.png" }
  ],
  Hrt: [
    { start: 2010, end: 2011, name: "HRT", color: "#A6904F", logo: "/static/images/constructors/hrt.png" }
  ],
  Marussia: [
    { start: 2012, end: 2014, name: "Marussia", color: "#FF0000", logo: "/static/images/constructors/marussia.png" }
  ],
  Manor: [
    { start: 2015, end: 2015, name: "Manor Marussia", color: "#FF0000", logo: "/static/images/constructors/manor.png" },
    { start: 2016, end: 2016, name: "Manor", color: "#FF0000", logo: "/static/images/constructors/manor.png" }
  ]
};

document.addEventListener('DOMContentLoaded', function () {
  const carousel = document.getElementById('trackCarousel');
  if (!carousel) return;

  const items = Array.from(carousel.querySelectorAll('.box'));
  if (items.length === 0) return;

  const wrapPrev = document.querySelector('.carousel-btn-wrap.prev');
  const wrapNext = document.querySelector('.carousel-btn-wrap.next');

  const btnPrev = document.querySelector('.carousel-btn.prev');
  const btnNext = document.querySelector('.carousel-btn.next');

  function centerItem(el, behaviour = 'smooth') {
    const left = el.offsetLeft - (carousel.clientWidth - el.clientWidth) / 2;
    carousel.scrollTo({ left, behavior: behaviour });
  }

  /* Insert start/finish markers into the carousel */
  function insertImgLineMarkers(carousel) {
    if (!carousel) return;

    if (carousel.querySelector('.line-marker.start') || carousel.querySelector('.line-marker.finish')) return;

    function makeMarker(name, src, alt) {
      const wrapper = document.createElement('div');
      wrapper.className = `line-marker ${name}`;
      wrapper.setAttribute('aria-hidden', 'true');

      const img = document.createElement('img');
      img.src = src;
      img.alt = alt || '';
      img.loading = 'lazy';

      img.style.visibility = 'hidden';
      img.style.display = 'block';

      wrapper.appendChild(img);
      return wrapper;
    }

    const startMarker = makeMarker('start', '/static/images/line-start.jpg', 'Start line');
    const finishMarker = makeMarker('finish', '/static/images/line-finish.jpg', 'Finish line');

    const firstChild = carousel.firstElementChild;
    if (firstChild) carousel.insertBefore(startMarker, firstChild);
    carousel.appendChild(finishMarker);

    function updateMarkerHeights() {
      const imgs = carousel.querySelectorAll('.line-marker img');
      imgs.forEach(img => {
        img.style.visibility = 'visible';
      });
    }

    const imgs = carousel.querySelectorAll('.line-marker img');
    imgs.forEach(img => {
      if (img.complete) {
        updateMarkerHeights();
      } else {
        img.addEventListener('load', updateMarkerHeights, { once: true });
      }
    });

    let ro;
    if (window.ResizeObserver) {
      ro = new ResizeObserver(() => {
        updateMarkerHeights();
      });
      ro.observe(carousel);
    }

    window.addEventListener('resize', () => {
      clearTimeout(window.__lineMarkerResizeTimer);
      window.__lineMarkerResizeTimer = setTimeout(updateMarkerHeights, 80);
    });
  }

  insertImgLineMarkers(carousel);

  function applyFlagBackgrounds() {
    const serverEl = document.getElementById('server-data');
    if (!serverEl) return;
    let server;
    try { server = JSON.parse(serverEl.textContent || '{}'); }
    catch { return; }

    const tracks = server.tracks || [];
    const boxes = Array.from(document.querySelectorAll('.box'));

    boxes.forEach(box => {
        const attr = box.getAttribute('data-detailed-flag') || '';
        const idx = parseInt(box.getAttribute('data-index'), 10);
        const fallbackTrack = (typeof idx === 'number' && tracks[idx]) ? tracks[idx] : null;
        const filename = attr || (fallbackTrack && fallbackTrack.detailed_flag) || '';

        const bgDiv = box.querySelector('.box-bg');
        if (filename && bgDiv) {
            const url = '/static/images/textured-flags/' + encodeURIComponent(filename);
            bgDiv.style.backgroundImage = `url("${url}")`;
            box.classList.add('has-detailed-bg');
        } else if (bgDiv) {
            bgDiv.style.backgroundImage = '';
            box.classList.remove('has-detailed-bg');
        }
    });
  }

  applyFlagBackgrounds();

  function setActiveNearest() {
    const center = carousel.scrollLeft + carousel.clientWidth / 2;
    let nearest = null;
    let minDist = Infinity;

    const currentItems = Array.from(carousel.querySelectorAll('.box'));
    currentItems.forEach(item => {
      const itemCenter = item.offsetLeft + item.offsetWidth / 2;
      const dist = Math.abs(center - itemCenter);
      if (dist < minDist) {
        minDist = dist;
        nearest = item;
      }
    });

    currentItems.forEach(i => i.classList.toggle('active', i === nearest));

    const quickpickArrow = document.getElementById('quickpick-arrow');
    const quickpickItems = Array.from(document.querySelectorAll('.quickpick-item'));

    function updateArrow() {
      const active = carousel.querySelector('.box.active');
      if (!active) return;

      const idx = currentItems.indexOf(active);
      if (idx === -1 || !quickpickItems[idx]) return;

      const target = quickpickItems[idx];
      const rect = target.getBoundingClientRect();
      const barRect = document.querySelector('.quickpick-bar').getBoundingClientRect();

      const centerPos = rect.left + rect.width / 2 - barRect.left;
      quickpickArrow.style.left = `${centerPos - 8}px`;
    }

    updateArrow();
    window.addEventListener('resize', updateArrow);
  }

  function updateArrowsVisibility() {
    if (!wrapPrev || !wrapNext) return;

    const scLeft = Math.max(0, carousel.scrollLeft);
    const maxScroll = Math.max(0, carousel.scrollWidth - carousel.clientWidth);
    const epsilon = 6;

    if (scLeft <= epsilon) {
      wrapPrev.classList.add('hidden');
      wrapPrev.setAttribute('aria-hidden', 'true');
    } else {
      wrapPrev.classList.remove('hidden');
      wrapPrev.removeAttribute('aria-hidden');
    }

    if (scLeft >= (maxScroll - epsilon)) {
      wrapNext.classList.add('hidden');
      wrapNext.setAttribute('aria-hidden', 'true');
    } else {
      wrapNext.classList.remove('hidden');
      wrapNext.removeAttribute('aria-hidden');
    }
  }

  let scrollTimer = null;
  carousel.addEventListener('scroll', function () {
    setActiveNearest();
    updateArrowsVisibility();
    if (scrollTimer) clearTimeout(scrollTimer);
    scrollTimer = setTimeout(() => {
      setActiveNearest();
      updateArrowsVisibility();
    }, 110);
  });

  window.addEventListener('resize', () => {
    setActiveNearest();
    updateArrowsVisibility();
  });

  function indexOfActive() {
    return items.findIndex(i => i.classList.contains('active'));
  }

  if (btnPrev) btnPrev.addEventListener('click', function () {
    if (wrapPrev && wrapPrev.classList.contains('hidden')) return;
    let idx = indexOfActive();
    if (idx <= 0) idx = 0;
    else idx = idx - 1;
    if (items[idx]) centerItem(items[idx]);
  });

  if (btnNext) btnNext.addEventListener('click', function () {
    if (wrapNext && wrapNext.classList.contains('hidden')) return;
    let idx = indexOfActive();
    if (idx === -1) idx = 0;
    if (idx >= items.length - 1) idx = items.length - 1;
    else idx = idx + 1;
    if (items[idx]) centerItem(items[idx]);
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowLeft') btnPrev && !btnPrev.classList.contains('hidden') && btnPrev.click();
    if (e.key === 'ArrowRight') btnNext && !btnNext.classList.contains('hidden') && btnNext.click();
  });

  /* initial carousel position logic */
  const serverDataEl = document.getElementById('server-data');
  const serverData = serverDataEl ? JSON.parse(serverDataEl.textContent) : {};
  const preferRound = window.NEXT_ROUND || serverData.next_round || 1;
  const startIndex = items.findIndex(i => parseInt(i.getAttribute('data-round'), 10) === preferRound);
  const targetIndex = startIndex !== -1 ? startIndex : Math.min(Math.max(preferRound - 1, 0), items.length - 1);

  setTimeout(() => {
    if (items[targetIndex]) {
      centerItem(items[targetIndex], 'auto');
      setTimeout(() => {
        setActiveNearest();
        updateArrowsVisibility();
      }, 80);
    } else {
      setActiveNearest();
      updateArrowsVisibility();
    }
  }, 60);

  loadStandings();

  const toggleButtons = document.querySelectorAll(".toggle-btn");
  const driverPanel = document.querySelector(".driver-championship");
  const constructorPanel = document.querySelector(".constructor-championship");

  toggleButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      toggleButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      const target = btn.getAttribute("data-target");
      if (target === "drivers") {
        driverPanel.style.display = "block";
        constructorPanel.style.display = "none";
      } else {
        driverPanel.style.display = "none";
        constructorPanel.style.display = "block";
      }
    });
  });
});

/* ---------- Helpers ---------- */

function createTrophySVG() {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 512 512");

  const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  rect.setAttribute("x", "141.576");
  rect.setAttribute("y", "464");
  rect.setAttribute("width", "221.09");
  rect.setAttribute("height", "48");
  svg.appendChild(rect);

  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute(
    "d",
    "M389.818,16.484c0-10.168,0-16.484,0-16.484H250.182H110.545c0,0,0,6.316,0,16.484H22.723h-0.18h-0.24v80.484 c0,28.688,10.26,55.172,28.891,74.578c18.957,19.746,45.358,31.637,78.666,35.52c31.883,49.887,92.047,77.332,92.047,100.426 c0,31.418-31.42,84.828-31.42,84.828v34.25v0.07v0.242h119.391V392.32c0,0-31.418-53.41-31.418-84.828 c0-22.937,59.326-50.164,91.373-99.398c39.158-2.187,69.742-14.43,90.974-36.547c18.631-19.406,28.891-45.89,28.891-74.578V16.484 H389.818z M59.152,96.969V53.332h51.393c0,30.258,0,66.66,0,90.184c0,6.726,0.707,13.106,1.791,19.289 c0.162,1.156,0.258,2.308,0.446,3.469C65.231,152.387,59.152,115.039,59.152,96.969z M190.254,146.359l-0.094,41.715 c-23.192-10.004-44.705-43.114-44.705-56.367c0-13.278,0-92.918,0-92.918h44.799C190.254,38.789,190.254,92.039,190.254,146.359z M452.848,96.969c0,15.852-4.676,46.531-37.912,63.203c-7.715,3.844-16.972,6.922-28.056,8.879 c1.883-8.039,2.939-16.531,2.939-25.535c0-23.524,0-59.926,0-90.184h63.03V96.969z"
  );
  svg.appendChild(path);

  return svg;
}

function getConstructorInfo(constructorKey, season) {
    const ranges = constructors[constructorKey];
    if (!ranges) {
        console.warn("Constructor key not found:", constructorKey);
        return {
            name: constructorKey,
            color: "#ccc",
            logo: "/static/images/constructors/constructor-placeholder.png"
        };
    }

    const match = ranges.find(r => season >= r.start && season <= r.end);
    if (match) {
        return {
            name: match.name,
            color: match.color,
            logo: match.logo
        };
    }

    const fallback = ranges[ranges.length - 1];
    console.warn("No season match, using fallback:", fallback);
    return {
        name: fallback.name,
        color: fallback.color,
        logo: fallback.logo
    };
}

function hideSpinnerForList(listSelector) {
    const list = document.querySelector(listSelector);
    if (!list) return;
    const spinner = list.parentElement.querySelector('.spinner');
    if (spinner) spinner.style.display = 'none';
}

function capitalize(str) {
    if (!str && str !== 0) return '';
    str = String(str);
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function ordinal(n) {
    const s = ["th", "st", "nd", "rd"], v = n % 100;
    return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

function safeMetric(value, decimals = 2) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return 'N/A';
    if (typeof value === 'number') return value.toFixed(decimals);
    return String(value);
}

async function loadStandings() {
    const seasonAttr = document.body.getAttribute('data-season');
    const season = seasonAttr ? parseInt(seasonAttr, 10) : new Date().getFullYear();

    let standings;
    try {
        const resp = await fetch(`/ml/standings/${season}`);
        if (!resp.ok) throw new Error(`Failed to fetch standings for season ${season}: ${resp.status}`);
        standings = await resp.json();
    } catch (err) {
        console.error('Error fetching standings:', err);
        return;
    }

    if (Array.isArray(standings.constructor_standings)) {
        populateConstructorStandings(standings.constructor_standings, season);
    }

    if (Array.isArray(standings.driver_standings)) {
        populateDriverStandings(standings.driver_standings, season);
    }
}

function createPredictionItem(
    position,
    imageUrl,
    name,
    firsts,
    seconds,
    thirds,
    metricValue,
    isConstructor,
    constructorName,
    metricClass,
    showMetric,
    isProbability,
    changeType,
    season
) {
    const li = document.createElement("li");

    // Position
    const posSpan = document.createElement("span");
    posSpan.classList.add("position");
    posSpan.textContent = ordinal(position);
    li.appendChild(posSpan);

    // Driver/Constructor Info
    const driverInfo = document.createElement("div");
    driverInfo.classList.add("driver-info");

    const imageWrapper = document.createElement("div");
    imageWrapper.classList.add("image-wrapper");

    let displayName = name;
    let bgColor = "#ccc";
    let logoUrl = null;

    if (constructorName) {
      const info = getConstructorInfo(constructorName, season);
      if (isConstructor) {
          displayName = info.name || name;
          logoUrl = info.logo || '/static/images/constructors/constructor-placeholder.png';
      }
      bgColor = info.color || "#ccc";
    }

    imageWrapper.style.backgroundColor = bgColor;

    const img = document.createElement("img");
    img.alt = displayName;
    img.classList.add(isConstructor ? "constructor-img" : "driver-img");

    if (isConstructor) {
        img.src = logoUrl;
    } else {
        const lastName = (name || '').split(' ').slice(-1)[0].toLowerCase().replace(/[^a-z0-9]/g, '');
        const defaultDriverPath = `/static/images/drivers/${lastName}.png`;
        const placeholder = '/static/images/drivers/driver-placeholder.png';
        img.src = imageUrl || defaultDriverPath;
        img.onerror = function () {
            this.onerror = null;
            this.src = placeholder;
            this.className = 'static-img';
        };
    }

    imageWrapper.appendChild(img);
    driverInfo.appendChild(imageWrapper);

    const nameSpan = document.createElement("span");
    nameSpan.textContent = displayName;
    driverInfo.appendChild(nameSpan);

    li.appendChild(driverInfo);

    const podiumWrapper = document.createElement("div");
    podiumWrapper.classList.add("podium-wrapper");

    if (firsts != 0) {
        const firstsWrapper = document.createElement("div");
        firstsWrapper.classList.add("firsts-wrapper");
        const trophy = createTrophySVG();
        trophy.setAttribute("class", "trophy-icon first");
        firstsWrapper.appendChild(trophy);
        const firstspan = document.createElement("span");
        firstspan.classList.add("count-span");
        firstspan.textContent = "x" + firsts;
        firstsWrapper.appendChild(firstspan);
        podiumWrapper.appendChild(firstsWrapper);
    }

    if (seconds != 0) {
        const secondsWrapper = document.createElement("div");
        secondsWrapper.classList.add("seconds-wrapper");
        const trophy = createTrophySVG();
        trophy.setAttribute("class", "trophy-icon second");
        secondsWrapper.appendChild(trophy);
        const secondspan = document.createElement("span");
        secondspan.classList.add("count-span");
        secondspan.textContent = "x" + seconds;
        secondsWrapper.appendChild(secondspan);
        podiumWrapper.appendChild(secondsWrapper);
    }

    if (thirds != 0) {
        const thirdsWrapper = document.createElement("div");
        thirdsWrapper.classList.add("thirds-wrapper");
        const trophy = createTrophySVG();
        trophy.setAttribute("class", "trophy-icon third");
        thirdsWrapper.appendChild(trophy);
        const thirdspan = document.createElement("span");
        thirdspan.classList.add("count-span");
        thirdspan.textContent = "x" + thirds;
        thirdsWrapper.appendChild(thirdspan);
        podiumWrapper.appendChild(thirdsWrapper);
    }

    li.appendChild(podiumWrapper);

    if (showMetric) {
        const metricWrapper = document.createElement("div");
        metricWrapper.classList.add("metric-wrapper", `metric-${metricClass}`);
        const metricSpan = document.createElement("span");
        metricSpan.classList.add("gp-metric", `metric-${metricClass}`);

        if (isProbability) {
            metricSpan.textContent = `${safeMetric(metricValue)}%`;
        } else {
            metricSpan.textContent = `${safeMetric(metricValue, 0)} pts`;
        }

        metricSpan.style.color = "rgba(220, 220, 220, 1)";
        metricWrapper.appendChild(metricSpan);
        li.appendChild(metricWrapper);
    }

    return li;
}

function populateConstructorStandings(constructors, season) {
    const list = document.querySelector('.constructor-standings');
    if (!list) return;

    list.innerHTML = '';
    hideSpinnerForList('.constructor-standings');

    constructors.forEach((team, index) => {
        const name = team.constructor || 'Unknown';
        const firsts = team.firsts ?? 0;
        const seconds = team.seconds ?? 0;
        const thirds = team.thirds ?? 0;
        const points = team.points ?? 0;

        const li = createPredictionItem(index + 1, null, name, firsts, seconds, thirds, points, true, name, 'points', true, false, 'neutral', season);
        list.appendChild(li);
    });
}

function populateDriverStandings(drivers, season) {
    const list = document.querySelector('.driver-standings');
    if (!list) return;

    list.innerHTML = '';
    hideSpinnerForList('.driver-standings');

    drivers.forEach((drv, index) => {
        const name = drv.driver || 'Unknown';
        const constructorName = drv.constructor || null;
        const firsts = drv.firsts ?? 0;
        const seconds = drv.seconds ?? 0;
        const thirds = drv.thirds ?? 0;
        const points = drv.points ?? 0;

        const li = createPredictionItem(index + 1, null, name, firsts, seconds, thirds, points, false, constructorName, 'points', true, false, 'neutral', season);
        list.appendChild(li);
    });
}

(function () {
  const carousel = document.querySelector('.carousel');
  const btns = Array.from(document.querySelectorAll('.carousel-btn'));
  if (!carousel || btns.length === 0) return;

  const MIN_H = 40;
  const MAX_H = 500;
  const RATIO = 0.7;

  function updateButtonHeights() {
    const h = carousel.clientHeight || Math.round(carousel.getBoundingClientRect().height);
    if (!h || h <= 0) return;

    const targetH = Math.max(MIN_H, Math.min(MAX_H, Math.round(h * RATIO)));

    btns.forEach(b => {
      b.style.height = `${targetH}px`;

      const w = b.offsetWidth;
      const radius = Math.round(w * 0.25);
      b.style.borderRadius = `${radius}px`;
    });
  }

  let timer = null;
  function schedule(delay = 80) {
    clearTimeout(timer);
    timer = setTimeout(updateButtonHeights, delay);
  }

  window.addEventListener('load', () => {
    schedule(50);
    carousel.querySelectorAll('img').forEach(img => {
      if (!img.complete) img.addEventListener('load', () => schedule(50), { once: true });
    });
  });

  window.addEventListener('resize', () => schedule(120));
  window.addEventListener('orientationchange', () => schedule(120));

  if ('ResizeObserver' in window) {
    new ResizeObserver(() => schedule(40)).observe(carousel);
  }

  schedule(20);
})();

(function(){
  const trigger = document.getElementById('trackTrigger');
  const menu = document.getElementById('trackDropdown');
  const label = trigger.querySelector('.track-select-label');

  function openMenu() {
    const rect = trigger.getBoundingClientRect();
    menu.style.left = `${rect.left}px`;
    menu.style.top  = `${rect.bottom + 6}px`;
    menu.style.minWidth = `${rect.width}px`;
    menu.hidden = false;
    trigger.setAttribute('aria-expanded', 'true');
  }
  function closeMenu() {
    menu.hidden = true;
    trigger.setAttribute('aria-expanded', 'false');
  }
  function toggleMenu() {
    if (menu.hidden) openMenu(); else closeMenu();
  }

  trigger.addEventListener('click', (e) => {
    e.stopPropagation();
    toggleMenu();
  });

  menu.addEventListener('click', (e) => {
    const li = e.target.closest('.track-select-item');
    if (!li) return;
    const name = li.querySelector('.track-select-name')?.textContent?.trim() || 'Track';
    const href = li.dataset.href;
    label.textContent = name;
    closeMenu();
    if (href) window.location.href = href;
  });

  menu.addEventListener('keydown', (e) => {
    const items = [...menu.querySelectorAll('.track-select-item')];
    const idx = items.indexOf(document.activeElement);
    if (e.key === 'ArrowDown') { e.preventDefault(); (items[idx+1] || items[0]).focus(); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); (items[idx-1] || items[items.length-1]).focus(); }
    else if (e.key === 'Enter') { document.activeElement.click(); }
    else if (e.key === 'Escape') { closeMenu(); trigger.focus(); }
  });

  document.addEventListener('click', (e) => {
    if (!menu.hidden && !trigger.contains(e.target) && !menu.contains(e.target)) closeMenu();
  });
  window.addEventListener('resize', () => { if (!menu.hidden) openMenu(); });
  window.addEventListener('scroll', () => { if (!menu.hidden) openMenu(); }, true);

  const carousel = document.querySelector('.carousel');
  if (!carousel) return;

  function sizeLineMarkers() {
    const kids = Array.from(carousel.children).filter(el => !el.classList.contains('line-marker'));
    const h = Math.max(0, ...kids.map(el => el.offsetHeight));
    if (!h) return;
    carousel.querySelectorAll('.line-marker img').forEach(img => {
      img.style.height = h + 'px';
      img.style.width = 'auto';
      img.style.maxHeight = 'none';
      img.style.visibility = 'visible';
    });
  }

  sizeLineMarkers();

  const debounce = (fn, d=60) => { let t; return (...a)=>{ clearTimeout(t); t=setTimeout(()=>fn(...a), d); }; };
  const rerun = debounce(sizeLineMarkers, 80);

  window.addEventListener('load', rerun);
  window.addEventListener('resize', rerun);
  window.addEventListener('orientationchange', rerun);

  carousel.querySelectorAll('img').forEach(img => {
    if (!img.complete) img.addEventListener('load', rerun, { once: true });
  });

  if (window.ResizeObserver) {
    const ro = new ResizeObserver(rerun);
    ro.observe(carousel);
  }
})();

function rebalanceQuickpick() {
  const quickpick = document.querySelector(".quickpick-flags");
  const arrow = document.getElementById("quickpick-arrow");

  if (!quickpick || !arrow) return;

  const items = [...quickpick.querySelectorAll(".quickpick-item")];
  const tops = new Set(items.map(it => it.offsetTop));
  const rows = tops.size;

  arrow.style.display = rows > 1 ? "none" : "";
}

window.addEventListener("load", rebalanceQuickpick);
window.addEventListener("resize", rebalanceQuickpick);
window.addEventListener("orientationchange", rebalanceQuickpick);