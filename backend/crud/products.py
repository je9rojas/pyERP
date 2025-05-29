from backend.database import db
from backend.models.product import Product
from bson import ObjectId

collection = db["products"]

async def create_product(product: Product) -> dict:
    result = await collection.insert_one(product.dict())
    return {**product.dict(), "_id": str(result.inserted_id)}

async def list_products() -> list:
    products = []
    async for prod in collection.find():
        prod["_id"] = str(prod["_id"])
        products.append(prod)
    return products
