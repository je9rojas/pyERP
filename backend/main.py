# 📁 backend/main.py
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import logging
import datetime
import traceback
import os
import asyncio
from backend.database import connect_to_mongodb, close_mongodb_connection
from backend.models.user import crear_superadmin_inicial, Usuario
from dotenv import load_dotenv
from jinja2.exceptions import TemplateNotFound

load_dotenv()

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "una_clave_secreta_muy_larga_y_compleja_1234567890!"),
    session_cookie="erp_session",
    max_age=3600
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

@app.on_event("startup")
async def startup_event():
    logger.info("Iniciando aplicación...")
    if not await connect_to_mongodb():
        logger.error("¡Error crítico! No se pudo conectar a MongoDB")
        return
    
    # Crear superadmin de forma síncrona
    await asyncio.to_thread(crear_superadmin_inicial)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Deteniendo aplicación...")
    await close_mongodb_connection()

static_dir = os.path.join(FRONTEND_DIR, "static")
templates_dir = os.path.join(FRONTEND_DIR, "templates")

# Crear directorios si no existen
os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    logger.error(f"¡Directorio estático no encontrado: {static_dir}")

# Configuración robusta de templates
templates = Jinja2Templates(directory=templates_dir)
templates.env.globals["current_year"] = datetime.datetime.now().year
templates.env.globals["static_url"] = lambda filename: f"/static/{filename}"

# Middleware mejorado para manejo de errores
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except TemplateNotFound as e:
        logger.error(f"Plantilla no encontrada: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Plantilla no encontrada", "details": str(e)}
        )
    except Exception as e:
        logger.error(f"Error no controlado: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "details": str(e)}
        )

async def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    
    try:
        return await asyncio.to_thread(lambda: Usuario.objects(id=user_id).first())
    except Exception as e:
        logger.error(f"Error obteniendo usuario: {str(e)}")
        return None

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    public_routes = ["/", "/login", "/health", "/static", "/logout"]
    
    if any(request.url.path == route or request.url.path.startswith(route) for route in public_routes):
        return await call_next(request)
    
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Permisos para rutas administrativas
    if request.url.path.startswith("/admin") and not (user.is_admin() or user.is_superadmin()):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": "Acceso no autorizado"}
        )
    
    # Permisos para rutas de gestión
    management_routes = ["/users", "/registro-productos", "/purchases", "/inventario"]
    if request.url.path in management_routes and not user.is_admin():
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": "Acceso no autorizado"}
        )
    
    # Permiso para ventas (vendedores y admins)
    if request.url.path == "/ventas" and not (user.is_vendedor() or user.is_admin()):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": "Acceso no autorizado"}
        )
    
    return await call_next(request)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return render_template("home", request, fecha_actual=datetime.datetime.now().strftime("%d/%m/%Y"))

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return render_template("login", request)

@app.post("/login")
async def login(request: Request):
    form_data = await request.form()
    email = form_data.get("email")
    password = form_data.get("password")
    
    usuario = await asyncio.to_thread(lambda: Usuario.objects(email=email).first())
    
    if not usuario:
        logger.warning(f"Intento de login fallido: usuario {email} no encontrado")
        return render_template("login", request, error="Credenciales inválidas")
    
    if not usuario.check_password(password):
        logger.warning(f"Intento de login fallido: contraseña incorrecta para {email}")
        return render_template("login", request, error="Credenciales inválidas")
    
    if not usuario.activo:
        logger.warning(f"Intento de login fallido: cuenta desactivada {email}")
        return render_template("login", request, error="Cuenta desactivada")
    
    request.session["user_id"] = str(usuario.id)
    logger.info(f"Login exitoso: {email} ({usuario.rol})")
    
    # Redirección según rol
    if usuario.is_admin() or usuario.is_superadmin():
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    elif usuario.is_vendedor():
        return RedirectResponse(url="/vendedor/dashboard", status_code=303)
    elif usuario.is_cliente():
        return RedirectResponse(url="/cliente/dashboard", status_code=303)
    else:
        return RedirectResponse(url="/", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    if "user_id" in request.session:
        del request.session["user_id"]
        logger.info("Usuario cerró sesión")
    return RedirectResponse(url="/", status_code=303)

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    user = await get_current_user(request)
    if not user or not (user.is_admin() or user.is_superadmin()):
        return RedirectResponse(url="/login", status_code=303)
    
    metricas = {
        "ventas_hoy": 142,
        "ingresos_hoy": 24580,
        "bajo_stock": 8,
        "usuarios_activos": 42
    }
    
    productos_populares = [
        {"nombre": "Laptop HP EliteBook", "categoria": "Computadoras", "ventas": 142},
        {"nombre": "Monitor Dell 24\"", "categoria": "Monitores", "ventas": 98},
    ]
    
    return render_template("admin/dashboard", request, user=user, metricas=metricas, productos_populares=productos_populares)

@app.get("/vendedor/dashboard", response_class=HTMLResponse)
async def vendedor_dashboard(request: Request):
    user = await get_current_user(request)
    if not user or not user.is_vendedor():
        return RedirectResponse(url="/login", status_code=303)
    
    metricas_vendedor = {
        "ventas_hoy": 15,
        "comisiones_hoy": 1250,
        "clientes_atendidos": 8,
        "objetivo_cumplido": 75
    }
    
    return render_template("vendedor/dashboard", request, user=user, metricas=metricas_vendedor)

@app.get("/cliente/dashboard", response_class=HTMLResponse)
async def cliente_dashboard(request: Request):
    user = await get_current_user(request)
    if not user or not user.is_cliente():
        return RedirectResponse(url="/login", status_code=303)
    
    datos_cliente = {
        "pedidos_pendientes": 2,
        "pedidos_completados": 12,
        "saldo_pendiente": 45000,
        "ultimos_pedidos": [
            {"id": "P-10023", "fecha": "2023-06-20", "total": 125000, "estado": "Entregado"},
            {"id": "P-10024", "fecha": "2023-06-22", "total": 78000, "estado": "En proceso"}
        ]
    }
    
    return render_template("cliente/dashboard", request, user=user, datos=datos_cliente)

@app.get("/ventas", response_class=HTMLResponse)
async def serve_ventas(request: Request):
    user = await get_current_user(request)
    if not user or not (user.is_vendedor() or user.is_admin()):
        return RedirectResponse(url="/login", status_code=303)
    
    return render_template("ventas/index", request, user=user)

@app.get("/purchases", response_class=HTMLResponse)
async def serve_compras(request: Request):
    user = await get_current_user(request)
    if not user or not user.is_admin():
        return RedirectResponse(url="/login", status_code=303)
    
    return render_template("compras/index", request, user=user)

@app.get("/inventario", response_class=HTMLResponse)
async def serve_inventario(request: Request):
    user = await get_current_user(request)
    if not user or not user.is_admin():
        return RedirectResponse(url="/login", status_code=303)
    
    return render_template("inventario/index", request, user=user)

@app.get("/users", response_class=HTMLResponse)
async def serve_users(request: Request):
    user = await get_current_user(request)
    if not user or not user.is_admin():
        return RedirectResponse(url="/login", status_code=303)
    
    usuarios = await asyncio.to_thread(lambda: list(Usuario.objects.all()))
    return render_template("usuarios/index", request, user=user, usuarios=usuarios)

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    favicon_path = os.path.join(FRONTEND_DIR, "static", "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return JSONResponse(status_code=404, content={"detail": "Favicon not found"})

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "API funcionando"}

# Helper para renderizar plantillas con manejo de errores
def render_template(template_name: str, request: Request, **kwargs):
    try:
        return templates.TemplateResponse(f"{template_name}.html", {"request": request, **kwargs})
    except TemplateNotFound:
        logger.error(f"Plantilla no encontrada: {template_name}.html")
        return JSONResponse(
            status_code=500,
            content={"error": "Plantilla no encontrada", "template": template_name}
        )

# Carga de routers API
try:
    from backend.routes import products, sales, purchases, inventory
    app.include_router(products.router, prefix="/api/products", tags=["Products"])
    app.include_router(sales.router, prefix="/api/sales", tags=["Sales"])
    app.include_router(purchases.router, prefix="/api/purchases", tags=["Purchases"])
    app.include_router(inventory.router, prefix="/api/inventory", tags=["Inventory"])
    
    from backend.routes import auth, users
    app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
    app.include_router(users.router, prefix="/api/users", tags=["Users"])
    
    logger.info("Routers API cargados correctamente")
except ImportError as e:
    logger.error(f"Error al cargar routers: {str(e)}")
    logger.error(traceback.format_exc())
except Exception as e:
    logger.error(f"Error inesperado al cargar routers: {str(e)}")
    logger.error(traceback.format_exc())

@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: Exception):
    return render_template("404", request)

logger.info("Aplicación FastAPI completamente inicializada")