// 📁 frontend/static/js/compras.js
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
  const tablaBody = tablaCompras ? tablaCompras.querySelector("tbody") : null;
  const mensajeInicial = document.getElementById("mensajeInicial");

  let itemCounter = 0;
  
  // Cache local para productos
  const productCache = new Map();

  // Variables para paginación
  let currentPage = 1;
  const itemsPerPage = 10; // Compras por página
  let totalCompras = 0;

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
    
    if (compras.length === 0) {
      tablaBody.innerHTML = `<tr><td colspan="5" class="text-center">No se encontraron compras</td></tr>`;
      return;
    }
    
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
        <td class="text-center">
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
          
          // Recargar historial solo si ya hay una búsqueda activa
          if (tablaBody.innerHTML !== "" && !mensajeInicial) {
            loadPurchases(currentPage, getCurrentFilters());
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

  // 📦 Obtener compras con paginación y filtros
  async function loadPurchases(page = 1, filters = {}) {
    try {
      if (!tablaBody) return;
      
      // Mostrar spinner de carga
      tablaBody.innerHTML = `<tr><td colspan="5" class="text-center"><div class="spinner-border" role="status"></div> Cargando compras...</td></tr>`;
      
      // Construir parámetros de búsqueda
      const params = new URLSearchParams({
        page: page,
        per_page: itemsPerPage
      });
      
      // Agregar filtros si existen
      if (filters.proveedor) params.append("proveedor", filters.proveedor);
      if (filters.producto) params.append("producto", filters.producto);
      if (filters.fechaInicio) params.append("fecha_inicio", filters.fechaInicio);
      if (filters.fechaFin) params.append("fecha_fin", filters.fechaFin);
      
      const url = `/api/purchases/search?${params.toString()}`;
      
      const res = await fetch(url);
      
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || `Error ${res.status}: ${res.statusText}`);
      }
      
      const data = await res.json();
      
      // Manejar diferentes formatos de respuesta
      let compras = [];
      if (Array.isArray(data)) {
        // Formato antiguo (sin paginación)
        compras = data;
        totalCompras = data.length;
      } else if (data.compras && Array.isArray(data.compras)) {
        // Formato nuevo (con paginación)
        compras = data.compras;
        totalCompras = data.total;
      } else {
        throw new Error("Formato de respuesta inválido");
      }
      
      if (!Array.isArray(compras)) {
        throw new Error("Formato de compras inválido");
      }

      renderPurchases(compras);
      renderPagination(page, totalCompras);
      
      // Ocultar mensaje inicial si existe
      if (mensajeInicial) {
        mensajeInicial.style.display = "none";
      }
    } catch (err) {
      console.error("Error al cargar compras:", err);
      showAlert("Error", "Error al cargar compras: " + err.message, "error");
      if (tablaBody) {
        tablaBody.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Error al cargar datos</td></tr>`;
      }
    }
  }
  
  // 🧩 Renderizar paginación
  function renderPagination(currentPage, totalItems) {
    const pagination = document.getElementById("paginacionCompras");
    if (!pagination) return;
    
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    pagination.innerHTML = "";
    
    if (totalPages <= 1) return;
    
    // Botón Anterior
    const prevItem = document.createElement("li");
    prevItem.className = `page-item ${currentPage === 1 ? "disabled" : ""}`;
    prevItem.innerHTML = `<a class="page-link" href="#" data-page="${currentPage - 1}">&laquo;</a>`;
    pagination.appendChild(prevItem);
    
    // Páginas
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
      const pageItem = document.createElement("li");
      pageItem.className = `page-item ${i === currentPage ? "active" : ""}`;
      pageItem.innerHTML = `<a class="page-link" href="#" data-page="${i}">${i}</a>`;
      pagination.appendChild(pageItem);
    }
    
    // Botón Siguiente
    const nextItem = document.createElement("li");
    nextItem.className = `page-item ${currentPage === totalPages ? "disabled" : ""}`;
    nextItem.innerHTML = `<a class="page-link" href="#" data-page="${currentPage + 1}">&raquo;</a>`;
    pagination.appendChild(nextItem);
    
    // Eventos de paginación
    pagination.querySelectorAll(".page-link").forEach(link => {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        const page = parseInt(link.dataset.page);
        if (!isNaN(page)) {
          currentPage = page;
          loadPurchases(currentPage, getCurrentFilters());
        }
      });
    });
  }
  
  // 🧾 Obtener filtros actuales
  function getCurrentFilters() {
    const fechaInput = document.getElementById("filtroFecha");
    let fechaInicio = "";
    let fechaFin = "";
    
    if (fechaInput && fechaInput._flatpickr) {
      const selectedDates = fechaInput._flatpickr.selectedDates;
      if (selectedDates.length === 2) {
        fechaInicio = selectedDates[0].toISOString().split('T')[0];
        fechaFin = selectedDates[1].toISOString().split('T')[0];
      }
    }
    
    return {
      proveedor: document.getElementById("filtroProveedor").value.trim(),
      producto: document.getElementById("filtroProducto").value.trim(),
      fechaInicio: fechaInicio,
      fechaFin: fechaFin
    };
  }
  
  // Inicialización final
  if (tablaBody) {
    // Configurar evento de búsqueda
    const filtroForm = document.getElementById("filtroComprasForm");
    if (filtroForm) {
      filtroForm.addEventListener("submit", (e) => {
        e.preventDefault();
        currentPage = 1;
        loadPurchases(currentPage, getCurrentFilters());
      });
    }
    
    // Configurar botón limpiar
    const btnLimpiar = document.getElementById("btnLimpiarFiltros");
    if (btnLimpiar) {
      btnLimpiar.addEventListener("click", () => {
        document.getElementById("filtroProveedor").value = "";
        document.getElementById("filtroProducto").value = "";
        const fechaInput = document.getElementById("filtroFecha");
        if (fechaInput && fechaInput._flatpickr) {
          fechaInput._flatpickr.clear();
        }
        
        // Restaurar mensaje inicial
        if (mensajeInicial) {
          mensajeInicial.style.display = "";
          tablaBody.innerHTML = "";
          tablaBody.appendChild(mensajeInicial);
        }
        
        // Limpiar paginación
        const pagination = document.getElementById("paginacionCompras");
        if (pagination) pagination.innerHTML = "";
      });
    }
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