###############################
# 📁 backend/routes/products.py
###############################

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from bson import ObjectId
from backend.models.product import Product
from backend.crud import products as crud
from backend.database import db

router = APIRouter()

# -------------------------------
# ✅ Crear un nuevo producto
# -------------------------------
@router.post("/", summary="Crear un nuevo producto")
async def create_product(product: Product):
    return await crud.create_product(product)

# -------------------------------
# 📋 Listar todos los productos
# -------------------------------
@router.get("/", summary="Listar todos los productos")
async def list_products():
    return await crud.list_products()

# -------------------------------
# 🔍 Buscar productos por nombre o descripción
# -------------------------------
@router.get("/search/", summary="Buscar productos por texto")
async def search_products(query: str):
    filtro = {
        "$or": [
            {"name": {"$regex": query, "$options": "i"}},
            {"description": {"$regex": query, "$options": "i"}},
        ]
    }

    cursor = db["products"].find(filtro)
    results = []
    async for product in cursor:
        product["id"] = str(product["_id"])
        del product["_id"]
        results.append(product)

    return results
