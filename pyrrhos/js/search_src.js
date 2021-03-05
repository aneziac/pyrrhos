function search() {
    let input = document.getElementById('searchbar').value.toLowerCase();

    for (i = 0; i < data.length; i++) {
        var term = JSON.parse(data[i]);
        if (term.short.toLowerCase() == input || term.long.toLowerCase() == input) {
            window.location.href = term.link;
        }
    }
}
