from pydantic import BaseModel, Field
from typing import Optional
from bson import ObjectId

class Product(BaseModel):
    name: str
    description: Optional[str] = None
    stock: int = 0
    price: float

class ProductInDB(Product):
    id: str = Field(default_factory=str, alias="_id")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
