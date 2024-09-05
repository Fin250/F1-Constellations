document.addEventListener("DOMContentLoaded", function() {
    fetch('/ml/3')
        .then(response => response.json())
        .then(data => {
            const topDriversList = document.querySelector('.top-drivers');
            topDriversList.innerHTML = '';
            const drivers = [
                { name: capitalizeFirstLetter(data[0]['1st_predicted']), chance: data[0]['1st_predicted_chance'] },
                { name: capitalizeFirstLetter(data[0]['2nd_predicted']), chance: data[0]['2nd_predicted_chance'] },
                { name: capitalizeFirstLetter(data[0]['3rd_predicted']), chance: data[0]['3rd_predicted_chance'] },
                { name: capitalizeFirstLetter(data[0]['4th_predicted']), chance: data[0]['4th_predicted_chance'] },
                { name: capitalizeFirstLetter(data[0]['5th_predicted']), chance: data[0]['5th_predicted_chance'] }
            ];
            drivers.forEach(driver => {
                const listItem = document.createElement('li');
                listItem.textContent = `${driver.name} - Win probability: ${driver.chance}`;
                topDriversList.appendChild(listItem);
            });
        })
        .catch(error => console.error('Error fetching top drivers:', error));
});

function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}
