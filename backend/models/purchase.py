# models/purchase.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PurchaseBase(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)

class PurchaseCreate(PurchaseBase):
    pass

class PurchaseResponse(PurchaseBase):
    id: str
    created_at: datetime

    class Config:
        orm_mode = True
