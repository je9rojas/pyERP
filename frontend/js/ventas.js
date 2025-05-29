// frontend/js/ventas.js

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("productForm");

    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();

            const product = {
                name: document.getElementById("name").value,
                description: document.getElementById("description").value,
                stock: parseInt(document.getElementById("stock").value),
                price: parseFloat(document.getElementById("price").value)
            };

            try {
                const response = await fetch("http://localhost:8000/api/products/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(product)
                });

                if (response.ok) {
                    alert("Producto guardado con éxito.");
                    form.reset();
                } else {
                    const error = await response.json();
                    alert("Error al guardar: " + JSON.stringify(error));
                }
            } catch (err) {
                alert("Error de red: " + err.message);
            }
        });
    }
});
