from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.database import get_database, is_database_connected
import logging

# Configurar logger
logger = logging.getLogger("uvicorn")
router = APIRouter()

# -------------------------------
# 🧱 Modelo Pydantic
# -------------------------------
class Product(BaseModel):
    id: Optional[str] = None
    name: str
    code: str
    price: float
    stock: int
    description: Optional[str] = None

# -------------------------------
# ✅ Crear un nuevo producto
# -------------------------------
@router.post("/")
async def create_product(product: Product):
    try:
        logger.info(f"Creando nuevo producto: {product.code}")
        db = get_database()
        
        if not is_database_connected():
            raise Exception("No hay conexión a la base de datos")
        
        # Verificar si el código ya existe
        existing = await db.products.find_one({"code": product.code})
        if existing:
            raise HTTPException(status_code=400, detail="El código del producto ya existe")
        
        # Insertar en la base de datos
        product_data = product.dict(exclude={"id"})
        result = await db.products.insert_one(product_data)
        
        # Obtener y retornar el producto creado
        new_product = await db.products.find_one({"_id": result.inserted_id})
        new_product["id"] = str(new_product["_id"])
        new_product.pop("_id", None)
        
        # Asegurar valor para description
        if "description" not in new_product or new_product["description"] is None:
            new_product["description"] = ""
        
        return new_product
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error inesperado al crear producto: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# -------------------------------
# 📋 Listar todos los productos
# -------------------------------
@router.get("/")
async def list_products():
    try:
        logger.info("Listando todos los productos")
        db = get_database()
        
        if not is_database_connected():
            raise Exception("No hay conexión a la base de datos")
        
        products_cursor = db.products.find()
        products = []
        
        async for product in products_cursor:
            product["id"] = str(product["_id"])
            product.pop("_id", None)
            
            if "description" not in product or product["description"] is None:
                product["description"] = ""
            
            products.append(product)
        
        return products
        
    except Exception as e:
        logger.error(f"Error inesperado al listar productos: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# -------------------------------
# 🔍 Buscar productos por nombre o descripción
# -------------------------------
@router.get("/search/")
async def search_products(query: str):
    try:
        logger.info(f"Buscando productos con: '{query}'")
        db = get_database()
        
        if not is_database_connected():
            raise Exception("No hay conexión a la base de datos")
        
        filtro = {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
            ]
        }

        cursor = db.products.find(filtro)
        results = []
        
        async for product in cursor:
            product["id"] = str(product["_id"])
            product.pop("_id", None)
            
            if "description" not in product or product["description"] is None:
                product["description"] = ""
            
            results.append(product)
        
        return results
        
    except Exception as e:
        logger.error(f"Error inesperado al buscar productos: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# -------------------------------
# 🔍 Obtener producto por código (Versión optimizada)
# -------------------------------
@router.get("/{product_code}")
async def get_product_by_code(product_code: str):
    try:
        logger.info(f"Buscando producto: {product_code}")
        db = get_database()
        
        if not is_database_connected():
            raise Exception("No hay conexión a la base de datos")
        
        # Buscar el producto directamente
        product = await db.products.find_one({"code": product_code})
        
        if not product:
            logger.warning(f"Producto no encontrado: {product_code}")
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        # Crear un diccionario compatible con Pydantic
        response_data = {
            "id": str(product["_id"]),
            "name": product["name"],
            "code": product["code"],
            "price": float(product["price"]),
            "stock": int(product["stock"]),
            "description": product.get("description", "") or ""
        }
        
        logger.info(f"Producto encontrado: {response_data['code']}")
        return response_data
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error crítico: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")