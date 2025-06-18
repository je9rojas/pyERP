// 📁 frontend/static/js/ventas.js
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("ventaForm");
  const tablaVentas = document.getElementById("tablaVentas")?.querySelector("tbody");
  const messageDiv = document.getElementById("message");
  
  // Verificar que los elementos existan
  if (!form || !tablaVentas || !messageDiv) {
    console.error("Elementos esenciales no encontrados en el DOM");
    return;
  }

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

    // Validaciones básicas
    if (!data.product_id || isNaN(data.quantity) || isNaN(data.price)) {
      Swal.fire("❌ Error", "Datos inválidos", "error");
      return;
    }

    try {
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
        const errorMsg = result.detail || "Error desconocido";
        Swal.fire("❌ Error", errorMsg, "error");
      }
    } catch (error) {
      console.error("Error al registrar venta:", error);
      Swal.fire("❌ Error", "Error de conexión", "error");
    }
  });

  // 🔍 Búsquedas
  const inputsBusqueda = [
    inputBusquedaID,
    inputBusquedaCantidad,
    inputBusquedaPrecio
  ].filter(input => input); // Filtrar inputs válidos

  inputsBusqueda.forEach(input => {
    input.addEventListener("input", fetchVentas);
  });

  // 📦 Obtener ventas
  async function fetchVentas() {
    try {
      const query = inputBusquedaID?.value.trim() || "";
      const url = query ? `/api/sales/search?query=${encodeURIComponent(query)}` : "/api/sales/list";

      const res = await fetch(url);
      if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
      
      const ventas = await res.json();
      if (!Array.isArray(ventas)) throw new Error("Formato de respuesta inválido");

      renderVentas(ventas);
    } catch (err) {
      console.error("Error al cargar ventas:", err);
      if (messageDiv) {
        messageDiv.textContent = "❌ Error al cargar ventas";
      }
    }
  }

  // 🧱 Mostrar todas las ventas
  function renderVentas(ventas) {
    if (!tablaVentas) return;
    
    tablaVentas.innerHTML = "";
    
    const filtrarCantidad = inputBusquedaCantidad?.value.trim();
    const filtrarPrecio = inputBusquedaPrecio?.value.trim();

    ventas.forEach(venta => {
      // Filtrado adicional en cliente
      if (filtrarCantidad && venta.quantity !== parseInt(filtrarCantidad)) {
        return;
      }
      
      if (filtrarPrecio && venta.price !== parseFloat(filtrarPrecio)) {
        return;
      }

      renderVenta(venta);
    });
  }

  // 🧱 Mostrar fila individual
  function renderVenta(venta) {
    const tr = document.createElement("tr");

    // Manejar valores nulos o indefinidos
    const productCode = venta.product_code || "N/A";
    const productName = venta.name || "N/A";
    const quantity = venta.quantity ?? 0;
    const price = venta.price?.toFixed(2) ?? "0.00";

    tr.innerHTML = `
      <td>${productCode}</td>
      <td>${productName}</td>
      <td>${quantity}</td>
      <td>${price}</td>
      <td>
        <button class="btn-editar" data-id="${venta.id}" 
                data-quantity="${quantity}" 
                data-price="${venta.price}" 
                data-product="${venta.product_id}">✏️</button>
        <button class="btn-eliminar" data-id="${venta.id}">🗑️</button>
      </td>
    `;
    
    tablaVentas.appendChild(tr);
  }

  // 🎯 Event delegation para botones de editar/eliminar
  tablaVentas.addEventListener("click", (e) => {
    if (e.target.classList.contains("btn-editar")) {
      const id = e.target.dataset.id;
      const quantity = parseFloat(e.target.dataset.quantity);
      const price = parseFloat(e.target.dataset.price);
      const productId = e.target.dataset.product;
      editarVenta(id, quantity, price, productId);
    }
    
    if (e.target.classList.contains("btn-eliminar")) {
      const id = e.target.dataset.id;
      eliminarVenta(id);
    }
  });

  // ✏️ Editar venta
  async function editarVenta(id, cantidadActual, precioActual, productoID) {
    try {
      const { value: valores } = await Swal.fire({
        title: "✏️ Editar Venta",
        html: `
          <input id="swal-cantidad" class="swal2-input" type="number" min="1" value="${cantidadActual}">
          <input id="swal-precio" class="swal2-input" type="number" min="0" step="0.01" value="${precioActual}">
        `,
        focusConfirm: false,
        preConfirm: () => {
          const cantidad = parseInt(document.getElementById("swal-cantidad").value);
          const precio = parseFloat(document.getElementById("swal-precio").value);
          
          if (isNaN(cantidad)) {
            Swal.showValidationMessage("Cantidad inválida");
            return false;
          }
          
          if (isNaN(precio)) {
            Swal.showValidationMessage("Precio inválido");
            return false;
          }
          
          return [cantidad, precio];
        }
      });

      if (!valores) return;

      const [nuevaCantidad, nuevoPrecio] = valores;

      const res = await fetch(`/api/sales/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          product_id: productoID, 
          quantity: nuevaCantidad, 
          price: nuevoPrecio 
        })
      });

      const result = await res.json();
      if (res.ok) {
        Swal.fire("✅ Actualizado", result.message, "success");
        fetchVentas();
      } else {
        const errorMsg = result.detail || "Error al actualizar";
        Swal.fire("❌ Error", errorMsg, "error");
      }
    } catch (error) {
      console.error("Error al editar venta:", error);
      Swal.fire("❌ Error", "Error al editar venta", "error");
    }
  }

  // 🗑️ Eliminar venta
  async function eliminarVenta(id) {
    try {
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
        const errorMsg = result.detail || "Error al eliminar";
        Swal.fire("❌ Error", errorMsg, "error");
      }
    } catch (error) {
      console.error("Error al eliminar venta:", error);
      Swal.fire("❌ Error", "Error al eliminar venta", "error");
    }
  }
});