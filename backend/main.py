from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

from backend.routes import products, sales, purchases

app = FastAPI()

app.mount("/static", StaticFiles(directory="frontend"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/ventas", response_class=HTMLResponse)
async def serve_ventas(request: Request):
    return templates.TemplateResponse("ventas.html", {"request": request})

@app.get("/compras", response_class=HTMLResponse)
async def serve_compras(request: Request):
    return templates.TemplateResponse("compras.html", {"request": request})

app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(sales.router, prefix="/api/sales", tags=["Sales"])
app.include_router(purchases.router, prefix="/api/purchases", tags=["Purchases"])
