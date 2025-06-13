# backend/routes/purchases.py
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from backend.database import db
from bson import ObjectId
from typing import List

router = APIRouter()  # Eliminado el prefix aquí

# -------------------------------
# 📅 Modelos
# -------------------------------
class PurchaseCreate(BaseModel):
    product_id: str  # Este es el código del producto, como 'AP001'
    quantity: int
    price: float

class PurchaseOut(PurchaseCreate):
    id: str

# -------------------------------
# 🔄 Ruta de prueba
# -------------------------------
@router.get("/test")
async def test_purchases():
    return {"message": "Purchases route works"}

# -------------------------------
# ✅ Crear compra
# -------------------------------
@router.post("/", response_model=dict)
async def create_purchase(purchase: PurchaseCreate = Body(...)):
    if purchase.quantity <= 0:
        raise HTTPException(status_code=400, detail="Cantidad inválida")
    if purchase.price < 0:
        raise HTTPException(status_code=400, detail="Precio inválido")

    # Verificar que el producto existe
    product = await db["products"].find_one({"code": purchase.product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Insertar en compras
    result = await db["purchases"].insert_one(purchase.dict())

    # Actualizar stock
    await db["products"].update_one(
        {"code": purchase.product_id},
        {"$inc": {"stock": purchase.quantity}}
    )

    # Registrar historial
    await db["stock_history"].insert_one({
        "product_id": purchase.product_id,
        "type": "purchase",
        "quantity": purchase.quantity,
        "price": purchase.price
    })

    return {
        "message": "Compra registrada con éxito",
        "id": str(result.inserted_id),
        "purchase": purchase.dict()
    }

# -------------------------------
# 📋 Listar compras
# -------------------------------
@router.get("/list", response_model=List[PurchaseOut])
async def list_purchases():
    purchases_cursor = db["purchases"].find()
    purchases = []
    async for purchase in purchases_cursor:
        purchase["id"] = str(purchase["_id"])
        del purchase["_id"]
        purchases.append(purchase)
    return purchases

# -------------------------------
# ❌ Eliminar compra
# -------------------------------
@router.delete("/{purchase_id}")
async def delete_purchase(purchase_id: str):
    compra = await db["purchases"].find_one({"_id": ObjectId(purchase_id)})
    if not compra:
        raise HTTPException(status_code=404, detail="Compra no encontrada")

    # Revertir stock del producto
    await db["products"].update_one(
        {"code": compra["product_id"]},
        {"$inc": {"stock": -compra["quantity"]}}
    )

    # Eliminar compra
    await db["purchases"].delete_one({"_id": ObjectId(purchase_id)})

    return {"message": "Compra eliminada"}

# -------------------------------
# ✏️ Editar compra
# -------------------------------
@router.put("/{purchase_id}")
async def update_purchase(purchase_id: str, updated: PurchaseCreate):
    original = await db["purchases"].find_one({"_id": ObjectId(purchase_id)})
    if not original:
        raise HTTPException(status_code=404, detail="Compra no encontrada")

    diff = updated.quantity - original["quantity"]

    # Verificar que el producto existe
    product = await db["products"].find_one({"code": updated.product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Actualizar stock
    await db["products"].update_one(
        {"code": updated.product_id},
        {"$inc": {"stock": diff}}
    )

    # Actualizar compra
    result = await db["purchases"].update_one(
        {"_id": ObjectId(purchase_id)},
        {"$set": updated.dict()}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Sin cambios")

    # Registrar historial
    await db["stock_history"].insert_one({
        "product_id": updated.product_id,
        "type": "purchase_edit",
        "quantity": diff,
        "price": updated.price
    })

    return {"message": "Compra actualizada con éxito"}

# -------------------------------
# 🔍 Buscar compras
# -------------------------------
@router.get("/search")
async def search_purchases(query: str = ""):
    filtro = {"product_id": {"$regex": query, "$options": "i"}}
    cursor = db["purchases"].find(filtro)
    results = []
    async for item in cursor:
        item["id"] = str(item["_id"])
        del item["_id"]
        results.append(item)
    return results