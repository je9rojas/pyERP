// 📁 frontend/js/compras.js

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("purchaseForm");
    const messageDiv = document.getElementById("message");
    const tablaCompras = document.getElementById("tablaCompras").querySelector("tbody");

    const campoProducto = document.getElementById("product_id");
    const campoCantidad = document.getElementById("quantity");
    const campoPrecio = document.getElementById("price");
    const campoIdOculto = document.getElementById("purchase_id");

    const campoBuscarProducto = document.getElementById("busquedaProductoCompra");
    const campoBuscarCantidad = document.getElementById("busquedaCantidadCompra");
    const campoBuscarPrecio = document.getElementById("busquedaPrecioCompra");

    function showMessage(text, isError = false) {
        messageDiv.textContent = text;
        messageDiv.style.color = isError ? "red" : "green";
    }

    // ✅ CORREGIDO: Usar endpoint correcto
    async function cargarCompras() {
        try {
            const res = await fetch("/api/purchases/list");
            const data = await res.json();
            renderizarCompras(data);
        } catch (error) {
            showMessage("Error al cargar compras", true);
        }
    }

    function renderizarCompras(compras) {
        tablaCompras.innerHTML = "";

        const productoFiltro = campoBuscarProducto.value.trim().toLowerCase();
        const cantidadFiltro = parseInt(campoBuscarCantidad.value);
        const precioFiltro = parseFloat(campoBuscarPrecio.value);

        compras.filter(c => {
            if (productoFiltro && !c.product_id.toLowerCase().includes(productoFiltro)) return false;
            if (!isNaN(cantidadFiltro) && c.quantity !== cantidadFiltro) return false;
            if (!isNaN(precioFiltro) && c.price !== precioFiltro) return false;
            return true;
        }).forEach(compra => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${compra.product_id}</td>
                <td>${compra.quantity}</td>
                <td>${compra.price}</td>
                <td>
                    <button class="editar" data-id="${compra.id}">✏️</button>
                    <button class="eliminar" data-id="${compra.id}">🗑️</button>
                </td>
            `;
            tablaCompras.appendChild(tr);
        });
    }

    if (form) {
        form.addEventListener("submit", async e => {
            e.preventDefault();
            showMessage("");

            const product_id = campoProducto.value.trim();
            const quantity = parseInt(campoCantidad.value);
            const price = parseFloat(campoPrecio.value);
            const id = campoIdOculto.value;

            if (!product_id || isNaN(quantity) || isNaN(price)) {
                showMessage("Datos inválidos.", true);
                return;
            }

            const compra = { product_id, quantity, price };
            try {
                const url = id ? `/api/purchases/${id}` : "/api/purchases/";
                const method = id ? "PUT" : "POST";

                const res = await fetch(url, {
                    method,
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(compra)
                });

                if (res.ok) {
                    showMessage(id ? "Compra actualizada" : "Compra registrada");
                    form.reset();
                    campoIdOculto.value = "";
                    await cargarCompras();
                } else {
                    const err = await res.json();
                    showMessage("Error: " + err.detail, true);
                }
            } catch (err) {
                showMessage("Error de red: " + err.message, true);
            }
        });
    }

    tablaCompras.addEventListener("click", async e => {
        const id = e.target.dataset.id;

        if (e.target.classList.contains("eliminar")) {
            const confirm = await Swal.fire({
                title: "¿Eliminar compra?",
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: "Sí, eliminar",
                cancelButtonText: "Cancelar"
            });

            if (confirm.isConfirmed) {
                const res = await fetch(`/api/purchases/${id}`, { method: "DELETE" });
                if (res.ok) {
                    showMessage("Compra eliminada");
                    await cargarCompras();
                } else {
                    showMessage("Error al eliminar", true);
                }
            }
        }

        if (e.target.classList.contains("editar")) {
            const res = await fetch("/api/purchases/list"); // ✅ usar lista completa
            const data = await res.json();
            const compra = data.find(p => p.id === id); // ✅ usar campo "id"
            if (compra) {
                campoProducto.value = compra.product_id;
                campoCantidad.value = compra.quantity;
                campoPrecio.value = compra.price;
                campoIdOculto.value = compra.id;
            }
        }
    });

    [campoBuscarProducto, campoBuscarCantidad, campoBuscarPrecio].forEach(input => {
        input.addEventListener("input", cargarCompras);
    });

    cargarCompras(); // ✅ llamada inicial
});
