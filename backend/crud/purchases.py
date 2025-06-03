# backend/crud/purchases.py
from backend.database import db
from backend.models.purchase import Purchase
from bson import ObjectId

async def register_purchase(purchase: Purchase):
    # Actualizar stock por cada item comprado
    for item in purchase.items:
        await db.products.update_one(
            {"_id": ObjectId(item.product_id)},
            {"$inc": {"stock": item.quantity}}
        )
    # Guardar la compra
    result = await db.purchases.insert_one(purchase.dict())
    return str(result.inserted_id)