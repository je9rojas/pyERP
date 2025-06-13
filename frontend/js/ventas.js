// 📁 frontend/js/ventas.js
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("ventaForm");
  const tablaVentas = document.getElementById("tablaVentas").querySelector("tbody");
  const messageDiv = document.getElementById("message");

  const inputBusquedaID = document.getElementById("busquedaProductoVenta");
  const inputBusquedaCantidad = document.getElementById("busquedaCantidadVenta");
  const inputBusquedaPrecio = document.getElementById("busquedaPrecioVenta");

  // 🔄 Inicializar
  fetchVentas();

  // 📌 Registrar venta
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const data = {
      product_id: document.getElementById("product_id").value.trim(),
      quantity: parseInt(document.getElementById("quantity").value),
      price: parseFloat(document.getElementById("price").value)
    };

    const res = await fetch("/api/sales/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });

    const result = await res.json();
    if (res.ok) {
      Swal.fire("✅ Éxito", result.message, "success");
      form.reset();
      fetchVentas();
    } else {
      Swal.fire("❌ Error", result.detail, "error");
    }
  });

  // 🔍 Búsquedas
  [inputBusquedaID, inputBusquedaCantidad, inputBusquedaPrecio].forEach(input => {
    input.addEventListener("input", fetchVentas);
  });

  // 📦 Obtener ventas
  async function fetchVentas() {
    let query = inputBusquedaID.value.trim();
    let url = query ? `/api/sales/search/?query=${query}` : "/api/sales/list";

    try {
      const res = await fetch(url);
      const ventas = await res.json();
      if (!Array.isArray(ventas)) throw new Error("Formato inesperado");

      tablaVentas.innerHTML = "";
      ventas.forEach(venta => {
        // Filtrado adicional en cliente
        const filtrarCantidad = inputBusquedaCantidad.value.trim();
        const filtrarPrecio = inputBusquedaPrecio.value.trim();

        if (
          (filtrarCantidad && venta.quantity != parseInt(filtrarCantidad)) ||
          (filtrarPrecio && venta.price != parseFloat(filtrarPrecio))
        ) {
          return;
        }

        renderVenta(venta);
      });

    } catch (err) {
      console.error("Error al cargar ventas:", err);
      messageDiv.textContent = "❌ Error al cargar ventas";
    }
  }

  // 🧱 Mostrar fila
  function renderVenta(venta) {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td>${venta.product_code}</td>
      <td>${venta.name}</td>
      <td>${venta.quantity}</td>
      <td>${venta.price.toFixed(2)}</td>
      <td>
        <button onclick="editarVenta('${venta.id}', ${venta.quantity}, ${venta.price}, '${venta.product_id}')">✏️</button>
        <button onclick="eliminarVenta('${venta.id}')">🗑️</button>
      </td>
    `;
    tablaVentas.appendChild(tr);
  }

  // Exponer funciones globales
  window.editarVenta = async function(id, cantidadActual, precioActual, productoID) {
    const { value: valores } = await Swal.fire({
      title: "✏️ Editar Venta",
      html: `
        <input id="swal-cantidad" class="swal2-input" type="number" min="1" value="${cantidadActual}">
        <input id="swal-precio" class="swal2-input" type="number" min="0" step="0.01" value="${precioActual}">
      `,
      preConfirm: () => [
        parseInt(document.getElementById("swal-cantidad").value),
        parseFloat(document.getElementById("swal-precio").value)
      ]
    });

    if (!valores) return;

    const [nuevaCantidad, nuevoPrecio] = valores;

    const res = await fetch(`/api/sales/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_id: productoID, quantity: nuevaCantidad, price: nuevoPrecio })
    });

    const result = await res.json();
    if (res.ok) {
      Swal.fire("✅ Actualizado", result.message, "success");
      fetchVentas();
    } else {
      Swal.fire("❌ Error", result.detail || "Error al actualizar", "error");
    }
  };

  window.eliminarVenta = async function(id) {
    const confirm = await Swal.fire({
      title: "¿Eliminar venta?",
      text: "Esta acción es irreversible",
      icon: "warning",
      showCancelButton: true,
      confirmButtonText: "Sí, eliminar",
      cancelButtonText: "Cancelar"
    });

    if (!confirm.isConfirmed) return;

    const res = await fetch(`/api/sales/${id}`, { method: "DELETE" });
    const result = await res.json();

    if (res.ok) {
      Swal.fire("✅ Eliminada", result.message, "success");
      fetchVentas();
    } else {
      Swal.fire("❌ Error", result.detail || "Error al eliminar", "error");
    }
  };
});
