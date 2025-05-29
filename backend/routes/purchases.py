# backend/routes/purchases.py

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def test_purchases():
    return {"message": "Purchases route works"}
