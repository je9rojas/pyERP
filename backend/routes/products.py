from fastapi import APIRouter
from backend.models.product import Product
from backend.crud import products as crud

router = APIRouter()

@router.post("/", summary="Crear un nuevo producto")
async def create(product: Product):
    return await crud.create_product(product)

@router.get("/", summary="Listar todos los productos")
async def list_all():
    return await crud.list_products()
