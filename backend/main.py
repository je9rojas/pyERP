from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
import datetime  # Importar datetime para el dashboard
from backend.database import connect_to_mongodb, close_mongodb_connection

# Configurar logging
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

app = FastAPI()

# Eventos de inicio/cierre
@app.on_event("startup")
async def startup_event():
    logger.info("Iniciando aplicación...")
    if not await connect_to_mongodb():
        logger.error("¡Error crítico! No se pudo conectar a MongoDB")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Deteniendo aplicación...")
    await close_mongodb_connection()

# Configuración para servir archivos estáticos
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

# Añadir variables globales a todos los templates
templates.env.globals["current_year"] = datetime.datetime.now().year

# Middleware para manejar errores
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Error no controlado: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "details": str(e)}
        )

# Ruta para el dashboard (página de inicio)
@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "fecha_actual": datetime.datetime.now().strftime("%d/%m/%Y")
    })

# Ruta para registro de productos
@app.get("/registro-productos", response_class=HTMLResponse)
async def serve_registro_productos(request: Request):
    return templates.TemplateResponse("registro_productos.html", {"request": request})

# Rutas para las demás páginas
@app.get("/ventas", response_class=HTMLResponse)
async def serve_ventas(request: Request):
    return templates.TemplateResponse("ventas.html", {"request": request})

@app.get("/compras", response_class=HTMLResponse)
async def serve_compras(request: Request):
    return templates.TemplateResponse("compras.html", {"request": request})

@app.get("/inventario", response_class=HTMLResponse)
async def serve_inventario(request: Request):
    return templates.TemplateResponse("inventario.html", {"request": request})

# Health check
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "API funcionando"}

# Importación segura de routers
try:
    from backend.routes import products, sales, purchases, inventory
    app.include_router(products.router, prefix="/api/products", tags=["Products"])
    app.include_router(sales.router, prefix="/api/sales", tags=["Sales"])
    app.include_router(purchases.router, prefix="/api/purchases", tags=["Purchases"])
    app.include_router(inventory.router, prefix="/api/inventory", tags=["Inventory"])
    logger.info("Routers API cargados correctamente")
except ImportError as e:
    logger.error(f"Error al cargar routers: {str(e)}")
    import traceback
    logger.error(traceback.format_exc())  # Traza detallada
except Exception as e:
    logger.error(f"Error inesperado al cargar routers: {str(e)}")
    import traceback
    logger.error(traceback.format_exc())

logger.info("Aplicación FastAPI completamente inicializada")