# backend/routes/sales.py

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from backend.database import db
from bson import ObjectId

router = APIRouter()

# -------------------------------
# 📦 Modelos de datos (Pydantic)
# -------------------------------

class SaleCreate(BaseModel):
    product_id: str
    quantity: int
    price: float

class SaleOut(SaleCreate):
    id: str

# -------------------------------
# 🔁 Ruta de prueba
# -------------------------------

@router.get("/")
async def test_sales():
    return {"message": "Ruta de ventas funcionando correctamente"}

# -------------------------------
# ✅ Crear nueva venta
# -------------------------------

@router.post("/")
async def create_sale(sale: SaleCreate = Body(...)):
    if sale.quantity <= 0:
        raise HTTPException(status_code=400, detail="Cantidad inválida")
    if sale.price < 0:
        raise HTTPException(status_code=400, detail="Precio inválido")

    result = await db["sales"].insert_one(sale.dict())
    return {
        "message": "Venta registrada con éxito",
        "id": str(result.inserted_id),
        "sale": sale.dict()
    }

# -------------------------------
# 📋 Listar todas las ventas
# -------------------------------

@router.get("/list", response_model=list[SaleOut])
async def list_sales():
    sales_cursor = db["sales"].find()
    sales = []
    async for sale in sales_cursor:
        sale["id"] = str(sale["_id"])
        del sale["_id"]
        sales.append(sale)
    return sales

# -------------------------------
# ❌ Eliminar una venta por ID
# -------------------------------

@router.delete("/{sale_id}")
async def delete_sale(sale_id: str):
    result = await db["sales"].delete_one({"_id": ObjectId(sale_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return {"message": "Venta eliminada correctamente"}

# -------------------------------
# ✏️ Actualizar una venta por ID
# -------------------------------

@router.put("/{sale_id}")
async def update_sale(sale_id: str, updated: SaleCreate):
    result = await db["sales"].update_one(
        {"_id": ObjectId(sale_id)},
        {"$set": updated.dict()}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Venta no encontrada o sin cambios")
    return {"message": "Venta actualizada con éxito"}

# -------------------------------
# 🔍 Buscar ventas por texto (product_id)
# -------------------------------

@router.get("/search/")
async def search_sales(query: str = ""):
    filtro = {"product_id": {"$regex": query, "$options": "i"}}
    cursor = db["sales"].find(filtro)
    results = []
    async for item in cursor:
        item["id"] = str(item["_id"])
        del item["_id"]
        results.append(item)
    return results
