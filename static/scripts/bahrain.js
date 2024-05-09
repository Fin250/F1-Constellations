document.addEventListener("DOMContentLoaded", function() {
    fetch('/ml/bahrain')
        .then(response => response.json())
        .then(data => {
            const topDriversList = document.querySelector('.top-drivers');
            topDriversList.innerHTML = '';
            data.forEach(driver => {
                const listItem = document.createElement('li');
                listItem.textContent = driver;
                topDriversList.appendChild(listItem);
            });
        })
        .catch(error => console.error('Error fetching top drivers:', error));
});
