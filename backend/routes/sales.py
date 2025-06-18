# 📁 backend/routes/sales.py

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from backend.database import get_database
from bson import ObjectId
from datetime import datetime
from typing import List
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# ======================================
# 🧾 Modelos de datos (entrada y salida)
# ======================================

class SaleCreate(BaseModel):
    product_id: str
    quantity: int
    price: float

class SaleOut(SaleCreate):
    id: str
    product_code: str
    name: str

# ===========================
# 🔁 Ruta de prueba
# ===========================

@router.get("/")
async def test_sales():
    return {"message": "✅ Ruta de ventas funcionando correctamente"}

# ===========================
# ✅ Crear una nueva venta (CORREGIDO)
# ===========================

@router.post("/")
async def create_sale(sale: SaleCreate = Body(...)):
    # Obtener la base de datos
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no disponible")
    
    if sale.quantity <= 0:
        raise HTTPException(status_code=400, detail="Cantidad inválida")
    if sale.price < 0:
        raise HTTPException(status_code=400, detail="Precio inválido")

    # Buscar el producto - CORRECCIÓN: Usar notación de diccionario
    product = await db["products"].find_one({"code": sale.product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Verificar stock - CORRECCIÓN: Acceder directamente al campo
    if "stock" not in product or product["stock"] < sale.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuficiente. Disponible: {product.get('stock', 0)}"
        )

    # Crear documento de venta
    sale_data = sale.dict()
    sale_data["date"] = datetime.utcnow()
    
    # Insertar en la colección 'sales'
    result = await db["sales"].insert_one(sale_data)

    # Actualizar stock del producto
    await db["products"].update_one(
        {"code": sale.product_id},
        {"$inc": {"stock": -sale.quantity}}
    )

    # Registrar en historial
    await db["stock_history"].insert_one({
        "product_id": sale.product_id,
        "change": -sale.quantity,
        "reason": "venta",
        "date": datetime.utcnow()
    })

    return {
        "message": "✅ Venta registrada con éxito",
        "id": str(result.inserted_id),
        "sale": sale_data
    }

# ===========================
# 📋 Listar todas las ventas
# ===========================

@router.get("/list")
async def list_sales():
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no disponible")
    
    ventas = []
    cursor = db["sales"].find().sort("date", -1)

    async for venta in cursor:
        producto = await db["products"].find_one({"code": venta["product_id"]})
        ventas.append({
            "id": str(venta["_id"]),
            "product_id": venta["product_id"],
            "product_code": venta["product_id"],
            "name": producto["name"] if producto else "Desconocido",
            "quantity": venta["quantity"],
            "price": venta["price"],
            "date": venta.get("date", venta.get("_id").generation_time)
        })

    return ventas

# ========================================
# ❌ Eliminar una venta y revertir el stock
# ========================================

@router.delete("/{sale_id}")
async def delete_sale(sale_id: str):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no disponible")
    
    try:
        object_id = ObjectId(sale_id)
    except:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    venta = await db["sales"].find_one({"_id": object_id})
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    producto = await db["products"].find_one({"code": venta["product_id"]})
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Eliminar venta
    await db["sales"].delete_one({"_id": object_id})

    # Revertir stock
    await db["products"].update_one(
        {"code": venta["product_id"]},
        {"$inc": {"stock": venta["quantity"]}}
    )

    # Registrar en historial
    await db["stock_history"].insert_one({
        "product_id": venta["product_id"],
        "change": venta["quantity"],
        "reason": "reversión venta",
        "date": datetime.utcnow()
    })

    return {"message": "✅ Venta eliminada correctamente"}

# ====================================
# ✏️ Actualizar una venta y el stock
# ====================================

@router.put("/{sale_id}")
async def update_sale(sale_id: str, updated: SaleCreate):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no disponible")
    
    try:
        object_id = ObjectId(sale_id)
    except:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    if updated.quantity <= 0:
        raise HTTPException(status_code=400, detail="Cantidad inválida")
    if updated.price < 0:
        raise HTTPException(status_code=400, detail="Precio inválido")

    venta = await db["sales"].find_one({"_id": object_id})
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    producto = await db["products"].find_one({"code": updated.product_id})
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Calcular diferencia
    diferencia = updated.quantity - venta["quantity"]

    # Verificar stock si se aumenta la cantidad
    if diferencia > 0:
        stock_actual = producto.get("stock", 0)
        if stock_actual < diferencia:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente. Disponible: {stock_actual}"
            )

    # Actualizar venta
    await db["sales"].update_one(
        {"_id": object_id},
        {"$set": updated.dict()}
    )

    # Actualizar stock
    await db["products"].update_one(
        {"code": updated.product_id},
        {"$inc": {"stock": -diferencia}}
    )

    # Registrar en historial
    await db["stock_history"].insert_one({
        "product_id": updated.product_id,
        "change": -diferencia,
        "reason": "edición venta",
        "date": datetime.utcnow()
    })

    return {"message": "✅ Venta actualizada con éxito"}

# ====================================
# 🔍 Buscar ventas por ID de producto
# ====================================

@router.get("/search")
async def search_sales(query: str = ""):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no disponible")
    
    filtro = {"product_id": {"$regex": query, "$options": "i"}}
    cursor = db["sales"].find(filtro)
    resultados = []

    async for venta in cursor:
        producto = await db["products"].find_one({"code": venta["product_id"]})
        resultados.append({
            "id": str(venta["_id"]),
            "product_id": venta["product_id"],
            "product_code": venta["product_id"],
            "name": producto["name"] if producto else "Desconocido",
            "quantity": venta["quantity"],
            "price": venta["price"]
        })

    return resultados

# ==================================================
# 📜 Ver historial de stock (con nombre del producto)
# ==================================================

@router.get("/stock-history")
async def ver_historial():
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no disponible")
    
    pipeline = [
        {
            "$lookup": {
                "from": "products",
                "localField": "product_id",
                "foreignField": "code",
                "as": "producto"
            }
        },
        {"$unwind": {"path": "$producto", "preserveNullAndEmptyArrays": True}},
        {"$sort": {"date": -1}},
        {"$limit": 100}
    ]

    historial = []
    cursor = db["stock_history"].aggregate(pipeline)
    
    async for movimiento in cursor:
        historial.append({
            "id": str(movimiento["_id"]),
            "product_id": movimiento["product_id"],
            "product_name": movimiento.get("producto", {}).get("name", "Desconocido"),
            "change": movimiento["change"],
            "reason": movimiento["reason"],
            "date": movimiento["date"]
        })

    return historial