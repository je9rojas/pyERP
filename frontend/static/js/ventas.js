// 📁 frontend/static/js/ventas.js
document.addEventListener("DOMContentLoaded", () => {
  // Selección de elementos esenciales
  const form = document.getElementById("ventaForm");
  const itemsContainer = document.getElementById("itemsContainer");
  const addItemBtn = document.getElementById("addItemBtn");
  const totalElement = document.getElementById("totalVenta");
  
  // Verificar solo elementos absolutamente esenciales
  if (!form || !itemsContainer || !addItemBtn || !totalElement) {
    console.error("Elementos esenciales no encontrados en el DOM");
    showAlert("Error", "Elementos esenciales no encontrados en el DOM", "error");
    return;
  }

  // Elementos opcionales (historial de ventas)
  const tablaVentas = document.getElementById("tablaVentas");
  let tablaBody = null;
  
  if (tablaVentas) {
    tablaBody = tablaVentas.querySelector("tbody");
  }

  let itemCounter = 0;
  
  // Cache local para productos
  const productCache = new Map();

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
    
    // Configurar autocompletado para producto con debouncing y cache
    const productInput = itemDiv.querySelector(".product-code");
    let timeoutId = null;

    productInput.addEventListener("input", (e) => {
      const code = e.target.value.trim();
      
      // 1. Limpiar timeout anterior
      clearTimeout(timeoutId);
      
      // 2. Requerir mínimo 4 caracteres
      if (code.length < 4) return;
      
      // 3. Usar debouncing de 300ms
      timeoutId = setTimeout(async () => {
        // 4. Primero verificar caché local
        if (productCache.has(code)) {
          const priceInput = itemDiv.querySelector(".price");
          priceInput.value = productCache.get(code);
          updateTotal();
          return;
        }
        
        // 5. Hacer solicitud al servidor
        const product = await fetchProduct(code);
        if (product) {
          // Guardar en caché
          productCache.set(code, product.price);
          
          const priceInput = itemDiv.querySelector(".price");
          priceInput.value = product.price;
          updateTotal();
        }
      }, 300);
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
      showAlert("Error", "Debe ingresar un cliente", "error");
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
        showAlert("Error", "Datos incompletos en los ítems", "error");
        return;
      }
      
      items.push({
        product_id: productCode,
        quantity: quantity,
        price: price
      });
    }
    
    if (items.length === 0) {
      showAlert("Error", "Debe agregar al menos un producto", "error");
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
        showAlert("Éxito", "Venta registrada con éxito", "success");
        
        // Resetear formulario
        form.reset();
        itemsContainer.innerHTML = "";
        totalElement.textContent = "0.00";
        
        // Recargar historial si existe
        if (tablaBody) {
          loadSales();
        }
        
        // Agregar nuevo ítem vacío
        addItemForm();
      } else {
        const errorMsg = result.detail || "Error desconocido";
        showAlert("Error", errorMsg, "error");
      }
    } catch (error) {
      console.error("Error al registrar venta:", error);
      showAlert("Error", "Error de conexión: " + error.message, "error");
    }
  });

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

  // 🧱 Mostrar todas las ventas
  function renderSales(ventas) {
    if (!tablaBody) return;
    
    tablaBody.innerHTML = "";
    
    ventas.forEach(venta => {
      const tr = document.createElement("tr");
      const fecha = new Date(venta.date).toLocaleDateString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });

      tr.innerHTML = `
        <td>${venta.client || 'Sin nombre'}</td>
        <td>${venta.items.length} productos</td>
        <td>${venta.total?.toFixed(2) || '0.00'}</td>
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
      
      tablaBody.appendChild(tr);
    });
    
    // Agregar event listeners a los botones
    tablaBody.querySelectorAll(".btn-detalles").forEach(btn => {
      btn.addEventListener("click", () => {
        viewSaleDetails(btn.dataset.id);
      });
    });
    
    tablaBody.querySelectorAll(".btn-eliminar").forEach(btn => {
      btn.addEventListener("click", () => {
        deleteSale(btn.dataset.id);
      });
    });
  }

  // 👁️ Ver detalles de la venta
  async function viewSaleDetails(id) {
    try {
      const res = await fetch(`/api/sales/${id}`);
      
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || `Error ${res.status}: ${res.statusText}`);
      }
      
      const venta = await res.json();
      
      let detallesHTML = `
        <div class="container">
          <h5 class="mb-3">Detalles de Venta</h5>
          <div class="row mb-3">
            <div class="col-md-6">
              <p><strong>Cliente:</strong> ${venta.client || 'Sin nombre'}</p>
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
        const productName = item.product_name || 'Desconocido';
        const price = item.price?.toFixed(2) || '0.00';
        const subtotal = (item.quantity * item.price)?.toFixed(2) || '0.00';
        
        detallesHTML += `
          <tr>
            <td>${item.product_id}</td>
            <td>${productName}</td>
            <td>${item.quantity}</td>
            <td>${price}</td>
            <td>${subtotal}</td>
          </tr>
        `;
      });
      
      detallesHTML += `
              </tbody>
              <tfoot>
                <tr class="table-primary">
                  <td colspan="4" class="text-end fw-bold">Total:</td>
                  <td class="fw-bold">${venta.total?.toFixed(2) || '0.00'}</td>
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
      showAlert("Error", "No se pudieron cargar los detalles: " + error.message, "error");
    }
  }

  // 🗑️ Eliminar venta
  async function deleteSale(id) {
    try {
      // Usamos confirmAction para la confirmación
      confirmAction("¿Eliminar venta? Esta acción es irreversible y revertirá el stock de productos", async () => {
        try {
          const res = await fetch(`/api/sales/${id}`, { method: "DELETE" });
          
          if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.detail || `Error ${res.status}: ${res.statusText}`);
          }
          
          const result = await res.json();
          
          showAlert("Eliminada", result.message || "Venta eliminada correctamente", "success");
          
          // Recargar historial
          if (tablaBody) {
            loadSales();
          }
        } catch (error) {
          console.error("Error al eliminar venta:", error);
          showAlert("Error", "Error al eliminar: " + error.message, "error");
        }
      });
    } catch (error) {
      console.error("Error en la confirmación:", error);
    }
  }

  // 📦 Obtener ventas
  async function loadSales() {
    try {
      if (!tablaBody) return;
      
      // Obtener el valor de búsqueda directamente por ID
      const searchInput = document.getElementById("busquedaClienteVenta");
      const query = searchInput ? searchInput.value.trim() : "";
      
      const url = query ? 
        `/api/sales/search?query=${encodeURIComponent(query)}` : 
        "/api/sales/list";

      const res = await fetch(url);
      
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || `Error ${res.status}: ${res.statusText}`);
      }
      
      const ventas = await res.json();
      if (!Array.isArray(ventas)) throw new Error("Formato de respuesta inválido");

      renderSales(ventas);
    } catch (err) {
      console.error("Error al cargar ventas:", err);
      showAlert("Error", "Error al cargar ventas: " + err.message, "error");
    }
  }

  // Inicialización final
  if (tablaBody) {
    // Configurar evento de búsqueda
    const searchInput = document.getElementById("busquedaClienteVenta");
    if (searchInput) {
      searchInput.addEventListener("input", loadSales);
    }
    
    // Cargar ventas iniciales
    loadSales();
  }

  // ➕ Agregar el primer ítem al cargar la página
  addItemForm();
});