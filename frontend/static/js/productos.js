document.addEventListener("DOMContentLoaded", () => {
    const productForm = document.getElementById("productForm");
    const codeInput = document.getElementById("productCode");
    const nameInput = document.getElementById("productName");
    const priceInput = document.getElementById("productPrice");
    const stockInput = document.getElementById("productStock");
    const descriptionInput = document.getElementById("productDescription");
    const feedbackElement = document.getElementById("formFeedback");
    
    // Verificar si los elementos existen
    if (!productForm) {
        console.error("Formulario de productos no encontrado");
        return;
    }
    
    // Evento de envío del formulario
    productForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        // Mostrar carga
        feedbackElement.innerHTML = `
            <div class="spinner-border spinner-border-sm" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div> Registrando producto...
        `;
        feedbackElement.className = "form-text text-primary";
        
        try {
            // Validar campos requeridos
            if (!codeInput.value.trim()) throw new Error("El código es requerido");
            if (!nameInput.value.trim()) throw new Error("El nombre es requerido");
            
            // Validar y obtener precio
            const priceValue = priceInput.value.trim();
            if (!priceValue) throw new Error("El precio es requerido");
            const price = parseFloat(priceValue);
            if (isNaN(price)) throw new Error("Precio inválido");
            if (price <= 0) throw new Error("El precio debe ser mayor que cero");
            
            // Validar y obtener stock
            const stockValue = stockInput.value.trim();
            if (!stockValue) throw new Error("El stock es requerido");
            const stock = parseInt(stockValue);
            if (isNaN(stock)) throw new Error("Stock inválido");
            if (stock < 0) throw new Error("El stock no puede ser negativo");
            
            // Crear objeto producto
            const productData = {
                code: codeInput.value.trim(),
                name: nameInput.value.trim(),
                price: price,
                stock: stock,
                description: descriptionInput.value.trim() || ""
            };
            
            // Enviar al servidor
            const response = await fetch("/api/products", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(productData)
            });
            
            if (!response.ok) {
                // Intentar obtener el mensaje de error del servidor
                let errorMsg = "Error en el servidor";
                try {
                    const errorData = await response.json();
                    errorMsg = errorData.detail || errorMsg;
                } catch (e) {
                    // Si no se puede parsear la respuesta, usar el status
                    errorMsg = `Error ${response.status}: ${response.statusText}`;
                }
                throw new Error(errorMsg);
            }
            
            // Éxito
            const newProduct = await response.json();
            feedbackElement.innerHTML = `
                <div class="d-flex align-items-center">
                    <i class="bi bi-check-circle-fill text-success me-2"></i>
                    Producto <strong>${newProduct.name}</strong> registrado exitosamente!
                </div>
            `;
            feedbackElement.className = "form-text text-success";
            
            // Resetear formulario
            productForm.reset();
            
            // Opcional: Redirigir o actualizar lista de productos
            // window.location.href = "/inventario";
            
        } catch (error) {
            console.error("Error al registrar producto:", error);
            feedbackElement.innerHTML = `
                <div class="d-flex align-items-center">
                    <i class="bi bi-exclamation-circle-fill text-danger me-2"></i>
                    ${error.message}
                </div>
            `;
            feedbackElement.className = "form-text text-danger";
        }
    });
    
    // Generar código automático si está vacío
    nameInput.addEventListener("blur", () => {
        if (!codeInput.value.trim()) {
            const name = nameInput.value.trim();
            if (name) {
                // Generar código: primeras 2 letras de cada palabra en mayúscula
                const code = name.split(/\s+/)
                    .filter(word => word.length > 0)
                    .map(word => word.substring(0, 2).toUpperCase())
                    .join("");
                
                codeInput.value = code;
            }
        }
    });
    
    // Validación en tiempo real para campos numéricos
    priceInput.addEventListener("input", () => {
        const value = priceInput.value.trim();
        if (value && (isNaN(value) || parseFloat(value) <= 0)) {
            priceInput.classList.add("is-invalid");
        } else {
            priceInput.classList.remove("is-invalid");
        }
    });
    
    stockInput.addEventListener("input", () => {
        const value = stockInput.value.trim();
        if (value && (isNaN(value) || parseInt(value) < 0)) {
            stockInput.classList.add("is-invalid");
        } else {
            stockInput.classList.remove("is-invalid");
        }
    });
    
    // Validación en tiempo real para campos requeridos
    const validateRequiredFields = () => {
        const requiredFields = [codeInput, nameInput, priceInput, stockInput];
        let allValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add("is-invalid");
                allValid = false;
            } else {
                field.classList.remove("is-invalid");
            }
        });
        
        return allValid;
    };
    
    // Escuchar cambios en los campos requeridos
    [codeInput, nameInput, priceInput, stockInput].forEach(field => {
        field.addEventListener("input", () => {
            if (field.value.trim()) {
                field.classList.remove("is-invalid");
            } else {
                field.classList.add("is-invalid");
            }
        });
    });
});