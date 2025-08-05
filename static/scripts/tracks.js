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
            const topDriversList = document.querySelector('.top-drivers');
            if (!topDriversList) {
                console.warn("Element '.top-drivers' not found.");
                return;
            }

            topDriversList.innerHTML = '';
            data.forEach(driver => {
                const listItem = document.createElement('li');
                const name = capitalize(driver.driver);
                listItem.textContent = `${name} - Win probability: ${driver.probability}%`;
                topDriversList.appendChild(listItem);
            });
        })
        .catch(error => console.error('Error fetching driver predictions:', error));
});

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}