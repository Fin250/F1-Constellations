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

function normalizeConstructorName(rawName) {
    if (!rawName) return 'Unknown';
    const key = rawName.toLowerCase().trim();
    return constructorNameMap[key] || rawName;
}

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

document.addEventListener("DOMContentLoaded", function () {
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

    fetch(`/ml/${round}`)
        .then(response => {
            if (!response.ok) throw new Error(`Failed to fetch predictions: ${response.status}`);
            return response.json();
        })
        .then(data => {
            console.log("Data received from backend:", data);

            const metadata = data.driver_metadata || {};

            if (!data.gp_results || !Array.isArray(data.gp_results.predictions)) {
                console.error("Invalid or missing gp_results.predictions");
            } else {
                populateGPResults(data.gp_results.predictions, metadata);
            }

            if (!Array.isArray(data.driver_strength)) {
                console.error("Invalid or missing driver_strength array");
            } else {
                populateDriverStrength(data.driver_strength, metadata);
            }

            if (!Array.isArray(data.constructor_strength)) {
                console.error("Invalid or missing constructor_strength array");
            } else {
                populateConstructorStrength(data.constructor_strength);
            }
        })
        .catch(error => console.error('Error fetching predictions:', error));
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

/* Creates the list item used by all lists */
function createPredictionItem(position, imageUrl, name, metricValue, isConstructor = false, constructorName = null) {
    const li = document.createElement('li');

    // position
    const posSpan = document.createElement('span');
    posSpan.className = 'position';
    posSpan.textContent = ordinal(position);

    // info container
    const infoDiv = document.createElement('div');
    infoDiv.className = isConstructor ? 'constructor-info' : 'driver-info';

    // image wrapper
    const imgWrapper = document.createElement('div');
    imgWrapper.className = 'image-wrapper';

    // Apply constructor background color
    if (constructorName && constructorColors[constructorName]) {
        imgWrapper.style.backgroundColor = constructorColors[constructorName];
    }

    const img = document.createElement('img');
    img.src = imageUrl;
    img.alt = name;

    const isPlaceholder = (imageUrl || '').includes('driver-placeholder') || (imageUrl || '').includes('constructor-placeholder');

    if (!isConstructor && !isPlaceholder) {
        img.className = 'driver-img';
    } else {
        img.className = 'static-img';
    }

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

    const metricSpan = document.createElement('span');
    metricSpan.className = 'metric';
    metricSpan.textContent = metricValue;

    li.appendChild(posSpan);
    li.appendChild(infoDiv);
    li.appendChild(metricSpan);

    return li;
}

/* ---------- Population functions ---------- */

function populateGPResults(predictions, metadata) {
    const list = document.querySelector('.gp-results');
    if (!list) {
        console.warn("No .gp-results element found in DOM.");
        return;
    }

    list.innerHTML = '';
    predictions.forEach((driver, index) => {
        const key = (driver.driver || '').toLowerCase();
        const meta = metadata[key] || {};
        const name = meta.full_name || capitalize(driver.driver) || 'Unknown';
        const imageUrl = meta.image || `/static/images/drivers/driver-placeholder.png`;
        const constructorName = normalizeConstructorName(meta.constructor) || null;

        const probabilityValue = (typeof driver.probability === 'number') ? driver.probability.toFixed(1) : String(driver.probability);
        const probability = `${probabilityValue}%`;

        const li = createPredictionItem(index + 1, imageUrl, name, probability, false, constructorName);
        list.appendChild(li);
    });
}

function populateDriverStrength(drivers, metadata) {
    const list = document.querySelector('.driver-list');
    if (!list) {
        console.warn("No .driver-list element found in DOM.");
        return;
    }

    list.innerHTML = '';
    drivers.forEach((driver, index) => {
        const key = (driver.driver || '').toLowerCase();
        const meta = metadata[key] || {};
        const name = meta.full_name || capitalize(driver.driver) || 'Unknown';
        const imageUrl = meta.image || `/static/images/drivers/driver-placeholder.png`;
        const constructorName = meta.constructor || null;

        const strength = safeMetric(driver.strength, 1);

        const li = createPredictionItem(index + 1, imageUrl, name, strength, false, constructorName);
        list.appendChild(li);
    });
}

function populateConstructorStrength(constructors) {
    const list = document.querySelector('.constructor-list');
    if (!list) {
        console.warn("No .constructor-list element found in DOM.");
        return;
    }

    if (!Array.isArray(constructors)) {
        console.error("populateConstructorStrength expects an array.");
        list.innerHTML = '';
        return;
    }

    list.innerHTML = '';

    constructors.sort((a, b) => {
        const va = (a && typeof a.predicted_strength === 'number') ? a.predicted_strength : -Infinity;
        const vb = (b && typeof b.predicted_strength === 'number') ? b.predicted_strength : -Infinity;
        return vb - va;
    });

    constructors.forEach((constructor, index) => {
        const rawName = constructor.TEAM || constructor.constructor || constructor.team || 'Unknown';
        const name = normalizeConstructorName(rawName);
        const imageUrl = constructorLogos[name] || `/static/images/constructors/constructor-placeholder.jpg`;

        let strength = 'N/A';
        if (typeof constructor.predicted_strength === 'number') {
            strength = (constructor.predicted_strength * 100).toFixed(1);
        }

        const li = createPredictionItem(index + 1, imageUrl, name, strength, true, name);
        list.appendChild(li);
    });
}
