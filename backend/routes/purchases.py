# backend/routes/purchases.py
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from backend.database import get_database
from bson import ObjectId
from typing import List
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# -------------------------------
# 📅 Modelos
# -------------------------------
class PurchaseCreate(BaseModel):
    product_id: str
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
    db = get_database()
    if db is None:  # Corregido: verificar explícitamente contra None
        raise HTTPException(status_code=500, detail="Database not available")
    
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
# 📋 Listar compras (FIXED)
# -------------------------------
@router.get("/list", response_model=List[PurchaseOut])
async def list_purchases():
    try:
        db = get_database()
        if db is None:  # Corregido: verificar explícitamente contra None
            raise HTTPException(status_code=500, detail="Database not available")
        
        purchases_cursor = db["purchases"].find()
        purchases = []
        async for purchase in purchases_cursor:
            if purchase is None:
                logger.warning("Documento nulo encontrado")
                continue
                
            if "_id" not in purchase:
                logger.error(f"Documento sin _id: {purchase}")
                continue
                
            purchase_data = dict(purchase)
            purchase_data["id"] = str(purchase_data["_id"])
            del purchase_data["_id"]
            purchases.append(purchase_data)
        return purchases
    except Exception as e:
        logger.exception(f"Error crítico al listar compras: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )

# -------------------------------
# ❌ Eliminar compra
# -------------------------------
@router.delete("/{purchase_id}")
async def delete_purchase(purchase_id: str):
    db = get_database()
    if db is None:  # Corregido: verificar explícitamente contra None
        raise HTTPException(status_code=500, detail="Database not available")
    
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
    db = get_database()
    if db is None:  # Corregido: verificar explícitamente contra None
        raise HTTPException(status_code=500, detail="Database not available")
    
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
# 🔍 Buscar compras (FIXED)
# -------------------------------
@router.get("/search")
async def search_purchases(query: str = ""):
    try:
        db = get_database()
        if db is None:  # Corregido: verificar explícitamente contra None
            raise HTTPException(status_code=500, detail="Database not available")
        
        filtro = {"product_id": {"$regex": query, "$options": "i"}}
        cursor = db["purchases"].find(filtro)
        results = []
        async for item in cursor:
            if item is None:
                continue
                
            if "_id" in item:
                item_data = dict(item)
                item_data["id"] = str(item_data["_id"])
                del item_data["_id"]
                results.append(item_data)
        return results
    except Exception as e:
        logger.exception(f"Error en búsqueda de compras: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error en búsqueda: {str(e)}"
        )