// frontend/js/ventas.js

document.addEventListener("DOMContentLoaded", () => {
    const ventasTbody = document.querySelector("#tablaVentas tbody");
    const form = document.getElementById("ventaForm"); // capturamos el formulario

    // Mostrar mensajes al usuario
    function showMessage(text, isError = false) {
        const msg = document.getElementById("message");
        msg.textContent = text;
        msg.style.color = isError ? "red" : "green";
    }

    // ✅ Evento para registrar nueva venta
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        showMessage("");

        const product_id = document.getElementById("product_id").value.trim();
        const quantity = parseInt(document.getElementById("quantity").value);
        const price = parseFloat(document.getElementById("price").value);

        if (!product_id || isNaN(quantity) || isNaN(price)) {
            showMessage("Datos inválidos", true);
            return;
        }

        const venta = { product_id, quantity, price };

        try {
            const res = await fetch("/api/sales/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(venta)
            });

            if (res.ok) {
                showMessage("Venta registrada con éxito.");
                form.reset(); // limpia el formulario
                await cargarVentas(); // recarga la tabla
            } else {
                const error = await res.json();
                showMessage("Error al registrar: " + error.detail, true);
            }
        } catch (err) {
            showMessage("Error de red: " + err.message, true);
        }
    });

    // Cargar y mostrar las ventas desde la API
    async function cargarVentas() {
        try {
            const res = await fetch("/api/sales/");
            const data = await res.json();

            ventasTbody.innerHTML = "";

            data.forEach(venta => {
                const fila = document.createElement("tr");

                fila.innerHTML = `
                    <td>${venta.product_id}</td>
                    <td>${venta.quantity}</td>
                    <td>${venta.price.toFixed(2)}</td>
                    <td>
                        <button class="editarBtn" data-id="${venta._id}">Editar</button>
                        <button class="eliminarBtn" data-id="${venta._id}">Eliminar</button>
                    </td>
                `;

                ventasTbody.appendChild(fila);
            });
        } catch (err) {
            showMessage("Error al cargar ventas: " + err.message, true);
        }
    }

    // Eliminar venta
    ventasTbody.addEventListener("click", async (e) => {
        if (e.target.classList.contains("eliminarBtn")) {
            const id = e.target.dataset.id;

            const confirm = await Swal.fire({
                title: "¿Eliminar esta venta?",
                text: "No podrás deshacer esta acción",
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: "Sí, eliminar",
                cancelButtonText: "Cancelar"
            });

            if (confirm.isConfirmed) {
                try {
                    const res = await fetch(`/api/sales/${id}`, { method: "DELETE" });

                    if (res.ok) {
                        showMessage("Venta eliminada correctamente.");
                        cargarVentas();
                    } else {
                        showMessage("Error al eliminar venta", true);
                    }
                } catch (err) {
                    showMessage("Error de red: " + err.message, true);
                }
            }
        }
    });

    // Editar venta
    ventasTbody.addEventListener("click", async (e) => {
        if (e.target.classList.contains("editarBtn")) {
            const id = e.target.dataset.id;

            const fila = e.target.closest("tr");
            const product_id = fila.children[0].textContent;
            const quantity = fila.children[1].textContent;
            const price = fila.children[2].textContent;

            const { value: formValues } = await Swal.fire({
                title: "Editar Venta",
                html: `
                    <input id="edit_product_id" class="swal2-input" value="${product_id}" placeholder="ID producto">
                    <input id="edit_quantity" class="swal2-input" type="number" value="${quantity}" placeholder="Cantidad">
                    <input id="edit_price" class="swal2-input" type="number" step="0.01" value="${price}" placeholder="Precio">
                `,
                focusConfirm: false,
                showCancelButton: true,
                confirmButtonText: "Guardar cambios",
                preConfirm: () => {
                    return {
                        product_id: document.getElementById("edit_product_id").value.trim(),
                        quantity: parseInt(document.getElementById("edit_quantity").value),
                        price: parseFloat(document.getElementById("edit_price").value)
                    };
                }
            });

            if (formValues) {
                try {
                    const res = await fetch(`/api/sales/${id}`, {
                        method: "PUT",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify(formValues)
                    });

                    if (res.ok) {
                        showMessage("Venta actualizada con éxito.");
                        cargarVentas();
                    } else {
                        const error = await res.json();
                        showMessage("Error al actualizar: " + error.detail, true);
                    }
                } catch (err) {
                    showMessage("Error de red: " + err.message, true);
                }
            }
        }
    });

    // Búsqueda avanzada
    function filtrarVentasAvanzado() {
        const filtroProducto = document.getElementById("busquedaProductoVenta").value.toLowerCase();
        const filtroCantidad = document.getElementById("busquedaCantidadVenta").value;
        const filtroPrecio = document.getElementById("busquedaPrecioVenta").value;

        const filas = document.querySelectorAll("#tablaVentas tbody tr");

        filas.forEach(fila => {
            const idProducto = fila.children[0].textContent.toLowerCase();
            const cantidad = fila.children[1].textContent;
            const precio = fila.children[2].textContent;

            const coincideProducto = idProducto.includes(filtroProducto);
            const coincideCantidad = filtroCantidad === "" || cantidad === filtroCantidad;
            const coincidePrecio = filtroPrecio === "" || precio === filtroPrecio;

            fila.style.display = (coincideProducto && coincideCantidad && coincidePrecio) ? "" : "none";
        });
    }

    // Eventos para los filtros de búsqueda
    document.getElementById("busquedaProductoVenta")?.addEventListener("input", filtrarVentasAvanzado);
    document.getElementById("busquedaCantidadVenta")?.addEventListener("input", filtrarVentasAvanzado);
    document.getElementById("busquedaPrecioVenta")?.addEventListener("input", filtrarVentasAvanzado);

    // Cargar ventas al iniciar
    cargarVentas();
});
