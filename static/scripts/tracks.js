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
            if (!response.ok) {
                throw new Error(`Failed to fetch predictions: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const metadata = data.driver_metadata || {};
            populateGPResults(data.gp_results, metadata);
            populateDriverStrength(data.driver_strength, metadata);
            populateConstructorStrength(data.constructor_strength);
        })
        .catch(error => console.error('Error fetching predictions:', error));
});

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function ordinal(n) {
    const s = ["th", "st", "nd", "rd"],
        v = n % 100;
    return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

function createPredictionItem(position, imageUrl, name, metricValue, isConstructor = false) {
    const li = document.createElement('li');

    // Position
    const posSpan = document.createElement('span');
    posSpan.className = 'position';
    posSpan.textContent = ordinal(position);

    // Info
    const infoDiv = document.createElement('div');
    infoDiv.className = isConstructor ? 'constructor-info' : 'driver-info';

    // Image wrapper
    const imgWrapper = document.createElement('div');
    imgWrapper.className = 'image-zoom-wrapper';

    const img = document.createElement('img');
    img.src = imageUrl;
    img.alt = name;

    const isPlaceholder = imageUrl.includes('driver-placeholder') || imageUrl.includes('constructor-placeholder');

    // Apply zoom class only to non-placeholder driver images
    if (!isConstructor && !isPlaceholder) {
        img.className = 'zoomed-driver-img';
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

function populateGPResults(predictions, metadata) {
    const list = document.querySelector('.gp-results');
    if (!list) return;

    list.innerHTML = '';
    predictions.forEach((driver, index) => {
        const key = driver.driver.toLowerCase();
        const meta = metadata[key] || {};
        const name = meta.full_name || capitalize(key);
        const imageUrl = meta.image || `/static/images/drivers/driver-placeholder.png`;
        const probability = `${driver.probability}%`;

        const li = createPredictionItem(index + 1, imageUrl, name, probability);
        list.appendChild(li);
    });
}

function populateDriverStrength(drivers, metadata) {
    const list = document.querySelector('.driver-list');
    if (!list) return;

    list.innerHTML = '';
    drivers.forEach((driver, index) => {
        const key = driver.driver.toLowerCase();
        const meta = metadata[key] || {};
        const name = meta.full_name || capitalize(key);
        const imageUrl = meta.image || `/static/images/drivers/driver-placeholder.png`;
        const strength = `${driver.strength}`;

        const li = createPredictionItem(index + 1, imageUrl, name, strength);
        list.appendChild(li);
    });
}

function populateConstructorStrength(constructors) {
    const list = document.querySelector('.constructor-list');
    if (!list) return;

    list.innerHTML = '';
    constructors.forEach((constructor, index) => {
        const name = constructor.constructor;
        const imageUrl = `/static/images/constructors/constructor-placeholder.jpg`;
        const strength = `${constructor.strength}`;
        const li = createPredictionItem(index + 1, imageUrl, name, strength, true);
        list.appendChild(li);
    });
}
