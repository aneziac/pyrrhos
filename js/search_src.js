var searchBar = document.getElementById('searchbar');

searchBar.addEventListener("keyup", function(event) {
    if (event.keyCode === 13) {  // check if user has pressed enter
        search();
    }
});

function search() {
    let searchInput = document.getElementById('searchbar').value.toLowerCase();

    for (i = 0; i < data.length; i++) {
        var term = JSON.parse(data[i]);  // parse all vocabulary terms
        if (term.short.toLowerCase() == searchInput || term.long.toLowerCase() == searchInput) {
            window.location.href = term.link;
        }
    }
}
