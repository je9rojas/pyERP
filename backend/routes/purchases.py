# 📁 backend/routes/purchases.py
from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel
from backend.database import get_database
from bson import ObjectId
from datetime import datetime, timedelta
from typing import List, Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# ======================================
# 🧾 Modelos de datos (entrada y salida)
# ======================================

class PurchaseItem(BaseModel):
    product_id: str
    quantity: int
    price: float

class PurchaseCreate(BaseModel):
    supplier: str
    items: List[PurchaseItem]
    total: float

class PurchaseOut(PurchaseCreate):
    id: str
    date: datetime

# ===========================
# 🔁 Ruta de prueba
# ===========================

@router.get("/")
async def test_purchases():
    return {"message": "✅ Ruta de compras funcionando correctamente"}

# ===========================
# ✅ Crear una nueva compra
# ===========================

@router.post("/", response_model=PurchaseOut)
async def create_purchase(purchase: PurchaseCreate = Body(...)):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no disponible")
    
    # Validar cada ítem
    for item in purchase.items:
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail=f"Cantidad inválida para el producto {item.product_id}")
        if item.price < 0:
            raise HTTPException(status_code=400, detail=f"Precio inválido para el producto {item.product_id}")

        # Buscar el producto
        product = await db["products"].find_one({"code": item.product_id})
        if not product:
            raise HTTPException(status_code=404, detail=f"Producto {item.product_id} no encontrado")

    # Crear documento de compra
    purchase_data = purchase.dict()
    purchase_data["date"] = datetime.utcnow()
    
    # Insertar en la colección 'purchases'
    result = await db["purchases"].insert_one(purchase_data)
    
    if not result.inserted_id:
        logger.error("Fallo al insertar compra, sin ID retornado")
        raise HTTPException(status_code=500, detail="Error al crear la compra")

    # Actualizar stock para cada producto
    for item in purchase.items:
        # Actualizar stock del producto
        await db["products"].update_one(
            {"code": item.product_id},
            {"$inc": {"stock": item.quantity}}
        )

        # Registrar en historial
        await db["stock_history"].insert_one({
            "product_id": item.product_id,
            "change": item.quantity,
            "reason": "compra",
            "date": datetime.utcnow()
        })

    # Obtener la compra recién creada para devolverla
    new_purchase = await db["purchases"].find_one({"_id": result.inserted_id})
    if not new_purchase:
        logger.error(f"Compra creada pero no encontrada: {result.inserted_id}")
        raise HTTPException(status_code=500, detail="Compra creada pero no encontrada")
    
    # Convertir ObjectId a string
    new_purchase["id"] = str(new_purchase["_id"])
    new_purchase.pop("_id", None)
    
    return new_purchase

# ========================================
# ❌ Eliminar una compra y revertir el stock
# ========================================

@router.delete("/{purchase_id}")
async def delete_purchase(purchase_id: str):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no disponible")
    
    try:
        object_id = ObjectId(purchase_id)
    except:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    compra = await db["purchases"].find_one({"_id": object_id})
    if not compra:
        raise HTTPException(status_code=404, detail="Compra no encontrada")

    # Revertir stock para cada ítem
    items = compra.get("items", [])
    for item in items:
        product_id = item.get("product_id")
        quantity = item.get("quantity", 0)
        
        if product_id and quantity > 0:
            # Revertir stock
            await db["products"].update_one(
                {"code": product_id},
                {"$inc": {"stock": -quantity}}
            )

            # Registrar en historial
            await db["stock_history"].insert_one({
                "product_id": product_id,
                "change": -quantity,
                "reason": "reversión compra",
                "date": datetime.utcnow()
            })

    # Eliminar compra
    delete_result = await db["purchases"].delete_one({"_id": object_id})
    
    if delete_result.deleted_count == 0:
        logger.error(f"Error al eliminar compra: {purchase_id}")
        raise HTTPException(status_code=500, detail="Error al eliminar la compra")

    return {"message": "✅ Compra eliminada correctamente"}

# ====================================
# 🔍 Buscar compras con paginación y filtros (OPTIMIZADO)
# ====================================

@router.get("/search")
async def search_purchases(
    proveedor: Optional[str] = Query(None),
    producto: Optional[str] = Query(None),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100)
):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no disponible")
    
    # Construir el filtro
    filtro = {}
    
    if proveedor:
        filtro["supplier"] = {"$regex": proveedor, "$options": "i"}
    
    if producto:
        # Buscar por código de producto en los items
        filtro["items.product_id"] = {"$regex": producto, "$options": "i"}
    
    if fecha_inicio and fecha_fin:
        try:
            # Convertir fechas a datetime
            start_date = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            end_date = datetime.strptime(fecha_fin, "%Y-%m-%d") + timedelta(days=1)  # Incluir todo el día final
            filtro["date"] = {"$gte": start_date, "$lte": end_date}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Formato de fecha inválido: {str(e)}")
    
    # Solo contar y buscar si hay filtros aplicados
    if not filtro:
        return {
            "compras": [],
            "total": 0,
            "page": page,
            "per_page": per_page,
            "total_pages": 0
        }
    
    # Contar total de documentos que coinciden
    total = await db["purchases"].count_documents(filtro)
    
    # Calcular el número de páginas
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0
    
    # Obtener las compras con paginación
    skip = (page - 1) * per_page
    cursor = db["purchases"].find(filtro).sort("date", -1).skip(skip).limit(per_page)
    
    resultados = []
    async for compra in cursor:
        # Convertir ObjectId a string
        compra["id"] = str(compra["_id"])
        compra.pop("_id", None)
        
        # Obtener nombres de productos para cada ítem
        items = compra.get("items", [])
        for item in items:
            product_id = item.get("product_id")
            if product_id:
                producto = await db["products"].find_one({"code": product_id})
                item["product_name"] = producto["name"] if producto else "Desconocido"
            else:
                item["product_name"] = "Desconocido"
        
        compra["items"] = items
        resultados.append(compra)

    return {
        "compras": resultados,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }

# ====================================
# 🔍 Obtener detalles de una compra por ID
# ====================================

@router.get("/{purchase_id}")
async def get_purchase_details(purchase_id: str):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no disponible")
    
    try:
        object_id = ObjectId(purchase_id)
    except:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    compra = await db["purchases"].find_one({"_id": object_id})
    if not compra:
        raise HTTPException(status_code=404, detail="Compra no encontrada")
    
    # Convertir ObjectId a string
    compra["id"] = str(compra["_id"])
    compra.pop("_id", None)
    
    # Obtener nombres de productos para cada ítem
    items = compra.get("items", [])
    for item in items:
        product_id = item.get("product_id")
        if product_id:
            producto = await db["products"].find_one({"code": product_id})
            item["product_name"] = producto["name"] if producto else "Desconocido"
    
    return compra

# ==================================================
# 📜 Ver historial de stock (opcional, no crítico)
# ==================================================

@router.get("/stock-history")
async def ver_historial(page: int = Query(1, ge=1), per_page: int = Query(10, ge=1, le=50)):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no disponible")
    
    skip = (page - 1) * per_page
    
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
        {"$skip": skip},
        {"$limit": per_page},
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