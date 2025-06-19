# 📁 backend/routes/main.py

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
import datetime
import traceback
import os
from backend.database import connect_to_mongodb, close_mongodb_connection

# Configurar logging
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

app = FastAPI()

# Obtener la ruta base del proyecto - SOLUCIÓN CORREGIDA
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Sube un nivel
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")  # Ahora apunta a pyERP/frontend

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

# Configuración para servir archivos estáticos - VERIFICAR QUE EL DIRECTORIO EXISTA
static_dir = os.path.join(FRONTEND_DIR, "static")
templates_dir = os.path.join(FRONTEND_DIR, "templates")

# Verificar que los directorios existen antes de montarlos
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    logger.error(f"¡Directorio estático no encontrado: {static_dir}")

if os.path.exists(templates_dir):
    templates = Jinja2Templates(directory=templates_dir)
else:
    logger.error(f"¡Directorio de templates no encontrado: {templates_dir}")
    # Crear un objeto templates vacío para evitar errores
    templates = Jinja2Templates(directory="")

# Añadir variables globales a todos los templates
templates.env.globals["current_year"] = datetime.datetime.now().year
# Función para generar URLs estáticas
templates.env.globals["static_url"] = lambda filename: f"/static/{filename}"

# Middleware para manejar errores
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logger.error(f"Error no controlado: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "details": str(e)}
        )

# Ruta para el dashboard (página de inicio)
@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    try:
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "fecha_actual": datetime.datetime.now().strftime("%d/%m/%Y")
        })
    except Exception as e:
        logger.error(f"Error al cargar dashboard: {str(e)}")
        logger.error(traceback.format_exc())
        return RedirectResponse(url="/ventas")

# Ruta para registro de productos
@app.get("/registro-productos", response_class=HTMLResponse)
async def serve_registro_productos(request: Request):
    try:
        return templates.TemplateResponse("registro_productos.html", {"request": request})
    except Exception as e:
        logger.error(f"Error al cargar registro productos: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Error al cargar página"}
        )

# Rutas para las demás páginas
@app.get("/ventas", response_class=HTMLResponse)
async def serve_ventas(request: Request):
    try:
        return templates.TemplateResponse("ventas.html", {"request": request})
    except Exception as e:
        logger.error(f"Error al cargar ventas: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Error al cargar página de ventas"}
        )

@app.get("/compras", response_class=HTMLResponse)
async def serve_compras(request: Request):
    try:
        return templates.TemplateResponse("compras.html", {"request": request})
    except Exception as e:
        logger.error(f"Error al cargar compras: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Error al cargar página de compras"}
        )

@app.get("/inventario", response_class=HTMLResponse)
async def serve_inventario(request: Request):
    try:
        return templates.TemplateResponse("inventario.html", {"request": request})
    except Exception as e:
        logger.error(f"Error al cargar inventario: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Error al cargar página de inventario"}
        )

# Favicon para evitar errores
@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    favicon_path = os.path.join(FRONTEND_DIR, "static", "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    else:
        logger.warning("Favicon no encontrado, devolviendo respuesta vacía")
        return FileResponse("")

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
    logger.error(traceback.format_exc())
except Exception as e:
    logger.error(f"Error inesperado al cargar routers: {str(e)}")
    logger.error(traceback.format_exc())

# Manejo de errores para rutas no encontradas
@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: Exception):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

logger.info("Aplicación FastAPI completamente inicializada")