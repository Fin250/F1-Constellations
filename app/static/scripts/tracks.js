const constructors = {
  Red_bull: [
    { start: 2010, end: 2025, name: "Red Bull Racing", color: "#3671C6", logo: "/static/images/constructors/redbull.png" }
  ],
  Mercedes: [
    { start: 2010, end: 2025, name: "Mercedes", color: "#00D2BE", logo: "/static/images/constructors/mercedes.png" }
  ],
  Ferrari: [
    { start: 2010, end: 2025, name: "Ferrari", color: "#DC0000", logo: "/static/images/constructors/ferrari.png" }
  ],
  Mclaren: [
    { start: 2010, end: 2025, name: "McLaren", color: "#FF8000", logo: "/static/images/constructors/mclaren.png" }
  ],
  Williams: [
    { start: 2010, end: 2025, name: "Williams", color: "#005AFF", logo: "/static/images/constructors/williams.png" }
  ],
  Sauber: [
    { start: 2010, end: 2018, name: "Sauber F1 Team", color: "#9B0000", logo: "/static/images/constructors/sauber.png" },
    { start: 2024, end: 2025, name: "Kick Sauber", color: "#52E252", logo: "/static/images/constructors/kicksauber.png" }
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
    { start: 2024, end: 2025, name: "Visa Cash App RB", color: "#2B4562", logo: "/static/images/constructors/visacashapprb.png" }
  ],
  Force_india: [
    { start: 2010, end: 2018, name: "Force India", color: "#ffe6ddff", logo: "/static/images/constructors/forceindia.png" }
  ],
  Racing_point: [
    { start: 2018, end: 2020, name: "Racing Point", color: "#F596C8", logo: "/static/images/constructors/racingpoint.png" }
  ],
  Aston_martin: [
    { start: 2021, end: 2025, name: "Aston Martin", color: "#006F62", logo: "/static/images/constructors/astonmartin.png" }
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
    { start: 2021, end: 2025, name: "Alpine", color: "#2293D1", logo: "/static/images/constructors/alpine.png" }
  ],
  Haas: [
    { start: 2016, end: 2025, name: "Haas", color: "#f0e9e9ff", logo: "/static/images/constructors/haas.png" }
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

const driverDataMap = {};

document.addEventListener("DOMContentLoaded", async function () {
    const body = document.body;
    const seasonAttr = body.getAttribute('data-season');
    const roundAttr = body.getAttribute('data-round');

    if (!seasonAttr || !roundAttr) {
        console.error("Missing 'data-season' or 'data-round' on body.");
        return;
    }

    const season = parseInt(seasonAttr, 10);
    const round = parseInt(roundAttr, 10);

    if (isNaN(season) || isNaN(round)) {
        console.error("Invalid season or round number in body attributes.");
        return;
    }

    // fetch current round data
    let currentData;
    try {
        const resp = await fetch(`/ml/${season}/${round}`);
        if (!resp.ok) throw new Error(`Failed to fetch predictions: ${resp.status}`);
        currentData = await resp.json();
    } catch (err) {
        console.error('Error fetching current round predictions:', err);
        return;
    }

    // fetch previous round data
    let prevData = null;
    if (round > 1) {
        try {
            const respPrev = await fetch(`/ml/${season}/${round - 1}`);
            if (respPrev.ok) {
                prevData = await respPrev.json();
            } else {
                prevData = null;
            }
        } catch (err) {
            prevData = null;
        }
    }

    const metadata = currentData.driver_metadata || {};

    if (!currentData.gp_results || !Array.isArray(currentData.gp_results.predictions)) {
        console.error("Invalid or missing gp_results.predictions");
    } else {
        const prevGpPreds = prevData && prevData.gp_results && Array.isArray(prevData.gp_results.predictions)
            ? prevData.gp_results.predictions
            : null;
        populateGPResults(currentData.gp_results.predictions, metadata, prevGpPreds, round, seasonAttr);
    }

    if (!Array.isArray(currentData.driver_strength)) {
        console.error("Invalid or missing driver_strength array");
    } else {
        const prevDrivers = prevData && Array.isArray(prevData.driver_strength) ? prevData.driver_strength : null;
        populateDriverStrength(currentData.driver_strength, metadata, prevDrivers, round, seasonAttr);
    }

    if (!Array.isArray(currentData.constructor_strength)) {
        console.error("Invalid or missing constructor_strength array");
    } else {
        const prevConstructors = prevData && Array.isArray(prevData.constructor_strength) ? prevData.constructor_strength : null;
        populateConstructorStrength(currentData.constructor_strength, prevConstructors, round, seasonAttr);
    }
});

/* ---------- Helpers ---------- */

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

function getStrengthColor(strength) {
    if (strength === 'N/A') return '#888';
    const val = Number(strength);
    if (Number.isNaN(val)) return '#888';
    if (val >= 90) return '#00FF00';
    if (val <= 30) return '#FF1E1E';
    const green = Math.round(((val - 30) / 60) * 255);
    const red = 255 - green;
    return `rgb(${red},${green},0)`;
}

function getProbabilityColor(probStr) {
    if (probStr === 'N/A') return '#888';
    const val = parseFloat(String(probStr).replace('%', ''));
    if (Number.isNaN(val)) return '#888';
    if (val >= 25) return 'rgb(0,255,0)';
    if (val <= 0) return 'rgb(255,0,0)';
    const ratio = val / 25;
    const green = Math.round(ratio * 255);
    const red = 255 - green;
    return `rgb(${red},${green},0)`;
}

function hideSpinnerForList(listSelector) {
    const list = document.querySelector(listSelector);
    if (!list) return;
    const spinner = list.parentElement.querySelector('.spinner');
    if (spinner) spinner.style.display = 'none';
}

function createBookmarkSVG() {
    const svgNS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("width", "18");
    svg.setAttribute("height", "18");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.classList.add('change-icon', 'change-new');

    const path = document.createElementNS(svgNS, "path");
    path.setAttribute("fill", "currentColor");
    path.setAttribute("d", "M6 2h12v18l-6-4-6 4V2z");

    svg.appendChild(path);
    return svg;
}

function createSparkleSVG() {
    const svgNS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("width", "18");
    svg.setAttribute("height", "18");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.classList.add('change-icon', 'change-new');

    const p1 = document.createElementNS(svgNS, "path");
    p1.setAttribute("fill", "currentColor");
    p1.setAttribute("d", "M12 2l1.8 4.2L18 8l-4.2 1.8L12 14l-1.8-4.2L6 8l4.2-1.8L12 2z");

    const p2 = document.createElementNS(svgNS, "path");
    p2.setAttribute("fill", "currentColor");
    p2.setAttribute("d", "M19.5 14.5l.8 1.8 1.8.8-1.8.8-.8 1.8-.8-1.8-1.8-.8 1.8-.8.8-1.8z");

    svg.appendChild(p1);
    svg.appendChild(p2);
    return svg;
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

function computeChangeType(currentPos, prevPos, prevExists, roundNum) {
    if (!prevExists) {
        return (roundNum === 1) ? 'neutral' : (prevPos === undefined || prevPos === null ? 'new' : 'neutral');
    }
    if (prevPos === undefined || prevPos === null) return 'new';
    if (currentPos < prevPos) return 'up';
    if (currentPos > prevPos) return 'down';
    return 'neutral';
}

function createChangeIconSVG(type) {
    const svgNS = "http://www.w3.org/2000/svg";

    if (type === 'up' || type === 'down' || type === 'neutral') {
        const svg = document.createElementNS(svgNS, "svg");
        svg.setAttribute("width", "18");
        svg.setAttribute("height", "18");
        svg.setAttribute("viewBox", "0 0 24 24");
        svg.classList.add('change-icon', `change-${type}`);

        const path = document.createElementNS(svgNS, "path");
        path.setAttribute("fill", "currentColor");

        switch (type) {
            case 'up':
                path.setAttribute("d", "M12 5l7 12H5z");
                break;
            case 'down':
                path.setAttribute("d", "M12 19l-7-12h14z");
                break;
            case 'neutral':
            default:
                path.setAttribute("d", "M6 11h12v2H6z");
                break;
        }

        svg.appendChild(path);
        return svg;
    }

    return createBookmarkSVG();
}

/* Creates the list item */
function createPredictionItem(
    key,
    position,
    imageUrl,
    name,
    metricValue,
    isConstructor = false,
    constructorName = null,
    metricClass = 'metric',
    showMetric = true,
    isProbability = false,
    changeType = 'neutral',
    season = new Date().getFullYear()
) {
    const li = document.createElement('li');

    // position wrapper (icon + ordinal)
    const posWrapper = document.createElement('div');
    posWrapper.className = `position-wrapper change-${changeType}`;

    // change icon
    const iconSvg = createChangeIconSVG(changeType);
    posWrapper.appendChild(iconSvg);

    // ordinal span
    const ordSpan = document.createElement('span');
    ordSpan.className = 'position';
    ordSpan.textContent = ordinal(position);
    posWrapper.appendChild(ordSpan);

    // info container
    const infoDiv = document.createElement('div');
    infoDiv.className = isConstructor ? 'constructor-info' : 'driver-info';

    // image wrapper
    const imgWrapper = document.createElement('div');
    imgWrapper.className = 'image-wrapper';

    let displayName = name;
    let bgColor = '#ccc';
    let logoUrl = null;

    if (constructorName) {
        const info = getConstructorInfo(constructorName, season);
        if (isConstructor) {
            displayName = info.name || name;
            logoUrl = info.logo || '/static/images/constructors/constructor-placeholder.png';
        }
        bgColor = info.color || '#ccc';
    }

    imgWrapper.style.backgroundColor = bgColor;

    // create img element
    const img = document.createElement('img');
    img.alt = displayName;
    img.classList.add(isConstructor ? 'constructor-img' : 'driver-img');

    if (isConstructor) {
        const placeholder = '/static/images/constructors/constructor-placeholder.png';
        img.src = logoUrl || placeholder;
        img.onerror = function () {
            this.onerror = null;
            this.src = placeholder;
            this.className = 'static-img';
        };
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

    imgWrapper.appendChild(img);
    infoDiv.appendChild(imgWrapper);

    const nameSpan = document.createElement('span');
    nameSpan.textContent = displayName;
    infoDiv.appendChild(nameSpan);

    // metric
    const metricWrapper = document.createElement('div');
    metricWrapper.className = 'metric-wrapper';
    if (isProbability) metricWrapper.classList.add('metric-probability');

    if (showMetric && metricValue !== 'N/A') {
        const metricSpan = document.createElement('span');
        metricSpan.className = metricClass;
        metricSpan.textContent = metricValue;
        metricWrapper.appendChild(metricSpan);

        if (!isProbability) {
            const svgNS = "http://www.w3.org/2000/svg";
            const svg = document.createElementNS(svgNS, "svg");
            svg.setAttribute("viewBox", "0 0 40 40");
            svg.classList.add("metric-circle");

            const radius = 17.6;
            const circleBg = document.createElementNS(svgNS, "circle");
            circleBg.setAttribute("cx", "20");
            circleBg.setAttribute("cy", "20");
            circleBg.setAttribute("r", radius);
            circleBg.setAttribute("stroke", "#333");
            circleBg.setAttribute("stroke-width", "3.2");
            circleBg.setAttribute("fill", "none");
            circleBg.setAttribute("class", "circle-bg");

            const circleFg = document.createElementNS(svgNS, "circle");
            circleFg.setAttribute("cx", "20");
            circleFg.setAttribute("cy", "20");
            circleFg.setAttribute("r", radius);
            circleFg.setAttribute("stroke", getStrengthColor(metricValue));
            circleFg.setAttribute("stroke-width", "3.2");
            circleFg.setAttribute("fill", "none");
            circleFg.setAttribute("stroke-linecap", "round");
            circleFg.setAttribute("transform", "rotate(-90 20 20)");
            circleFg.setAttribute("class", "circle-fg");

            const percent = parseFloat(String(metricValue).replace('%', ''));
            const circumference = 2 * Math.PI * radius;
            const safePercent = (Number.isFinite(percent) ? percent : 0);
            circleFg.setAttribute("stroke-dasharray", circumference);
            circleFg.setAttribute("stroke-dashoffset", circumference * (1 - Math.min(Math.max(safePercent, 0), 100) / 100));

            svg.appendChild(circleBg);
            svg.appendChild(circleFg);
            metricWrapper.appendChild(svg);

            metricSpan.style.color = getStrengthColor(metricValue);
            metricSpan.classList.add('metric-with-circle');
        } else {
            metricSpan.classList.add('metric-prob');
            metricSpan.style.color = getProbabilityColor(metricValue);
        }
    }

    li.appendChild(posWrapper);
    li.appendChild(infoDiv);
    if (showMetric) li.appendChild(metricWrapper);

    driverDataMap[key] = driverDataMap[key] || {};
    driverDataMap[key].constructorColor = bgColor;
    li.dataset.driverKey = key;

    li.addEventListener("click", () => {
        const type = isConstructor ? 'constructor' : 'driver';
        openDriverModal(li.dataset.driverKey, type);
    });

    return li;
}

/* ---------- Population functions with change detection ---------- */

function populateGPResults(predictions, metadata, prevPredictions, roundNum, season) {
    const list = document.querySelector('.gp-results');
    if (!list) return;

    list.innerHTML = '';
    hideSpinnerForList('.gp-results');

    const prevExists = Array.isArray(prevPredictions);
    const prevMap = {};
    if (prevExists) {
        prevPredictions.forEach((p, idx) => {
            const key = (p.driver || '').toLowerCase();
            if (key) prevMap[key] = idx + 1;
        });
    }

    predictions.forEach((driver, index) => {
        const key = (driver.driver || '').toLowerCase();
        const meta = metadata[key] || {};
        const name = meta.full_name || capitalize(driver.driver) || 'Unknown';
        const imageUrl = `/static/images/drivers/${key}.png`;
        const constructorName = driver.constructor || null;

        const probabilityValue = (typeof driver.probability === 'number') 
            ? driver.probability.toFixed(1) 
            : String(driver.probability);
        const probability = `${probabilityValue}%`;

        const currentPos = index + 1;
        const prevPos = prevMap[key] !== undefined ? prevMap[key] : null;
        const changeType = computeChangeType(currentPos, prevPos, prevExists, roundNum);

        driverDataMap[key] = driverDataMap[key] || {};
        driverDataMap[key].probability = probability;
        driverDataMap[key].constructor = constructorName;
        driverDataMap[key].name = name;
        driverDataMap[key].fullName = meta.full_name || name;

        const li = createPredictionItem(
            key, currentPos, imageUrl, name, probability,
            false, constructorName, 'gp-metric',
            true, true, changeType, season
        );
        list.appendChild(li);
    });
    window.driverDataMap = driverDataMap;
}

function populateDriverStrength(drivers, metadata, prevDrivers, roundNum, season) {
    const list = document.querySelector('.driver-list');
    if (!list) return;

    list.innerHTML = '';
    hideSpinnerForList('.driver-list');

    const sorted = drivers.slice().sort((a, b) => {
        const va = (a && (typeof a.rating === 'number' ? a.rating : Number(a.rating || a.strength || -Infinity)));
        const vb = (b && (typeof b.rating === 'number' ? b.rating : Number(b.rating || b.strength || -Infinity)));
        return vb - va;
    });

    const prevExists = Array.isArray(prevDrivers);
    const prevMap = {};
    if (prevExists) {
        const prevSorted = prevDrivers.slice().sort((a, b) => {
            const va = (a && (typeof a.rating === 'number' ? a.rating : Number(a.rating || a.strength || -Infinity)));
            const vb = (b && (typeof b.rating === 'number' ? b.rating : Number(b.rating || b.strength || -Infinity)));
            return vb - va;
        });
        prevSorted.forEach((d, idx) => {
            const k = (d.driver || '').toLowerCase();
            if (k) prevMap[k] = idx + 1;
        });
    }

    sorted.forEach((d, index) => {
        const driverNameRaw = d.driver || d.Driver || '';
        const key = (driverNameRaw || '').toLowerCase();
        const meta = metadata[key] || {};
        const name = meta.full_name || capitalize(driverNameRaw) || 'Unknown';
        const imageUrl = `/static/images/drivers/${key}.png`;
        const constructorName = d.constructor || null;

        let ratingVal = null;
        if (d.rating !== undefined && d.rating !== null) {
            ratingVal = Number(d.rating);
        } else if (d.strength !== undefined && d.strength !== null) {
            ratingVal = Number(d.strength);
        }

        const strength = (ratingVal !== null && !Number.isNaN(ratingVal)) 
            ? safeMetric(ratingVal, 0) 
            : 'N/A';

        const currentPos = index + 1;
        const prevPos = prevMap[key] !== undefined ? prevMap[key] : null;
        const changeType = computeChangeType(currentPos, prevPos, prevExists, roundNum);

        driverDataMap[key] = driverDataMap[key] || {};
        driverDataMap[key].strength = strength;
        driverDataMap[key].constructor = constructorName;
        driverDataMap[key].name = name;
        driverDataMap[key].fullName = meta.full_name || name;

        const li = createPredictionItem(
            key, currentPos, imageUrl, name, strength,
            false, constructorName, 'driver-metric',
            true, false, changeType, season
        );
        list.appendChild(li);
    });
    window.driverDataMap = driverDataMap;
}

function createMetricBadge(metricValue) {
  const ns = "http://www.w3.org/2000/svg";
  const wrapper = document.createElement('div');
  wrapper.className = 'metric-badge';

  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", "0 0 40 40");
  svg.classList.add("metric-circle");

  const radius = 17.6;

  // background ring
  const circleBg = document.createElementNS(ns, "circle");
  circleBg.setAttribute("cx", "20");
  circleBg.setAttribute("cy", "20");
  circleBg.setAttribute("r", radius);
  circleBg.setAttribute("stroke", "#2b2b2b");
  circleBg.setAttribute("stroke-width", "3.2");
  circleBg.setAttribute("fill", "none");
  circleBg.setAttribute("class", "circle-bg");

  // foreground ring
  const circleFg = document.createElementNS(ns, "circle");
  circleFg.setAttribute("cx", "20");
  circleFg.setAttribute("cy", "20");
  circleFg.setAttribute("r", radius);
  circleFg.setAttribute("stroke", getStrengthColor(metricValue));
  circleFg.setAttribute("stroke-width", "3.2");
  circleFg.setAttribute("fill", "none");
  circleFg.setAttribute("stroke-linecap", "round");
  circleFg.setAttribute("transform", "rotate(-90 20 20)");
  circleFg.setAttribute("class", "circle-fg");

  // percent value compute
  const percent = parseFloat(String(metricValue).replace('%', ''));
  const circumference = 2 * Math.PI * radius;
  const safePercent = (Number.isFinite(percent) ? percent : 0);
  circleFg.setAttribute("stroke-dasharray", circumference);
  circleFg.setAttribute("stroke-dashoffset", circumference * (1 - Math.min(Math.max(safePercent, 0), 100) / 100));

  svg.appendChild(circleBg);
  svg.appendChild(circleFg);

  const number = document.createElement('div');
  number.className = 'metric-number';
  number.textContent = String(metricValue);

  wrapper.appendChild(svg);
  wrapper.appendChild(number);

  return wrapper;
}

/* ---------------------------
   Modal builder
   --------------------------- */
(function () {
  const modal = document.getElementById('driverModal');
  const inner = modal.querySelector('.modal-inner');

  function el(tag, props = {}, children = []) {
    const node = document.createElement(tag);
    Object.entries(props).forEach(([k, v]) => {
      if (k === 'class') node.className = v;
      else if (k === 'style') Object.assign(node.style, v);
      else if (k === 'html') node.innerHTML = v;
      else if (k === 'title') node.title = v;
      else node.setAttribute(k, v);
    });
    (Array.isArray(children) ? children : [children]).forEach(child => {
      if (!child && child !== 0) return;
      if (typeof child === 'string' || typeof child === 'number') node.appendChild(document.createTextNode(child));
      else node.appendChild(child);
    });
    return node;
  }

  function getStatIconImg(type) {
        const basePath = '/static/images/icons/';
        const iconMap = {
            raced: 'raced.png',
            wins: 'wins.png',
            points: 'points.png',
            pos: 'position.png',
            dry: 'dry.png',
            rain: 'rain.png',
            qual: 'qualifying.png',
            dnf: 'dnf.png',
        };
        const fileName = iconMap[type] || 'raced.png';
        
        const img = document.createElement('img');
        img.src = `${basePath}${fileName}`;
        img.alt = type;
        img.width = 18;
        img.height = 18;
        img.className = 'stat-icon';
        return img;
    }

  function getFlagPathForName(name) {
    const safe = String(name || '').replace(/\s+/g, '_').replace(/[^A-Za-z0-9_\-]/g, '');
    return `/static/images/flags/Flag_of_${safe}.png`;
  }

  function resolveConstructorColor(data) {
    if (data && data.constructorColor) return data.constructorColor;
    if (data && data.constructor && typeof window.getConstructorInfo === 'function') {
      try {
        const info = getConstructorInfo(data.constructor);
        if (info && info.color) return info.color;
      } catch (e) {}
    }
    return '#2f4be6';
  }

  function buildModalForDriver(key, type='driver') {
    const data = (window.driverDataMap && window.driverDataMap[key]) ? window.driverDataMap[key] : {};
    console.debug('openDriverModal - key:', key, 'data:', data);

    const name = (data && (data.fullName || data.full_name || data.displayName || data.display_name || data.name))
      || (typeof capitalize === 'function' ? capitalize(key) : key) || 'Unknown';

    const photoSrc = (data && (data.imageUrl || data.image || data.photo)) || `/static/images/drivers/${key}.png`;
    const ctorColor = resolveConstructorColor(data);

    const career = data?.career ?? data?.careerValue ?? 77;
    const overall = data?.overall ?? data?.overallValue ?? 82;
    const track = data?.track ?? data?.trackValue ?? 94;

    const stats = type === 'driver'
      ? (data?.stats || [
          { type: 'raced', label: 'Track races', value: '6', color: '#7ea6ff' },
          { type: 'wins', label: 'Track wins', value: '3x', color: '#ffd36e' },
          { type: 'points', label: 'Track points', value: '23', color: '#9fb4ff' },
          { type: 'pos', label: 'Track overtakes', value: '82', color: '#7ee6a8' },
          { type: 'dry', label: 'Dry race rating', value: '95%', color: '#9bd78b' },
          { type: 'rain', label: 'Wet race rating', value: '82%', color: '#6ec1ff' },
          { type: 'qual', label: 'Quali strength', value: '88', color: '#c7b3ff' },
          { type: 'dnf', label: 'DNF rate', value: '13%', color: '#ff7b7b' }
        ])
      : (data?.stats || [
          { type: 'raced', label: 'Constructor det', value: '6', color: '#7ea6ff' },
          { type: 'wins', label: 'Track wins', value: '3x', color: '#ffd36e' },
          { type: 'points', label: 'Track points', value: '23', color: '#9fb4ff' },
          { type: 'pos', label: 'Track overtakes', value: '82', color: '#7ee6a8' },
          { type: 'dry', label: 'Dry race rating', value: '95%', color: '#9bd78b' },
          { type: 'rain', label: 'Wet race rating', value: '82%', color: '#6ec1ff' },
          { type: 'qual', label: 'Quali strength', value: '88', color: '#c7b3ff' },
          { type: 'dnf', label: 'DNF rate', value: '13%', color: '#ff7b7b' }
        ]);

    const bestTracks = data?.bestTracks || [{ rank: 1, name: 'Bahrain' }, { rank: 2, name: 'Italy' }, { rank: 3, name: 'Qatar' }, { rank: 4, name: 'Belgium' }];
    const worstTracks = data?.worstTracks || [{ rank: 21, name: 'Brazil' }, { rank: 22, name: 'Hungary' }, { rank: 23, name: 'Spain' }, { rank: 24, name: 'China' }];

    inner.innerHTML = '';

    // close button
    const closeBtn = el('button', { class: 'modal-close', type: 'button', title: 'Close' }, ['\u00D7']);
    inner.appendChild(closeBtn);

    // left stats column
    const left = el('div', { class: 'modal-left' });
    stats.forEach(s => {
      const row = el('div', { class: 'stat-row' });
      row.appendChild(el('div', { class: 'stat-icon' }, [getStatIconImg(s.type)]));
      row.appendChild(el('div', { class: 'stat-text' }, [s.label]));
      row.appendChild(el('div', { class: 'stat-value' }, [s.value]));
      left.appendChild(row);
    });

    const main = el('div', { class: 'modal-main' });

    // photo circle
    const photoWrap = el('div', { class: 'photo-wrap' });
    const photoCircle = el('div', { class: 'photo-circle', style: { background: ctorColor } });
    const img = el('img', { src: photoSrc, alt: name });
    img.onerror = function () { this.onerror = null; this.src = '/static/images/drivers/driver-placeholder.png'; };
    photoCircle.appendChild(img);
    photoWrap.appendChild(photoCircle);
    main.appendChild(photoWrap);

    // name
    main.appendChild(el('div', { class: 'driver-name' }, [name]));

    // badges
    const badges = el('div', { class: 'badges' });
    [[career, 'Career'], [overall, 'Overall'], [track, 'Track']].forEach(([val, label]) => {
      const badge = el('div', { class: 'badge' });
      badge.appendChild(createMetricBadge(val));
      badge.appendChild(el('div', { class: 'badge-label' }, [label]));
      badges.appendChild(badge);
    });
    main.appendChild(badges);

    // track lists
    const trackLists = el('div', { class: 'track-lists' });
    function makeTrackCol(heading, arr) {
      const col = el('div', { class: 'track-col' });
      col.appendChild(el('div', { class: 'heading' }, [heading]));
      arr.forEach(item => {
        const it = (typeof item === 'string') ? { rank: '', name: item } : item;
        const row = el('div', { class: 'track-item' });
        row.appendChild(el('div', { class: 'track-rank' }, [String(it.rank)]));
        const flagImg = el('img', { class: 'flag', src: getFlagPathForName(it.name), alt: `${it.name} flag` });
        flagImg.onerror = function () { this.style.display = 'none'; };
        row.appendChild(flagImg);
        row.appendChild(el('div', { class: 'track-name' }, [it.name]));
        col.appendChild(row);
      });
      return col;
    }
    trackLists.appendChild(makeTrackCol('Best tracks', bestTracks));
    trackLists.appendChild(makeTrackCol('Worst tracks', worstTracks));
    main.appendChild(trackLists);

    inner.appendChild(left);
    inner.appendChild(main);

    closeBtn.addEventListener('click', closeModal);
  }

  function openDriverModal(driverKey, type='driver') {
    if (!driverKey) return;
    buildModalForDriver(driverKey, type);
    modal.style.display = 'flex';
    modal.setAttribute('aria-hidden', 'false');
    setTimeout(() => modal.addEventListener('click', onOutsideClick), 0);
  }

  function closeModal() {
    modal.style.display = 'none';
    modal.setAttribute('aria-hidden', 'true');
    modal.removeEventListener('click', onOutsideClick);
  }

  function onOutsideClick(e) {
    if (e.target === modal) closeModal();
  }

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && modal.style.display === 'flex') closeModal();
  });

  window.openDriverModal = window.openDriverModal || openDriverModal;
  window.closeDriverModal = window.closeDriverModal || closeModal;
})();

function populateConstructorStrength(constructors, prevConstructors, roundNum, season) {
    const list = document.querySelector('.constructor-list');
    if (!list) return;

    if (!Array.isArray(constructors)) {
        console.error("populateConstructorStrength expects an array.");
        list.innerHTML = '';
        return;
    }

    list.innerHTML = '';
    hideSpinnerForList('.constructor-list');

    const sorted = constructors.slice().sort((a, b) => {
        const va = (a && typeof a.predicted_strength === 'number') ? a.predicted_strength : -Infinity;
        const vb = (b && typeof b.predicted_strength === 'number') ? b.predicted_strength : -Infinity;
        return vb - va;
    });

    const prevExists = Array.isArray(prevConstructors);
    const prevMap = {};
    if (prevExists) {
        const prevSorted = prevConstructors.slice().sort((a, b) => {
            const va = (a && typeof a.predicted_strength === 'number') ? a.predicted_strength : -Infinity;
            const vb = (b && typeof b.predicted_strength === 'number') ? b.predicted_strength : -Infinity;
            return vb - va;
        });
        prevSorted.forEach((c, idx) => {
            const raw = c.TEAM || c.constructor || c.team || '';
            const n = raw || 'Unknown';
            prevMap[n.toLowerCase()] = idx + 1;
        });
    }

    sorted.forEach((constructor, index) => {
        const rawName = constructor.TEAM || constructor.constructor || constructor.team || 'Unknown';
        const name = capitalize(rawName);
        const key = rawName.toLowerCase().replace(/[^a-z0-9]/g, '');

        let strength = 'N/A';
        if (typeof constructor.predicted_strength === 'number') {
            strength = (constructor.predicted_strength * 100).toFixed(0);
        }

        const currentPos = index + 1;
        const prevPos = prevMap[name.toLowerCase()] !== undefined ? prevMap[name.toLowerCase()] : null;
        const changeType = computeChangeType(currentPos, prevPos, prevExists, roundNum);

        driverDataMap[key] = driverDataMap[key] || {};
        driverDataMap[key].strength = strength;
        driverDataMap[key].name = name;
        driverDataMap[key].constructor = name;

        const li = createPredictionItem(
            key, currentPos, null, name, strength,
            true, name, 'constructor-metric',
            true, false, changeType, season
        );
        list.appendChild(li);
    });
}

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
})();