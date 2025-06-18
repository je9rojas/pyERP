from fastapi import APIRouter, Query
from pydantic import BaseModel
from backend.database import get_database
from datetime import datetime
from typing import List, Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Modelo para los items de inventario
class InventoryItem(BaseModel):
    code: str
    name: str
    current_stock: int
    last_updated: datetime
    history: List[dict] = []

# Modelo para la respuesta del historial
class HistoryItem(BaseModel):
    date: datetime
    reason: str
    change: int

@router.get("/list", response_model=List[InventoryItem])
async def get_inventory():
    db = get_database()
    if db is None:
        return []
    
    try:
        # Obtener productos con stock actual
        products = []
        cursor = db["products"].find()
        
        async for product in cursor:
            # Obtener campos con valores por defecto seguros
            code = product.get("code", "N/A")
            name = product.get("name", "Sin nombre")
            stock = product.get("stock", 0)
            last_updated = product.get("last_updated", datetime.utcnow())
            
            # Obtener historial reciente (últimos 5 movimientos)
            history = []
            history_cursor = db["stock_history"].find({"product_id": code}).sort("date", -1).limit(5)
            
            async for movement in history_cursor:
                history.append({
                    "type": movement.get("reason", "movimiento"),
                    "quantity": movement.get("change", 0),
                    "date": movement.get("date", datetime.utcnow())
                })
            
            products.append(InventoryItem(
                code=code,
                name=name,
                current_stock=stock,
                last_updated=last_updated,
                history=history
            ))
        
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
        cursor = db["stock_history"].find({"product_id": product_id}).sort("date", -1)
        
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