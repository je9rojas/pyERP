document.addEventListener("DOMContentLoaded", () => {
  // Selección de elementos esenciales
  const form = document.getElementById("compraForm");
  const itemsContainer = document.getElementById("itemsContainer");
  const addItemBtn = document.getElementById("addItemBtn");
  const totalElement = document.getElementById("totalCompra");
  
  // Verificar solo elementos absolutamente esenciales
  if (!form || !itemsContainer || !addItemBtn || !totalElement) {
    console.error("Elementos esenciales no encontrados en el DOM");
    showAlert("Error", "Elementos esenciales no encontrados en el DOM", "error");
    return;
  }

  // Elementos opcionales (historial de compras)
  const tablaCompras = document.getElementById("tablaCompras");
  let tablaBody = null;
  
  if (tablaCompras) {
    tablaBody = tablaCompras.querySelector("tbody");
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

  // 📌 Registrar compra
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const supplier = document.getElementById("supplier").value.trim();
    if (!supplier) {
      showAlert("Error", "Debe ingresar un proveedor", "error");
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
      supplier: supplier,
      items: items,
      total: total
    };

    try {
      const res = await fetch("/api/purchases/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });

      const result = await res.json();
      
      if (res.ok) {
        showAlert("Éxito", "Compra registrada con éxito", "success");
        
        // Resetear formulario
        form.reset();
        itemsContainer.innerHTML = "";
        totalElement.textContent = "0.00";
        
        // Recargar historial si existe
        if (tablaBody) {
          loadPurchases();
        }
        
        // Agregar nuevo ítem vacío
        addItemForm();
      } else {
        const errorMsg = result.detail || "Error desconocido";
        showAlert("Error", errorMsg, "error");
      }
    } catch (error) {
      console.error("Error al registrar compra:", error);
      showAlert("Error", "Error de conexión: " + error.message, "error");
    }
  });

  // 🧮 Actualizar total de la compra
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

  // 🧱 Mostrar todas las compras
  function renderPurchases(compras) {
    if (!tablaBody) return;
    
    tablaBody.innerHTML = "";
    
    compras.forEach(compra => {
      const tr = document.createElement("tr");
      const fecha = new Date(compra.date).toLocaleDateString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });

      tr.innerHTML = `
        <td>${compra.supplier || 'Sin proveedor'}</td>
        <td>${compra.items.length} productos</td>
        <td>${compra.total?.toFixed(2) || '0.00'}</td>
        <td>${fecha}</td>
        <td>
          <button class="btn btn-primary btn-sm btn-detalles" data-id="${compra.id}">
            <i class="bi bi-eye"></i> Detalles
          </button>
          <button class="btn btn-danger btn-sm btn-eliminar" data-id="${compra.id}">
            <i class="bi bi-trash"></i>
          </button>
        </td>
      `;
      
      tablaBody.appendChild(tr);
    });
    
    // Agregar event listeners a los botones
    tablaBody.querySelectorAll(".btn-detalles").forEach(btn => {
      btn.addEventListener("click", () => {
        viewPurchaseDetails(btn.dataset.id);
      });
    });
    
    tablaBody.querySelectorAll(".btn-eliminar").forEach(btn => {
      btn.addEventListener("click", () => {
        deletePurchase(btn.dataset.id);
      });
    });
  }

  // 👁️ Ver detalles de la compra
  async function viewPurchaseDetails(id) {
    try {
      const res = await fetch(`/api/purchases/${id}`);
      
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || `Error ${res.status}: ${res.statusText}`);
      }
      
      const compra = await res.json();
      
      let detallesHTML = `
        <div class="container">
          <h5 class="mb-3">Detalles de Compra</h5>
          <div class="row mb-3">
            <div class="col-md-6">
              <p><strong>Proveedor:</strong> ${compra.supplier || 'Sin proveedor'}</p>
            </div>
            <div class="col-md-6">
              <p><strong>Fecha:</strong> ${new Date(compra.date).toLocaleString()}</p>
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
      
      compra.items.forEach(item => {
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
                  <td class="fw-bold">${compra.total?.toFixed(2) || '0.00'}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      `;
      
      Swal.fire({
        title: `Compra #${id}`,
        html: detallesHTML,
        width: '80%',
        showConfirmButton: false,
        showCloseButton: true
      });
    } catch (error) {
      console.error("Error al obtener detalles de la compra:", error);
      showAlert("Error", "No se pudieron cargar los detalles: " + error.message, "error");
    }
  }

  // 🗑️ Eliminar compra
  async function deletePurchase(id) {
    try {
      // Usamos confirmAction para la confirmación
      confirmAction("¿Eliminar compra? Esta acción es irreversible y afectará el stock de productos", async () => {
        try {
          const res = await fetch(`/api/purchases/${id}`, { method: "DELETE" });
          
          if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.detail || `Error ${res.status}: ${res.statusText}`);
          }
          
          const result = await res.json();
          
          showAlert("Eliminada", result.message || "Compra eliminada correctamente", "success");
          
          // Recargar historial
          if (tablaBody) {
            loadPurchases();
          }
        } catch (error) {
          console.error("Error al eliminar compra:", error);
          showAlert("Error", "Error al eliminar: " + error.message, "error");
        }
      });
    } catch (error) {
      console.error("Error en la confirmación:", error);
    }
  }

  // 📦 Obtener compras
  async function loadPurchases() {
    try {
      if (!tablaBody) return;
      
      // Obtener el valor de búsqueda
      const searchInput = document.getElementById("busquedaProveedorCompra");
      const query = searchInput ? searchInput.value.trim() : "";
      
      const url = query ? 
        `/api/purchases/search?query=${encodeURIComponent(query)}` : 
        "/api/purchases/list";

      const res = await fetch(url);
      
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || `Error ${res.status}: ${res.statusText}`);
      }
      
      const compras = await res.json();
      if (!Array.isArray(compras)) throw new Error("Formato de respuesta inválido");

      renderPurchases(compras);
    } catch (err) {
      console.error("Error al cargar compras:", err);
      showAlert("Error", "Error al cargar compras: " + err.message, "error");
    }
  }

  // Inicialización final
  if (tablaBody) {
    // Configurar evento de búsqueda
    const searchInput = document.getElementById("busquedaProveedorCompra");
    if (searchInput) {
      searchInput.addEventListener("input", loadPurchases);
    }
    
    // Cargar compras iniciales
    loadPurchases();
  }

  // ➕ Agregar el primer ítem al cargar la página
  addItemForm();
});

// Función para mostrar alertas con SweetAlert
function showAlert(title, text, icon) {
  Swal.fire({
    title: title,
    text: text,
    icon: icon,
    confirmButtonText: 'Aceptar'
  });
}

// Función para confirmar acciones
function confirmAction(message, callback) {
  Swal.fire({
    title: '¿Estás seguro?',
    text: message,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#3085d6',
    cancelButtonColor: '#d33',
    confirmButtonText: 'Sí',
    cancelButtonText: 'Cancelar'
  }).then((result) => {
    if (result.isConfirmed) {
      callback();
    }
  });
}