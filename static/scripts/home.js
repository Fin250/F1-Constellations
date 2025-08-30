const constructorNameMap = {
    "red_bull": "Red Bull Racing",
    "mercedes": "Mercedes",
    "ferrari": "Ferrari",
    "mclaren": "McLaren",
    "aston_martin": "Aston Martin",
    "alpine": "Alpine",
    "sauber": "Kick Sauber",
    "williams": "Williams",
    "rb": "Visa Cash App RB",
    "haas": "Haas"
};

const constructorColors = {
    "Red Bull Racing": "#3671C6",
    "McLaren": "#FF8000",
    "Mercedes": "#00D2BE",
    "Ferrari": "#DC0000",
    "Aston Martin": "#006F62",
    "Alpine": "#2293D1",
    "Williams": "#005AFF",
    "Visa Cash App RB": "#2B4562",
    "Haas": "#f0e9e9ff",
    "Kick Sauber": "#52E252"
};

const constructorLogos = {
    "Red Bull Racing": "/static/images/constructors/redbull.png",
    "McLaren": "/static/images/constructors/mclaren.png",
    "Mercedes": "/static/images/constructors/mercedes.png",
    "Ferrari": "/static/images/constructors/ferrari.png",
    "Aston Martin": "/static/images/constructors/astonmartin.png",
    "Alpine": "/static/images/constructors/alpine.png",
    "Williams": "/static/images/constructors/williams.png",
    "Visa Cash App RB": "/static/images/constructors/visacashapprb.png",
    "Haas": "/static/images/constructors/haas.png",
    "Kick Sauber": "/static/images/constructors/kicksauber.png"
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
      const h = Math.max(0, carousel.clientHeight);
      if (h <= 0) return;
      const imgs = carousel.querySelectorAll('.line-marker img');
      imgs.forEach(img => {
        img.style.height = `${h}px`;
        img.style.width = 'auto';
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
    try {
      server = JSON.parse(serverEl.textContent || '{}');
    } catch (err) {
      return;
    }
    const tracks = server.tracks || [];
    const boxes = Array.from(carousel.querySelectorAll('.box'));

    boxes.forEach(box => {
      const attr = box.getAttribute('data-detailed-flag') || '';
      const idx = parseInt(box.getAttribute('data-index'), 10);
      const fallbackTrack = (typeof idx === 'number' && tracks[idx]) ? tracks[idx] : null;
      const filename = attr || (fallbackTrack && fallbackTrack.detailed_flag) || '';

      if (filename) {
        const url = '/static/images/textured-flags/' + encodeURIComponent(filename);
        const gradient = 'linear-gradient(135deg, rgba(24,24,24,0.72) 0%, rgba(30,27,27,0.48) 50%, rgba(19,14,14,0.58) 100%)';
        box.style.backgroundImage = `${gradient}, url("${url}")`;
        box.classList.add('has-detailed-bg');
      } else {
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
});

/* ---------- Helpers ---------- */

function normalizeConstructorName(rawName) {
    if (!rawName) return 'Unknown';
    const key = rawName.toLowerCase().trim();
    return constructorNameMap[key] || rawName;
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
    let standings;
    try {
        const resp = await fetch(`/ml/standings`);
        if (!resp.ok) throw new Error(`Failed to fetch standings: ${resp.status}`);
        standings = await resp.json();
    } catch (err) {
        console.error('Error fetching standings:', err);
        return;
    }

    if (Array.isArray(standings.constructor_standings)) {
        populateConstructorStandings(standings.constructor_standings);
    }

    if (Array.isArray(standings.driver_standings)) {
        populateDriverStandings(standings.driver_standings);
    }
}

function createPredictionItem(
    position,
    imageUrl,
    name,
    metricValue,
    isConstructor,
    constructorName,
    metricClass,
    showMetric,
    isProbability,
    changeType
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

    // Team colour
    if (constructorName && constructorColors[normalizeConstructorName(constructorName)]) {
        imageWrapper.style.backgroundColor = constructorColors[normalizeConstructorName(constructorName)];
    } else {
        imageWrapper.style.backgroundColor = "#ccc";
    }

    const img = document.createElement("img");
    img.src = imageUrl;
    img.alt = name;
    img.classList.add(isConstructor ? "constructor-img" : "driver-img");

    imageWrapper.appendChild(img);
    driverInfo.appendChild(imageWrapper);

    const nameSpan = document.createElement("span");
    nameSpan.textContent = name;
    driverInfo.appendChild(nameSpan);

    li.appendChild(driverInfo);

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

        metricSpan.style.color = "rgb(202, 194, 194)";

        metricWrapper.appendChild(metricSpan);
        li.appendChild(metricWrapper);
    }

    return li;
}

function populateConstructorStandings(constructors) {
    const list = document.querySelector('.constructor-standings');
    if (!list) return;

    list.innerHTML = '';
    hideSpinnerForList('.constructor-standings');

    constructors.forEach((team, index) => {
        const name = team.constructor || 'Unknown';
        const points = team.points ?? 0;
        const imageUrl = constructorLogos[name] || `/static/images/constructors/constructor-placeholder.jpg`;

        const li = createPredictionItem(index + 1, imageUrl, name, points, true, name, 'points', true, false, 'neutral');
        list.appendChild(li);
    });
}

function populateDriverStandings(drivers) {
    const list = document.querySelector('.driver-standings');
    if (!list) return;

    list.innerHTML = '';
    hideSpinnerForList('.driver-standings');

    drivers.forEach((drv, index) => {
        const name = drv.driver || 'Unknown';
        const constructorName = drv.constructor || null;
        const points = drv.points ?? 0;
        const imageUrl = drv.image || `/static/images/drivers/driver-placeholder.png`;

        const li = createPredictionItem(index + 1, imageUrl, name, points, false, constructorName, 'points', true, false, 'neutral');
        list.appendChild(li);
    });
}

document.addEventListener("DOMContentLoaded", () => {
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
