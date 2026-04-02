document.addEventListener('DOMContentLoaded', function () {
    document.body.addEventListener('click', function (e) {
        const navLink = e.target.closest('.pagination a');
        if (!navLink) return;

        e.preventDefault();
        const url = navLink.href;

        const listRecipe = document.querySelector('#list-recipe');
        const paginationBox = document.querySelector('.pagination');
        if (listRecipe) listRecipe.style.opacity = '0.5';

        fetch(url)
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.text();
            })
            .then(data => {
                const parser = new DOMParser();
                const newDoc = parser.parseFromString(data, 'text/html');

                const newContent = newDoc.querySelector('#list-recipe');
                if (newContent && listRecipe) {
                    listRecipe.innerHTML = newContent.innerHTML;
                    listRecipe.style.opacity = '1';
                }

                const newPagination = newDoc.querySelector('.pagination');
                if (newPagination && paginationBox) {
                    paginationBox.innerHTML = newPagination.innerHTML;
                }

                window.history.pushState({ path: url }, '', url);
            })
            .catch(err => {
                console.error('Lỗi AJAX:', err);
                window.location.href = url;
            });
    });
});