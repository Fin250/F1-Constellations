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

function normalizeConstructorName(rawName) {
    if (!rawName) return 'Unknown';
    const key = rawName.toLowerCase().trim();
    return constructorNameMap[key] || rawName;
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

document.addEventListener("DOMContentLoaded", async function () {
    const roundAttr = document.body.getAttribute('data-round');
    if (!roundAttr) {
        console.error("Missing 'data-round' on body.");
        return;
    }

    const round = parseInt(roundAttr, 10);
    if (isNaN(round)) {
        console.error("Invalid round number in 'data-round'.");
        return;
    }

    // fetch current round data
    let currentData;
    try {
        const resp = await fetch(`/ml/${round}`);
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
            const respPrev = await fetch(`/ml/${round - 1}`);
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
        populateGPResults(currentData.gp_results.predictions, metadata, prevGpPreds, round);
    }

    if (!Array.isArray(currentData.driver_strength)) {
        console.error("Invalid or missing driver_strength array");
    } else {
        const prevDrivers = prevData && Array.isArray(prevData.driver_strength) ? prevData.driver_strength : null;
        populateDriverStrength(currentData.driver_strength, metadata, prevDrivers, round);
    }

    if (!Array.isArray(currentData.constructor_strength)) {
        console.error("Invalid or missing constructor_strength array");
    } else {
        const prevConstructors = prevData && Array.isArray(prevData.constructor_strength) ? prevData.constructor_strength : null;
        populateConstructorStrength(currentData.constructor_strength, prevConstructors, round);
    }
});

/* ---------- Helpers ---------- */

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
function createPredictionItem(position, imageUrl, name, metricValue, isConstructor = false, constructorName = null, metricClass = 'metric', showMetric = true, isProbability = false, changeType = 'neutral') {
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
    if (constructorName && constructorColors[constructorName]) {
        imgWrapper.style.backgroundColor = constructorColors[constructorName];
    }

    const img = document.createElement('img');
    img.src = imageUrl;
    img.alt = name;
    const isPlaceholder = (imageUrl || '').includes('driver-placeholder') || (imageUrl || '').includes('constructor-placeholder');
    img.className = (!isConstructor && !isPlaceholder) ? 'driver-img' : 'static-img';
    img.onerror = function () {
        this.onerror = null;
        this.src = isConstructor
            ? '/static/images/constructors/constructor-placeholder.jpg'
            : '/static/images/drivers/driver-placeholder.png';
        this.className = 'static-img';
    };

    imgWrapper.appendChild(img);
    infoDiv.appendChild(imgWrapper);

    const nameSpan = document.createElement('span');
    nameSpan.textContent = name;
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
            svg.setAttribute("width", "40");
            svg.setAttribute("height", "40");

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
            metricSpan.style.color = '#cac2c2ff';
        }
    }

    li.appendChild(posWrapper);
    li.appendChild(infoDiv);
    if (showMetric) li.appendChild(metricWrapper);

    return li;
}

/* ---------- Population functions with change detection ---------- */

function populateGPResults(predictions, metadata, prevPredictions, roundNum) {
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
        const imageUrl = meta.image || `/static/images/drivers/driver-placeholder.png`;
        const constructorName = normalizeConstructorName(meta.constructor) || null;

        const probabilityValue = (typeof driver.probability === 'number') ? driver.probability.toFixed(1) : String(driver.probability);
        const probability = `${probabilityValue}%`;

        const currentPos = index + 1;
        const prevPos = prevMap[key] !== undefined ? prevMap[key] : null;
        const changeType = computeChangeType(currentPos, prevPos, prevExists, roundNum);

        const li = createPredictionItem(currentPos, imageUrl, name, probability, false, constructorName, 'gp-metric', true, true, changeType);
        list.appendChild(li);
    });
}

function populateDriverStrength(drivers, metadata, prevDrivers, roundNum) {
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
        const imageUrl = meta.image || `/static/images/drivers/driver-placeholder.png`;
        const constructorName = normalizeConstructorName(meta.constructor) || null;

        let ratingVal = null;
        if (d.rating !== undefined && d.rating !== null) {
            ratingVal = Number(d.rating);
        } else if (d.strength !== undefined && d.strength !== null) {
            ratingVal = Number(d.strength);
        }

        const strength = (ratingVal !== null && !Number.isNaN(ratingVal)) ? safeMetric(ratingVal, 0) : 'N/A';

        const currentPos = index + 1;
        const prevPos = prevMap[key] !== undefined ? prevMap[key] : null;
        const changeType = computeChangeType(currentPos, prevPos, prevExists, roundNum);

        const li = createPredictionItem(currentPos, imageUrl, name, strength, false, constructorName, 'driver-metric', true, false, changeType);
        list.appendChild(li);
    });
}

function populateConstructorStrength(constructors, prevConstructors, roundNum) {
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
            const n = normalizeConstructorName(raw);
            prevMap[n.toLowerCase()] = idx + 1;
        });
    }

    sorted.forEach((constructor, index) => {
        const rawName = constructor.TEAM || constructor.constructor || constructor.team || 'Unknown';
        const name = normalizeConstructorName(rawName);
        const imageUrl = constructorLogos[name] || `/static/images/constructors/constructor-placeholder.jpg`;

        let strength = 'N/A';
        if (typeof constructor.predicted_strength === 'number') {
            strength = (constructor.predicted_strength * 100).toFixed(0);
        }

        const currentPos = index + 1;
        const prevPos = prevMap[name.toLowerCase()] !== undefined ? prevMap[name.toLowerCase()] : null;
        const changeType = computeChangeType(currentPos, prevPos, prevExists, roundNum);

        const li = createPredictionItem(currentPos, imageUrl, name, strength, true, name, 'constructor-metric', true, false, changeType);
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