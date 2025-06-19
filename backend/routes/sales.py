# 📁 backend/routes/sales.py

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
# 🔍 Buscar ventas con paginación y filtros (OPTIMIZADO)
# ====================================

@router.get("/search")
async def search_sales(
    cliente: Optional[str] = Query(None),
    producto: Optional[str] = Query(None),
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100)
):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no disponible")
    
    # Construir el filtro solo si se proporcionan parámetros
    filtro = {}
    
    if cliente:
        filtro["client"] = {"$regex": cliente, "$options": "i"}
    
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
            "ventas": [],
            "total": 0,
            "page": page,
            "per_page": per_page,
            "total_pages": 0
        }
    
    # Contar total de documentos que coinciden
    total = await db["sales"].count_documents(filtro)
    
    # Calcular el número de páginas
    total_pages = (total + per_page - 1) // per_page if total > 0 else 0
    
    # Obtener las ventas con paginación
    skip = (page - 1) * per_page
    cursor = db["sales"].find(filtro).sort("date", -1).skip(skip).limit(per_page)
    
    resultados = []
    async for venta in cursor:
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
            else:
                item["product_name"] = "Desconocido"
        
        venta["items"] = items
        resultados.append(venta)

    return {
        "ventas": resultados,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }

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