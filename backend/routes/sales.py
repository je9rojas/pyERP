from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def test_sales():
    return {"message": "Sales route works"}
