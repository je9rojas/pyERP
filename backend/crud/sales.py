# backend/crud/sales.py
from backend.database import db
from backend.models.sale import Sale
from bson import ObjectId

async def register_sale(sale: Sale):
    # Actualizar stock por cada item vendido
    for item in sale.items:
        await db.products.update_one(
            {"_id": ObjectId(item.product_id)},
            {"$inc": {"stock": -item.quantity}}
        )
    # Guardar la venta
    result = await db.sales.insert_one(sale.dict())
    return str(result.inserted_id)
