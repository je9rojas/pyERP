# 📁 backend/routes/sales.py

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from backend.database import get_database
from bson import ObjectId
from datetime import datetime
from typing import List
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# ======================================
# 🧾 Modelos de datos (entrada y salida)
# ======================================

class SaleItem(BaseModel):
    product_id: str
    quantity: int
    price: float

class SaleCreate(BaseModel):
    client: str = "Consumidor final"
    items: List[SaleItem]
    total: float

class SaleOut(SaleCreate):
    id: str
    date: datetime

# ===========================
# 🔁 Ruta de prueba
# ===========================

@router.get("/")
async def test_sales():
    return {"message": "✅ Ruta de ventas funcionando correctamente"}

# ===========================
# ✅ Crear una nueva venta
# ===========================

@router.post("/", response_model=SaleOut)
async def create_sale(sale: SaleCreate = Body(...)):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no disponible")
    
    # Validar cada ítem
    for item in sale.items:
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail=f"Cantidad inválida para el producto {item.product_id}")
        if item.price < 0:
            raise HTTPException(status_code=400, detail=f"Precio inválido para el producto {item.product_id}")

        # Buscar el producto
        product = await db["products"].find_one({"code": item.product_id})
        if not product:
            raise HTTPException(status_code=404, detail=f"Producto {item.product_id} no encontrado")
        
        # Verificar stock
        if "stock" not in product or product["stock"] < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para {item.product_id}. Disponible: {product.get('stock', 0)}"
            )

    # Crear documento de venta
    sale_data = sale.dict()
    sale_data["date"] = datetime.utcnow()
    
    # Insertar en la colección 'sales'
    result = await db["sales"].insert_one(sale_data)
    
    if not result.inserted_id:
        logger.error("Fallo al insertar venta, sin ID retornado")
        raise HTTPException(status_code=500, detail="Error al crear la venta")

    # Actualizar stock para cada producto
    for item in sale.items:
        # Actualizar stock del producto
        await db["products"].update_one(
            {"code": item.product_id},
            {"$inc": {"stock": -item.quantity}}
        )

        # Registrar en historial
        await db["stock_history"].insert_one({
            "product_id": item.product_id,
            "change": -item.quantity,
            "reason": "venta",
            "date": datetime.utcnow()
        })

    # Obtener la venta recién creada para devolverla
    new_sale = await db["sales"].find_one({"_id": result.inserted_id})
    if not new_sale:
        logger.error(f"Venta creada pero no encontrada: {result.inserted_id}")
        raise HTTPException(status_code=500, detail="Venta creada pero no encontrada")
    
    # Convertir ObjectId a string
    new_sale["id"] = str(new_sale["_id"])
    new_sale.pop("_id", None)
    
    return new_sale

# ===========================
# 📋 Listar todas las ventas (CORREGIDO)
# ===========================

@router.get("/list")
async def list_sales():
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no disponible")
    
    ventas = []
    cursor = db["sales"].find().sort("date", -1)

    async for venta in cursor:
        # Manejar ventas sin items
        items = venta.get("items", [])
        
        # Convertir ObjectId a string
        venta["id"] = str(venta["_id"])
        venta.pop("_id", None)
        
        # Obtener nombres de productos para cada ítem
        for item in items:
            # Manejar items sin product_id
            product_id = item.get("product_id")
            if product_id:
                producto = await db["products"].find_one({"code": product_id})
                item["product_name"] = producto["name"] if producto else "Desconocido"
            else:
                item["product_name"] = "Desconocido"
        
        # Asegurar que la venta tenga la estructura correcta
        venta["items"] = items
        ventas.append(venta)

    return ventas

# ========================================
# ❌ Eliminar una venta y revertir el stock
# ========================================

@router.delete("/{sale_id}")
async def delete_sale(sale_id: str):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no disponible")
    
    try:
        object_id = ObjectId(sale_id)
    except:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    venta = await db["sales"].find_one({"_id": object_id})
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    # Revertir stock para cada ítem
    items = venta.get("items", [])
    for item in items:
        product_id = item.get("product_id")
        quantity = item.get("quantity", 0)
        
        if product_id and quantity > 0:
            # Revertir stock
            await db["products"].update_one(
                {"code": product_id},
                {"$inc": {"stock": quantity}}
            )

            # Registrar en historial
            await db["stock_history"].insert_one({
                "product_id": product_id,
                "change": quantity,
                "reason": "reversión venta",
                "date": datetime.utcnow()
            })

    # Eliminar venta
    delete_result = await db["sales"].delete_one({"_id": object_id})
    
    if delete_result.deleted_count == 0:
        logger.error(f"Error al eliminar venta: {sale_id}")
        raise HTTPException(status_code=500, detail="Error al eliminar la venta")

    return {"message": "✅ Venta eliminada correctamente"}

# ====================================
# ✏️ Actualizar una venta y el stock
# ====================================

@router.put("/{sale_id}", response_model=SaleOut)
async def update_sale(sale_id: str, updated: SaleCreate):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no disponible")
    
    try:
        object_id = ObjectId(sale_id)
    except:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    # Validar cada ítem
    for item in updated.items:
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail=f"Cantidad inválida para el producto {item.product_id}")
        if item.price < 0:
            raise HTTPException(status_code=400, detail=f"Precio inválido para el producto {item.product_id}")

    venta = await db["sales"].find_one({"_id": object_id})
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    # Calcular diferencias por producto
    diferencias = {}
    old_items = venta.get("items", [])
    
    for old_item in old_items:
        pid = old_item.get("product_id")
        if pid:
            diferencias[pid] = diferencias.get(pid, 0) - old_item.get("quantity", 0)
    
    for new_item in updated.items:
        pid = new_item.product_id
        diferencias[pid] = diferencias.get(pid, 0) + new_item.quantity
        
        # Verificar stock si se aumenta la cantidad
        if diferencias[pid] > 0:
            producto = await db["products"].find_one({"code": pid})
            if not producto:
                raise HTTPException(status_code=404, detail=f"Producto {pid} no encontrado")
            
            stock_actual = producto.get("stock", 0)
            if stock_actual < diferencias[pid]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Stock insuficiente para {pid}. Disponible: {stock_actual}"
                )

    # Actualizar venta
    updated_data = updated.dict()
    updated_data["date"] = venta.get("date", datetime.utcnow())
    
    await db["sales"].update_one(
        {"_id": object_id},
        {"$set": updated_data}
    )

    # Actualizar stock y registrar en historial
    for pid, diferencia in diferencias.items():
        if diferencia != 0:
            # Actualizar stock
            await db["products"].update_one(
                {"code": pid},
                {"$inc": {"stock": -diferencia}}
            )

            # Registrar en historial
            await db["stock_history"].insert_one({
                "product_id": pid,
                "change": -diferencia,
                "reason": "edición venta",
                "date": datetime.utcnow()
            })

    # Obtener la venta actualizada
    updated_sale = await db["sales"].find_one({"_id": object_id})
    updated_sale["id"] = str(updated_sale["_id"])
    updated_sale.pop("_id", None)
    
    return updated_sale

# ====================================
# 🔍 Buscar ventas por cliente o producto
# ====================================

@router.get("/search")
async def search_sales(query: str = ""):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no disponible")
    
    # Buscar por cliente, código de producto o nombre de producto
    filtro = {
        "$or": [
            {"client": {"$regex": query, "$options": "i"}},
            {"items.product_id": {"$regex": query, "$options": "i"}},
            {"items.product_name": {"$regex": query, "$options": "i"}}
        ]
    }
    
    cursor = db["sales"].find(filtro).sort("date", -1)
    resultados = []

    async for venta in cursor:
        # Convertir ObjectId a string
        venta["id"] = str(venta["_id"])
        venta.pop("_id", None)
        
        # Obtener nombres de productos
        items = venta.get("items", [])
        for item in items:
            product_id = item.get("product_id")
            if product_id:
                producto = await db["products"].find_one({"code": product_id})
                item["product_name"] = producto["name"] if producto else "Desconocido"
        
        venta["items"] = items
        resultados.append(venta)

    return resultados

# ==================================================
# 📜 Ver historial de stock
# ==================================================

@router.get("/stock-history")
async def ver_historial():
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no disponible")
    
    pipeline = [
        {
            "$lookup": {
                "from": "products",
                "localField": "product_id",
                "foreignField": "code",
                "as": "producto"
            }
        },
        {"$unwind": {"path": "$producto", "preserveNullAndEmptyArrays": True}},
        {"$sort": {"date": -1}},
        {"$limit": 100},
        {
            "$project": {
                "_id": 0,
                "id": {"$toString": "$_id"},
                "product_id": 1,
                "product_name": "$producto.name",
                "change": 1,
                "reason": 1,
                "date": 1
            }
        }
    ]

    historial = []
    cursor = db["stock_history"].aggregate(pipeline)
    
    async for movimiento in cursor:
        historial.append(movimiento)

    return historial

# ====================================
# 🔍 Obtener detalles de una venta por ID
# ====================================

@router.get("/{sale_id}")
async def get_sale_details(sale_id: str):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no disponible")
    
    try:
        object_id = ObjectId(sale_id)
    except:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    venta = await db["sales"].find_one({"_id": object_id})
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    
    # Convertir ObjectId a string
    venta["id"] = str(venta["_id"])
    venta.pop("_id", None)
    
    # Obtener nombres de productos para cada ítem
    items = venta.get("items", [])
    for item in items:
        product_id = item.get("product_id")
        if product_id:
            producto = await db["products"].find_one({"code": product_id})
            item["product_name"] = producto["name"] if producto else "Desconocido"
    
    return venta