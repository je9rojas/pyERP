from fastapi import APIRouter, Query
from pydantic import BaseModel
from backend.database import get_database
from datetime import datetime
from typing import List
import logging
import time

router = APIRouter()
logger = logging.getLogger(__name__)

# Cache para inventario
inventory_cache = None
cache_expire_time = 0
CACHE_TTL = 300  # 5 minutos en segundos

class InventoryItem(BaseModel):
    code: str
    name: str
    current_stock: int
    last_updated: datetime

class HistoryItem(BaseModel):
    date: datetime
    reason: str
    change: int

@router.get("/list", response_model=List[InventoryItem])
async def get_inventory():
    global inventory_cache, cache_expire_time
    
    # Usar caché si está vigente
    current_time = time.time()
    if inventory_cache and current_time < cache_expire_time:
        return inventory_cache
    
    db = get_database()
    if db is None:
        return []
    
    try:
        products = []
        cursor = db["products"].find(
            projection={
                "code": 1,
                "name": 1,
                "stock": 1,
                "last_updated": 1,
                "_id": 0
            }
        )
        
        async for product in cursor:
            products.append(InventoryItem(
                code=product.get("code", "N/A"),
                name=product.get("name", "Sin nombre"),
                current_stock=product.get("stock", 0),
                last_updated=product.get("last_updated", datetime.utcnow())
            ))
        
        # Actualizar caché
        inventory_cache = products
        cache_expire_time = current_time + CACHE_TTL
        
        return products
    
    except Exception as e:
        logger.error(f"Error al obtener inventario: {str(e)}")
        return []

@router.get("/history", response_model=List[HistoryItem])
async def get_product_history(product_id: str = Query(...)):
    db = get_database()
    if db is None:
        return []
    
    try:
        history = []
        cursor = db["stock_history"].find(
            {"product_id": product_id},
            projection={"date": 1, "reason": 1, "change": 1, "_id": 0}
        ).sort("date", -1)
        
        async for movement in cursor:
            history.append(HistoryItem(
                date=movement.get("date", datetime.utcnow()),
                reason=movement.get("reason", "movimiento"),
                change=movement.get("change", 0)
            ))
        
        return history
    
    except Exception as e:
        logger.error(f"Error al obtener historial: {str(e)}")
        return []