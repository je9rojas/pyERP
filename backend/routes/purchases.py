# backend/routes/purchases.py
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

# ===========================
# 📋 Listar todas las compras
# ===========================

@router.get("/list")
async def list_purchases():
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no disponible")
    
    compras = []
    cursor = db["purchases"].find().sort("date", -1)

    async for compra in cursor:
        # Manejar compras sin items
        items = compra.get("items", [])
        
        # Convertir ObjectId a string
        compra["id"] = str(compra["_id"])
        compra.pop("_id", None)
        
        # Obtener nombres de productos para cada ítem
        for item in items:
            # Manejar items sin product_id
            product_id = item.get("product_id")
            if product_id:
                producto = await db["products"].find_one({"code": product_id})
                item["product_name"] = producto["name"] if producto else "Desconocido"
            else:
                item["product_name"] = "Desconocido"
        
        # Asegurar que la compra tenga la estructura correcta
        compra["items"] = items
        compras.append(compra)

    return compras

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
# ✏️ Actualizar una compra y el stock
# ====================================

@router.put("/{purchase_id}", response_model=PurchaseOut)
async def update_purchase(purchase_id: str, updated: PurchaseCreate):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no disponible")
    
    try:
        object_id = ObjectId(purchase_id)
    except:
        raise HTTPException(status_code=400, detail="ID inválido")
    
    # Validar cada ítem
    for item in updated.items:
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail=f"Cantidad inválida para el producto {item.product_id}")
        if item.price < 0:
            raise HTTPException(status_code=400, detail=f"Precio inválido para el producto {item.product_id}")

    compra = await db["purchases"].find_one({"_id": object_id})
    if not compra:
        raise HTTPException(status_code=404, detail="Compra no encontrada")

    # Calcular diferencias por producto
    diferencias = {}
    old_items = compra.get("items", [])
    
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

    # Actualizar compra
    updated_data = updated.dict()
    updated_data["date"] = compra.get("date", datetime.utcnow())
    
    await db["purchases"].update_one(
        {"_id": object_id},
        {"$set": updated_data}
    )

    # Actualizar stock y registrar en historial
    for pid, diferencia in diferencias.items():
        if diferencia != 0:
            # Actualizar stock
            await db["products"].update_one(
                {"code": pid},
                {"$inc": {"stock": diferencia}}
            )

            # Registrar en historial
            await db["stock_history"].insert_one({
                "product_id": pid,
                "change": diferencia,
                "reason": "edición compra",
                "date": datetime.utcnow()
            })

    # Obtener la compra actualizada
    updated_purchase = await db["purchases"].find_one({"_id": object_id})
    updated_purchase["id"] = str(updated_purchase["_id"])
    updated_purchase.pop("_id", None)
    
    return updated_purchase

# ====================================
# 🔍 Buscar compras por proveedor o producto
# ====================================

@router.get("/search")
async def search_purchases(query: str = ""):
    db = get_database()
    if db is None:
        raise HTTPException(status_code=500, detail="Base de datos no disponible")
    
    # Buscar por proveedor o ID de producto
    filtro = {
        "$or": [
            {"supplier": {"$regex": query, "$options": "i"}},
            {"items.product_id": {"$regex": query, "$options": "i"}},
            {"items.product_name": {"$regex": query, "$options": "i"}}
        ]
    }
    
    cursor = db["purchases"].find(filtro).sort("date", -1)
    resultados = []

    async for compra in cursor:
        # Convertir ObjectId a string
        compra["id"] = str(compra["_id"])
        compra.pop("_id", None)
        
        # Obtener nombres de productos
        items = compra.get("items", [])
        for item in items:
            product_id = item.get("product_id")
            if product_id:
                producto = await db["products"].find_one({"code": product_id})
                item["product_name"] = producto["name"] if producto else "Desconocido"
        
        compra["items"] = items
        resultados.append(compra)

    return resultados

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