from backend.database import db
from backend.models.product import Product
from bson import ObjectId

async def create_product(product: Product):
    result = await db["products"].insert_one(product.dict())
    return {"id": str(result.inserted_id)}

async def list_products():
    cursor = db["products"].find()
    products = []
    async for p in cursor:
        p["id"] = str(p["_id"])
        del p["_id"]
        products.append(p)
    return products
