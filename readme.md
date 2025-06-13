Aquí tienes un README.md básico y profesional para el módulo de ventas de tu ERP, con instrucciones claras para desarrolladores que deseen integrarlo, probarlo o mantenerlo:

markdown
Copy
Edit
# 📦 Módulo de Ventas - ERP Backend

Este módulo forma parte del backend del ERP y gestiona la lógica relacionada con las **ventas de productos**, incluyendo registro, modificación, eliminación, control de stock y registro histórico de movimientos.

---

## 🚀 Endpoints disponibles

### ✅ Crear una nueva venta
- **POST** `/sales/`
- **Body JSON**:
```json
{
  "product_id": "64f123abc456...",
  "quantity": 2,
  "price": 15.99
}
⚙️ Disminuye el stock automáticamente y registra en historial.

📋 Listar todas las ventas
GET /sales/list

🔍 Devuelve un array de todas las ventas con sus respectivos id.

❌ Eliminar una venta
DELETE /sales/{sale_id}

⚙️ Reintegra el stock al producto y guarda reversión en historial.

✏️ Actualizar una venta
PUT /sales/{sale_id}

Body JSON igual al de creación.

⚙️ Ajusta la diferencia de stock y registra el cambio.

🔍 Buscar ventas por ID de producto
GET /sales/search/?query=PRODUCT_ID

🔎 Búsqueda flexible (regex, case-insensitive) por product_id.

📜 Ver historial de stock (relacionado con ventas)
GET /sales/stock-history

📊 Incluye nombre del producto, tipo de cambio y fecha.

📂 Estructura del módulo
text
Copy
Edit
backend/
└── routes/
    └── sales.py       # Rutas de la API relacionadas con ventas
📦 Dependencias utilizadas
FastAPI: Framework web principal

Pydantic: Validación de datos

motor: Cliente asíncrono de MongoDB

bson: Manejo de ObjectId

datetime: Registro de fechas para historial

🛠 Requisitos previos
MongoDB Atlas configurado con las colecciones:

products

sales

stock_history

El campo stock debe estar presente en cada documento de products.

✅ Buenas prácticas implementadas
Validaciones de cantidad y precio

Control y actualización automática del stock

Historial de movimientos de inventario

Respuestas claras para el frontend

🧪 Pruebas sugeridas
Crear venta con stock suficiente

Intentar vender con stock insuficiente

Editar venta aumentando y reduciendo cantidad

Eliminar venta y verificar reversión de stock

Ver historial actualizado tras cada operación

📩 Contacto / Soporte
Este módulo está pensado para integrarse con otros microservicios del ERP. Para soporte o contribuciones, contactar al equipo de desarrollo.

less
Copy
Edit

Este `README.md` puede colocarse directamente junto al archivo `sales.py` o en la raíz del módulo de backend.

¿Te gustaría que también te genere una colección de pruebas en Postman o Thunder Client para estos endpo