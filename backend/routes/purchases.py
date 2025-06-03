from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from backend.database import db
from bson import ObjectId

router = APIRouter()

# Modelo para crear una compra
class PurchaseCreate(BaseModel):
    product_id: str
    quantity: int
    price: float

# Modelo para devolver una compra con ID
class PurchaseOut(PurchaseCreate):
    id: str

@router.get("/")
async def test_purchases():
    return {"message": "Purchases route works"}

@router.post("/")
async def create_purchase(purchase: PurchaseCreate = Body(...)):
    if purchase.quantity <= 0:
        raise HTTPException(status_code=400, detail="Cantidad inválida")
    if purchase.price < 0:
        raise HTTPException(status_code=400, detail="Precio inválido")

    result = await db["purchases"].insert_one(purchase.dict())
    return {
        "message": "Compra registrada con éxito",
        "id": str(result.inserted_id),
        "purchase": purchase.dict()
    }

@router.get("/list", response_model=list[PurchaseOut])
async def list_purchases():
    purchases_cursor = db["purchases"].find()
    purchases = []
    async for purchase in purchases_cursor:
        purchase["id"] = str(purchase["_id"])
        del purchase["_id"]
        purchases.append(purchase)
    return purchases

@router.delete("/{purchase_id}")
async def delete_purchase(purchase_id: str):
    result = await db["purchases"].delete_one({"_id": ObjectId(purchase_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Compra no encontrada")
    return {"message": "Compra eliminada"}

@router.put("/{purchase_id}")
async def update_purchase(purchase_id: str, updated: PurchaseCreate):
    result = await db["purchases"].update_one(
        {"_id": ObjectId(purchase_id)},
        {"$set": updated.dict()}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Compra no encontrada o sin cambios")
    return {"message": "Compra actualizada con éxito"}

@router.get("/search/")
async def search_purchases(query: str = ""):
    filtro = {"$or": [
        {"product_id": {"$regex": query, "$options": "i"}},
    ]}
    cursor = db["purchases"].find(filtro)
    results = []
    async for item in cursor:
        item["id"] = str(item["_id"])
        del item["_id"]
        results.append(item)
    return results
