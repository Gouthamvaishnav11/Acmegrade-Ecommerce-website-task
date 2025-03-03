const bar = document.getElementById('bar');
const close = document.getElementById('close');
const nav = document.getElementById('navbar');

if (bar) {
    bar.addEventListener('click',()=> {
        nav.classList.add('active');
    })
}

if (close){
    close.addEventListener('click',()=>{
        nav.classList.remove('active');
    })
}


document.addEventListener("DOMContentLoaded", function () {
    let page = 1;
    let loading = false;

    window.addEventListener("scroll", function () {
        if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 100 && !loading) {
            loading = true;
            loadMoreProducts();
        }
    });

    function loadMoreProducts() {
        fetch(`/load_more_products?page=${page}`)
            .then(response => response.json())
            .then(data => {
                if (data.products.length > 0) {
                    let table = document.querySelector("table");
                    data.products.forEach(product => {
                        let row = table.insertRow();
                        row.innerHTML = `
                            <td>${product.name}</td>
                            <td>${product.description}</td>
                            <td>$${product.price}</td>
                            <td><img src="${product.image}" width="80"></td>
                        `;
                    });
                    page++;
                    loading = false;
                }
            });
    }
});

