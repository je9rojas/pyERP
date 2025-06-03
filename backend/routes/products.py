from fastapi import APIRouter, HTTPException
from backend.models.product import Product
from backend.crud import products as crud
from pydantic import BaseModel
from bson import ObjectId
from backend.database import db

router = APIRouter()

@router.post("/", summary="Crear un nuevo producto")
async def create(product: Product):
    return await crud.create_product(product)

@router.get("/", summary="Listar todos los productos")
async def list_all():
    return await crud.list_products()

# Nuevo: buscar por nombre o descripción
@router.get("/search/")
async def search_products(query: str):
    filtro = {"$or": [
        {"name": {"$regex": query, "$options": "i"}},
        {"description": {"$regex": query, "$options": "i"}},
    ]}
    cursor = db["products"].find(filtro)
    products = []
    async for p in cursor:
        p["id"] = str(p["_id"])
        del p["_id"]
        products.append(p)
    return products
