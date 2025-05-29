from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from backend.routes import products, sales, purchases

app = FastAPI()

# Montar la carpeta frontend como archivos estáticos accesibles desde /static
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Ruta para servir index.html en la raíz
@app.get("/", response_class=FileResponse)
async def serve_index():
    return FileResponse(os.path.join("frontend", "index.html"))

# Rutas API
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(sales.router, prefix="/api/sales", tags=["Sales"])
app.include_router(purchases.router, prefix="/api/purchases", tags=["Purchases"])
