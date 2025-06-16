from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.database import get_database  # Importación corregida
import time
import logging
from bson import ObjectId

# Configurar logger
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)
router = APIRouter()

# -------------------------------
# 🧱 Modelo Pydantic
# -------------------------------
class Product(BaseModel):
    id: Optional[str] = None
    name: str
    code: str
    price: float
    stock: int = 0
    description: Optional[str] = None

# -------------------------------
# ✅ Crear un nuevo producto
# -------------------------------
@router.post("/", summary="Crear un nuevo producto")
async def create_product(product: Product):
    logger.info(f"Creando nuevo producto: {product.code}")
    start_time = time.time()
    
    try:
        logger.debug("Obteniendo instancia de base de datos...")
        db = get_database()
        
        if not db:
            logger.error("La instancia de base de datos no está disponible")
            raise HTTPException(status_code=500, detail="No hay conexión a la base de datos")
        
        logger.debug(f"Verificando existencia de producto con código: {product.code}")
        existing = await db.products.find_one({"code": product.code})
        
        if existing:
            logger.warning(f"El código de producto ya existe: {product.code}")
            raise HTTPException(status_code=400, detail="El código del producto ya existe")
        
        logger.debug("Preparando datos para inserción...")
        product_data = product.dict()
        if product_data.get("id"):
            del product_data["id"]
            
        logger.debug("Insertando producto en la base de datos...")
        result = await db.products.insert_one(product_data)
        
        logger.debug(f"Buscando producto insertado con ID: {result.inserted_id}")
        new_product = await db.products.find_one({"_id": result.inserted_id})
        
        logger.debug("Procesando resultado...")
        new_product["id"] = str(new_product["_id"])
        del new_product["_id"]
        
        if "description" not in new_product or new_product["description"] is None:
            new_product["description"] = ""
        
        elapsed = time.time() - start_time
        logger.info(f"Producto creado exitosamente en {elapsed:.2f} segundos")
        return new_product
        
    except HTTPException as he:
        logger.error(f"Error HTTP: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Error inesperado al crear producto: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# -------------------------------
# 📋 Listar todos los productos
# -------------------------------
@router.get("/", summary="Listar todos los productos")
async def list_products():
    logger.info("Iniciando listado de productos")
    start_time = time.time()
    
    try:
        logger.debug("Obteniendo instancia de base de datos...")
        db = get_database()
        
        if not db:
            logger.error("La instancia de base de datos no está disponible")
            raise HTTPException(status_code=500, detail="No hay conexión a la base de datos")
        
        logger.debug("Buscando productos...")
        products_cursor = db.products.find()
        products = []
        
        async for product in products_cursor:
            product["id"] = str(product["_id"])
            del product["_id"]
            
            if "description" not in product or product["description"] is None:
                product["description"] = ""
            
            products.append(product)
        
        elapsed = time.time() - start_time
        logger.info(f"Listado completado exitosamente. Productos encontrados: {len(products)}")
        return products
        
    except Exception as e:
        logger.exception(f"Error inesperado al listar productos: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# -------------------------------
# 🔍 Buscar productos por nombre o descripción
# -------------------------------
@router.get("/search/", summary="Buscar productos por texto")
async def search_products(query: str):
    logger.info(f"Iniciando búsqueda con término: '{query}'")
    start_time = time.time()
    
    try:
        logger.debug("Obteniendo instancia de base de datos...")
        db = get_database()
        
        if not db:
            logger.error("La instancia de base de datos no está disponible")
            raise HTTPException(status_code=500, detail="No hay conexión a la base de datos")
        
        logger.debug("Construyendo filtro de búsqueda...")
        filtro = {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
            ]
        }

        logger.debug("Ejecutando búsqueda...")
        cursor = db.products.find(filtro)
        results = []
        
        async for product in cursor:
            product["id"] = str(product["_id"])
            del product["_id"]
            
            if "description" not in product or product["description"] is None:
                product["description"] = ""
            
            results.append(product)
        
        elapsed = time.time() - start_time
        logger.info(f"Búsqueda completada. Resultados encontrados: {len(results)}")
        return results
        
    except Exception as e:
        logger.exception(f"Error inesperado al buscar productos: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

# -------------------------------
# 🔍 Obtener producto por código
# -------------------------------
@router.get("/{product_code}", response_model=Product)
async def get_product_by_code(product_code: str):
    logger.info(f"Iniciando búsqueda de producto por código: '{product_code}'")
    start_time = time.time()
    
    try:
        logger.debug("Obteniendo instancia de base de datos...")
        db = get_database()
        
        if not db:
            logger.error("La instancia de base de datos no está disponible")
            raise HTTPException(status_code=500, detail="No hay conexión a la base de datos")
        
        # Paso 1: Verificar si la colección existe
        logger.debug("Verificando existencia de colección 'products'...")
        collection_names = await db.list_collection_names()
        
        if "products" not in collection_names:
            logger.error("La colección 'products' no existe en la base de datos")
            raise HTTPException(status_code=500, detail="La colección de productos no existe")
        
        # Paso 2: Operación de conteo (diagnóstico)
        logger.debug("Realizando conteo de documentos...")
        count_start = time.time()
        count = await db.products.count_documents({})
        count_time = time.time() - count_start
        logger.info(f"Conteo de productos completado. Total: {count}, Tiempo: {count_time:.2f}s")
        
        # Paso 3: Búsqueda específica
        logger.debug(f"Buscando producto con código: {product_code}")
        find_start = time.time()
        product = await db.products.find_one({"code": product_code})
        find_time = time.time() - find_start
        
        if not product:
            logger.warning(f"Producto no encontrado: {product_code}")
            
            # Obtener códigos existentes para diagnóstico
            try:
                codes = []
                async for p in db.products.find({}, {"code": 1}):
                    codes.append(p["code"])
                logger.info(f"Códigos existentes en la base de datos: {', '.join(codes)}")
            except Exception as e:
                logger.error(f"Error al obtener códigos existentes: {str(e)}")
            
            raise HTTPException(status_code=404, detail=f"Producto no encontrado. Código: {product_code}")
        
        logger.info(f"Búsqueda específica completada. Tiempo: {find_time:.2f}s")
        
        # Paso 4: Procesar resultado
        logger.debug("Procesando resultado...")
        product["id"] = str(product["_id"])
        del product["_id"]
        
        if "description" not in product or product["description"] is None:
            product["description"] = ""
        
        elapsed = time.time() - start_time
        logger.info(f"Producto encontrado exitosamente en {elapsed:.2f} segundos")
        return product
        
    except HTTPException as he:
        logger.error(f"Error controlado: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Error inesperado al buscar producto: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")