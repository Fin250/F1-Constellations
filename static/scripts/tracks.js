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
            populateGPResults(data.gp_results);
            populateDriverStrength(data.driver_strength);
            populateConstructorStrength(data.constructor_strength);
        })
        .catch(error => console.error('Error fetching predictions:', error));
});

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function populateGPResults(predictions) {
    const list = document.querySelector('.gp-results');
    if (!list) return;

    list.innerHTML = '';
    predictions.forEach(driver => {
        const li = document.createElement('li');
        const name = capitalize(driver.driver);
        li.textContent = `${name} - Win probability: ${driver.probability}%`;
        list.appendChild(li);
    });
}

function populateDriverStrength(drivers) {
    const list = document.querySelector('.driver-list');
    if (!list) return;

    list.innerHTML = '';
    drivers.forEach(driver => {
        const li = document.createElement('li');
        li.textContent = `${driver.driver} - Strength: ${driver.strength}`;
        list.appendChild(li);
    });
}

function populateConstructorStrength(constructors) {
    const list = document.querySelector('.constructor-list');
    if (!list) return;

    list.innerHTML = '';
    constructors.forEach(constructor => {
        const li = document.createElement('li');
        li.textContent = `${constructor.constructor} - Strength: ${constructor.strength}`;
        list.appendChild(li);
    });
}