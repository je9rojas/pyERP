# models/sale.py

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SaleBase(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)

class SaleCreate(SaleBase):
    pass

class SaleResponse(SaleBase):
    id: str
    created_at: datetime

    class Config:
        orm_mode = True
