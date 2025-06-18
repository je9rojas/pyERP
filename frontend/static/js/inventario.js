document.addEventListener("DOMContentLoaded", () => {
    const inventoryBody = document.getElementById("inventoryBody");
    const historyBody = document.getElementById("historyBody");
    const searchInput = document.getElementById("searchInventory");
    
    // Cargar inventario inicial
    fetchInventory();
    
    // Búsqueda en tiempo real
    searchInput.addEventListener("input", () => {
        filterInventory(searchInput.value.trim());
    });
    
    async function fetchInventory() {
        try {
            // Mostrar estado de carga
            showLoading(true);
            
            const response = await fetch("/api/inventory/list");
            const inventory = await response.json();
            
            if (!Array.isArray(inventory)) {
                throw new Error("Formato de respuesta inválido");
            }
            
            renderInventory(inventory);
        } catch (error) {
            console.error("Error al cargar inventario:", error);
            showAlert("Error al cargar inventario", "error");
        } finally {
            showLoading(false);
        }
    }
    
    function renderInventory(inventory) {
        // Limpiar tablas
        inventoryBody.innerHTML = "";
        historyBody.innerHTML = "";
        
        // Ordenar por stock (de menor a mayor)
        inventory.sort((a, b) => a.current_stock - b.current_stock);
        
        // Contador para movimientos recientes
        let recentMovements = 0;
        const maxRecentMovements = 10;
        
        inventory.forEach(item => {
            // Determinar clase CSS según stock
            let stockClass = "bg-success";
            if (item.current_stock <= 3) stockClass = "bg-danger";
            else if (item.current_stock <= 10) stockClass = "bg-warning";
            
            // Fila de inventario (BOTÓN CORREGIDO CON TEXTO)
            const row = document.createElement("tr");
            row.innerHTML = `
                <td class="text-center fw-bold">${item.code}</td>
                <td>${item.name}</td>
                <td class="text-center">
                    <span class="badge ${stockClass} rounded-pill fs-6">
                        ${item.current_stock}
                    </span>
                </td>
                <td class="text-center">${formatDate(item.last_updated)}</td>
                <td class="text-center">
                    <button class="btn btn-sm btn-outline-primary btn-view-history" 
                            data-code="${item.code}">
                        <i class="bi bi-clock-history me-1"></i> Ver historial
                    </button>
                </td>
            `;
            inventoryBody.appendChild(row);
            
            // Historial (últimos movimientos - CAMPOS CORREGIDOS)
            item.history.forEach(movement => {
                if (recentMovements < maxRecentMovements) {
                    const movementType = getMovementType(movement.type);  // Usar type en lugar de reason
                    const movementClass = movement.quantity > 0 ? "text-success" : "text-danger";  // Usar quantity en lugar de change
                    
                    const historyRow = document.createElement("tr");
                    historyRow.innerHTML = `
                        <td>${item.code} - ${item.name}</td>
                        <td class="text-center">${movementType}</td>
                        <td class="text-center ${movementClass} fw-bold">
                            ${movement.quantity > 0 ? '+' : ''}${movement.quantity}
                        </td>
                        <td class="text-center">${formatDate(movement.date)}</td>
                    `;
                    historyBody.appendChild(historyRow);
                    recentMovements++;
                }
            });
        });
        
        // Inicializar tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(tooltipTriggerEl => {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
        // Eventos para botones de historial
        document.querySelectorAll(".btn-view-history").forEach(btn => {
            btn.addEventListener("click", () => {
                const productCode = btn.dataset.code;
                viewFullHistory(productCode);
            });
        });
    }
    
    function filterInventory(query) {
        const rows = inventoryBody.querySelectorAll("tr");
        let visibleCount = 0;
        
        rows.forEach(row => {
            if (row.cells.length > 1) { // Ignorar filas de carga
                const code = row.cells[0].textContent.toLowerCase();
                const name = row.cells[1].textContent.toLowerCase();
                const text = `${code} ${name}`;
                
                if (text.includes(query.toLowerCase())) {
                    row.style.display = "";
                    visibleCount++;
                } else {
                    row.style.display = "none";
                }
            }
        });
        
        // Mostrar mensaje si no hay resultados
        if (visibleCount === 0 && query) {
            inventoryBody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center py-4">
                        <i class="bi bi-search display-5 text-muted"></i>
                        <h5 class="mt-3">No se encontraron productos</h5>
                        <p class="text-muted">Intenta con otro término de búsqueda</p>
                    </td>
                </tr>
            `;
        }
    }
    
    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('es-ES', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    function getMovementType(type) {
        // MANEJO MEJORADO DE VALORES NO DEFINIDOS
        if (!type) type = "unknown";
        
        const types = {
            "purchase": "<span class='badge bg-success'><i class='bi bi-cart-plus'></i> Compra</span>",
            "sale": "<span class='badge bg-primary'><i class='bi bi-cart-dash'></i> Venta</span>",
            "purchase_edit": "<span class='badge bg-warning'><i class='bi bi-pencil'></i> Ajuste Compra</span>",
            "sale_edit": "<span class='badge bg-warning'><i class='bi bi-pencil'></i> Ajuste Venta</span>",
            "reversión venta": "<span class='badge bg-info'><i class='bi bi-arrow-counterclockwise'></i> Reversión</span>",
            "unknown": "<span class='badge bg-secondary'>Desconocido</span>"
        };
        
        return types[type] || `<span class='badge bg-secondary'>${type}</span>`;
    }
    
    async function viewFullHistory(productCode) {
        try {
            // Mostrar loader en el modal
            Swal.fire({
                title: `Cargando historial: ${productCode}`,
                html: '<div class="spinner-border text-primary" role="status"></div>',
                showConfirmButton: false,
                allowOutsideClick: false
            });
            
            const response = await fetch(`/api/inventory/history?product_id=${productCode}`);
            const history = await response.json();
            
            if (history.length === 0) {
                Swal.close();
                showAlert("No hay historial para este producto", "info");
                return;
            }
            
            // Construir tabla de historial
            let historyHTML = `<div class="table-responsive">
                <table class="table table-sm table-hover">
                    <thead class="table-light">
                        <tr>
                            <th>Fecha</th>
                            <th>Tipo</th>
                            <th class="text-end">Cantidad</th>
                        </tr>
                    </thead>
                    <tbody>`;
            
            history.forEach(item => {
                const movementClass = item.change > 0 ? "text-success" : "text-danger";
                historyHTML += `
                    <tr>
                        <td>${formatDate(item.date)}</td>
                        <td>${getMovementType(item.reason)}</td>
                        <td class="text-end ${movementClass} fw-bold">
                            ${item.change > 0 ? '+' : ''}${item.change}
                        </td>
                    </tr>
                `;
            });
            
            historyHTML += "</tbody></table></div>";
            
            // Mostrar modal con historial
            Swal.fire({
                title: `Historial completo: ${productCode}`,
                html: historyHTML,
                width: "90%",
                confirmButtonText: "Cerrar",
                customClass: {
                    popup: 'rounded-3'
                }
            });
            
        } catch (error) {
            console.error("Error al obtener historial:", error);
            showAlert("Error al cargar historial", "error");
        }
    }
    
    function showAlert(message, type = "success") {
        const icon = type === "error" ? "bi-exclamation-circle" : 
                    type === "info" ? "bi-info-circle" : "bi-check-circle";
        
        Swal.fire({
            icon: type,
            title: message,
            showConfirmButton: false,
            timer: 3000,
            customClass: {
                popup: 'rounded-3'
            }
        });
    }
    
    function showLoading(loading) {
        if (loading) {
            inventoryBody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center py-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Cargando...</span>
                        </div>
                        <p class="mt-2 mb-0">Cargando inventario...</p>
                    </td>
                </tr>
            `;
            
            historyBody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-4">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Cargando...</span>
                        </div>
                        <p class="mt-2 mb-0">Cargando movimientos...</p>
                    </td>
                </tr>
            `;
        }
    }
});