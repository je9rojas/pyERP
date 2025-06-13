# 📁 backend/routes/sales.py

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from backend.database import db
from bson import ObjectId
from datetime import datetime
from typing import List

router = APIRouter()

# ======================================
# 🧾 Modelos de datos (entrada y salida)
# ======================================

class SaleCreate(BaseModel):
    product_id: str  # es el 'code' del producto
    quantity: int
    price: float

class SaleOut(SaleCreate):
    id: str
    product_code: str  # para frontend
    name: str          # nombre del producto (opcional para mostrar)

# ===========================
# 🔁 Ruta de prueba
# ===========================

@router.get("/")
async def test_sales():
    return {"message": "✅ Ruta de ventas funcionando correctamente"}

# ===========================
# ✅ Crear una nueva venta
# ===========================

@router.post("/")
async def create_sale(sale: SaleCreate = Body(...)):
    if sale.quantity <= 0:
        raise HTTPException(status_code=400, detail="Cantidad inválida")
    if sale.price < 0:
        raise HTTPException(status_code=400, detail="Precio inválido")

    product = await db["products"].find_one({"code": sale.product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    if product.get("stock", 0) < sale.quantity:
        raise HTTPException(status_code=400, detail="Stock insuficiente")

    result = await db["sales"].insert_one(sale.dict())

    await db["products"].update_one(
        {"code": sale.product_id},
        {"$inc": {"stock": -sale.quantity}}
    )

    await db["stock_history"].insert_one({
        "product_id": sale.product_id,  # guarda el code
        "change": -sale.quantity,
        "reason": "venta",
        "date": datetime.utcnow()
    })

    return {
        "message": "✅ Venta registrada con éxito",
        "id": str(result.inserted_id),
        "sale": sale.dict()
    }

# ===========================
# 📋 Listar todas las ventas
# ===========================

@router.get("/list")
async def list_sales():
    ventas = []
    cursor = db["sales"].find()

    async for venta in cursor:
        producto = await db["products"].find_one({"code": venta["product_id"]})
        ventas.append({
            "id": str(venta["_id"]),
            "product_id": venta["product_id"],
            "product_code": venta["product_id"],
            "name": producto["name"] if producto else "Desconocido",
            "quantity": venta["quantity"],
            "price": venta["price"]
        })

    return ventas

# ========================================
# ❌ Eliminar una venta y revertir el stock
# ========================================

@router.delete("/{sale_id}")
async def delete_sale(sale_id: str):
    venta = await db["sales"].find_one({"_id": ObjectId(sale_id)})
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    producto = await db["products"].find_one({"code": venta["product_id"]})
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    await db["sales"].delete_one({"_id": ObjectId(sale_id)})

    await db["products"].update_one(
        {"code": venta["product_id"]},
        {"$inc": {"stock": venta["quantity"]}}
    )

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
    if updated.quantity <= 0:
        raise HTTPException(status_code=400, detail="Cantidad inválida")
    if updated.price < 0:
        raise HTTPException(status_code=400, detail="Precio inválido")

    venta = await db["sales"].find_one({"_id": ObjectId(sale_id)})
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    producto = await db["products"].find_one({"code": updated.product_id})
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    diferencia = updated.quantity - venta["quantity"]

    if diferencia > 0 and producto.get("stock", 0) < diferencia:
        raise HTTPException(status_code=400, detail="Stock insuficiente para editar")

    await db["sales"].update_one(
        {"_id": ObjectId(sale_id)},
        {"$set": updated.dict()}
    )

    await db["products"].update_one(
        {"code": updated.product_id},
        {"$inc": {"stock": -diferencia}}
    )

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

@router.get("/search/")
async def search_sales(query: str = ""):
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
        {"$sort": {"date": -1}}
    ]

    cursor = db["stock_history"].aggregate(pipeline)
    historial = []

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
