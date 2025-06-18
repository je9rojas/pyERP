// 📁 frontend/static/js/ventas.js
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("ventaForm");
  const tablaVentas = document.getElementById("tablaVentas")?.querySelector("tbody");
  const messageDiv = document.getElementById("message");
  const itemsContainer = document.getElementById("itemsContainer");
  const addItemBtn = document.getElementById("addItemBtn");
  const totalElement = document.getElementById("totalVenta");
  
  // Verificar que los elementos existan
  if (!form || !tablaVentas || !messageDiv || !itemsContainer || !addItemBtn || !totalElement) {
    console.error("Elementos esenciales no encontrados en el DOM");
    return;
  }

  let currentItems = [];
  let itemCounter = 0;

  // 🔄 Inicializar
  fetchVentas();

  // ➕ Agregar nuevo ítem al formulario
  addItemBtn.addEventListener("click", () => {
    addItemForm();
  });

  // Función para agregar un nuevo ítem
  function addItemForm(item = {}) {
    itemCounter++;
    const itemDiv = document.createElement("div");
    itemDiv.className = "item-form mb-3 p-3 border rounded";
    itemDiv.innerHTML = `
      <div class="row g-3">
        <div class="col-md-5">
          <label class="form-label">Producto</label>
          <input type="text" class="form-control product-code" 
                 placeholder="Código del producto" 
                 value="${item.product_id || ''}" required>
        </div>
        <div class="col-md-2">
          <label class="form-label">Cantidad</label>
          <input type="number" class="form-control quantity" 
                 min="1" value="${item.quantity || '1'}" required>
        </div>
        <div class="col-md-3">
          <label class="form-label">Precio Unitario</label>
          <input type="number" class="form-control price" 
                 step="0.01" min="0" value="${item.price || ''}" required>
        </div>
        <div class="col-md-2 d-flex align-items-end">
          <button type="button" class="btn btn-danger remove-item-btn">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      </div>
    `;
    
    itemsContainer.appendChild(itemDiv);
    
    // Configurar evento para eliminar ítem
    const removeBtn = itemDiv.querySelector(".remove-item-btn");
    removeBtn.addEventListener("click", () => {
      itemDiv.remove();
      updateTotal();
    });
    
    // Configurar autocompletado para producto
    const productInput = itemDiv.querySelector(".product-code");
    productInput.addEventListener("input", async (e) => {
      const code = e.target.value.trim();
      if (code.length > 2) {
        const product = await fetchProduct(code);
        if (product) {
          const priceInput = itemDiv.querySelector(".price");
          priceInput.value = product.price;
          updateTotal();
        }
      }
    });
    
    // Actualizar total cuando cambian cantidades o precios
    const quantityInput = itemDiv.querySelector(".quantity");
    const priceInput = itemDiv.querySelector(".price");
    
    [quantityInput, priceInput].forEach(input => {
      input.addEventListener("input", updateTotal);
    });
  }

  // 📌 Registrar venta
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const client = document.getElementById("client").value.trim();
    if (!client) {
      Swal.fire("❌ Error", "Debe ingresar un cliente", "error");
      return;
    }

    // Recolectar ítems
    const items = [];
    const itemForms = document.querySelectorAll(".item-form");
    
    for (const itemForm of itemForms) {
      const productCode = itemForm.querySelector(".product-code").value.trim();
      const quantity = parseInt(itemForm.querySelector(".quantity").value);
      const price = parseFloat(itemForm.querySelector(".price").value);
      
      if (!productCode || isNaN(quantity) || isNaN(price)) {
        Swal.fire("❌ Error", "Datos incompletos en los ítems", "error");
        return;
      }
      
      items.push({
        product_id: productCode,
        quantity: quantity,
        price: price
      });
    }
    
    if (items.length === 0) {
      Swal.fire("❌ Error", "Debe agregar al menos un producto", "error");
      return;
    }

    // Calcular total
    const total = items.reduce((sum, item) => sum + (item.quantity * item.price), 0);

    const data = {
      client: client,
      items: items,
      total: total
    };

    try {
      const res = await fetch("/api/sales/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });

      const result = await res.json();
      if (res.ok) {
        Swal.fire("✅ Éxito", "Venta registrada con éxito", "success");
        form.reset();
        itemsContainer.innerHTML = ""; // Limpiar ítems
        totalElement.textContent = "0.00";
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
  const inputBusquedaCliente = document.getElementById("busquedaClienteVenta");
  const inputBusquedaTotal = document.getElementById("busquedaTotalVenta");
  
  const inputsBusqueda = [
    inputBusquedaCliente,
    inputBusquedaTotal
  ].filter(input => input); // Filtrar inputs válidos

  inputsBusqueda.forEach(input => {
    input.addEventListener("input", fetchVentas);
  });

  // 📦 Obtener ventas
  async function fetchVentas() {
    try {
      const query = inputBusquedaCliente?.value.trim() || "";
      const url = query ? `/api/sales/search?query=${encodeURIComponent(query)}` : "/api/sales/list";

      const res = await fetch(url);
      if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
      
      const ventas = await res.json();
      if (!Array.isArray(ventas)) throw new Error("Formato de respuesta inválido");

      renderVentas(ventas);
    } catch (err) {
      console.error("Error al cargar ventas:", err);
      if (messageDiv) {
        messageDiv.textContent = "❌ Error al cargar ventas: " + err.message;
      }
    }
  }

  // 🧱 Mostrar todas las ventas
  function renderVentas(ventas) {
    if (!tablaVentas) return;
    
    tablaVentas.innerHTML = "";
    
    const filtrarTotal = inputBusquedaTotal?.value.trim();

    ventas.forEach(venta => {
      // Filtrado por total
      if (filtrarTotal && venta.total !== parseFloat(filtrarTotal)) {
        return;
      }

      renderVenta(venta);
    });
  }

  // 🧱 Mostrar fila individual
  function renderVenta(venta) {
    const tr = document.createElement("tr");
    const fecha = new Date(venta.date).toLocaleDateString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });

    tr.innerHTML = `
      <td>${venta.client}</td>
      <td>${venta.items.length} productos</td>
      <td>${venta.total.toFixed(2)}</td>
      <td>${fecha}</td>
      <td>
        <button class="btn btn-primary btn-sm btn-detalles" data-id="${venta.id}">
          <i class="bi bi-eye"></i> Detalles
        </button>
        <button class="btn btn-danger btn-sm btn-eliminar" data-id="${venta.id}">
          <i class="bi bi-trash"></i>
        </button>
      </td>
    `;
    
    tablaVentas.appendChild(tr);
  }

  // 🎯 Event delegation para botones de detalles y eliminar
  tablaVentas.addEventListener("click", (e) => {
    if (e.target.classList.contains("btn-detalles") || 
        e.target.closest(".btn-detalles")) {
      const id = e.target.closest(".btn-detalles").dataset.id;
      verDetallesVenta(id);
    }
    
    if (e.target.classList.contains("btn-eliminar") || 
        e.target.closest(".btn-eliminar")) {
      const id = e.target.closest(".btn-eliminar").dataset.id;
      eliminarVenta(id);
    }
  });

  // 👁️ Ver detalles de la venta
  async function verDetallesVenta(id) {
    try {
      const res = await fetch(`/api/sales/${id}`);
      if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
      
      const venta = await res.json();
      
      let detallesHTML = `
        <div class="container">
          <h5 class="mb-3">Detalles de Venta</h5>
          <div class="row mb-3">
            <div class="col-md-6">
              <p><strong>Cliente:</strong> ${venta.client}</p>
            </div>
            <div class="col-md-6">
              <p><strong>Fecha:</strong> ${new Date(venta.date).toLocaleString()}</p>
            </div>
          </div>
          
          <h6 class="mb-3">Productos:</h6>
          <div class="table-responsive">
            <table class="table table-sm">
              <thead>
                <tr>
                  <th>Código</th>
                  <th>Producto</th>
                  <th>Cantidad</th>
                  <th>Precio Unitario</th>
                  <th>Subtotal</th>
                </tr>
              </thead>
              <tbody>
      `;
      
      venta.items.forEach(item => {
        detallesHTML += `
          <tr>
            <td>${item.product_id}</td>
            <td>${item.product_name || 'Desconocido'}</td>
            <td>${item.quantity}</td>
            <td>${item.price.toFixed(2)}</td>
            <td>${(item.quantity * item.price).toFixed(2)}</td>
          </tr>
        `;
      });
      
      detallesHTML += `
              </tbody>
              <tfoot>
                <tr class="table-primary">
                  <td colspan="4" class="text-end fw-bold">Total:</td>
                  <td class="fw-bold">${venta.total.toFixed(2)}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      `;
      
      Swal.fire({
        title: `Venta #${id}`,
        html: detallesHTML,
        width: '80%',
        showConfirmButton: false,
        showCloseButton: true
      });
    } catch (error) {
      console.error("Error al obtener detalles de la venta:", error);
      Swal.fire("❌ Error", "No se pudieron cargar los detalles de la venta", "error");
    }
  }

  // 🗑️ Eliminar venta
  async function eliminarVenta(id) {
    try {
      const confirm = await Swal.fire({
        title: "¿Eliminar venta?",
        text: "Esta acción es irreversible y revertirá el stock de productos",
        icon: "warning",
        showCancelButton: true,
        confirmButtonText: "Sí, eliminar",
        cancelButtonText: "Cancelar",
        confirmButtonColor: "#dc3545"
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

  // 🔍 Obtener información de un producto
  async function fetchProduct(code) {
    try {
      const res = await fetch(`/api/products/${code}`);
      if (res.ok) {
        return await res.json();
      }
      return null;
    } catch (error) {
      console.error("Error al buscar producto:", error);
      return null;
    }
  }

  // 🧮 Actualizar total de la venta
  function updateTotal() {
    const items = document.querySelectorAll(".item-form");
    let total = 0;
    
    items.forEach(item => {
      const quantity = parseFloat(item.querySelector(".quantity").value) || 0;
      const price = parseFloat(item.querySelector(".price").value) || 0;
      total += quantity * price;
    });
    
    totalElement.textContent = total.toFixed(2);
  }

  // ➕ Agregar el primer ítem al cargar la página
  addItemForm();
});