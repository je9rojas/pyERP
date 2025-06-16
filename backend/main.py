from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
from backend.database import connect_to_mongodb, close_mongodb_connection

# Configurar logging
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)  # Habilitar DEBUG

app = FastAPI()

# Eventos de inicio/cierre
@app.on_event("startup")
async def startup_event():
    logger.debug("Iniciando evento de startup...")
    connected = await connect_to_mongodb()
    if connected:
        logger.info("Conexión a MongoDB establecida correctamente")
    else:
        logger.critical("No se pudo establecer conexión con MongoDB")

@app.on_event("shutdown")
async def shutdown_event():
    logger.debug("Iniciando evento de shutdown...")
    await close_mongodb_connection()

# Configuración para servir archivos estáticos
app.mount("/static", StaticFiles(directory="frontend"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

# Rutas para las páginas HTML
@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/ventas", response_class=HTMLResponse)
async def serve_ventas(request: Request):
    return templates.TemplateResponse("ventas.html", {"request": request})

@app.get("/compras", response_class=HTMLResponse)
async def serve_compras(request: Request):
    return templates.TemplateResponse("compras.html", {"request": request})

# Health check
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "API funcionando"}

# Inclusión de los routers API
from backend.routes import products, sales, purchases
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(sales.router, prefix="/api/sales", tags=["Sales"])
app.include_router(purchases.router, prefix="/api/purchases", tags=["Purchases"])

logger.info("Aplicación FastAPI completamente inicializada")