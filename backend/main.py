# 📁 backend/main.py

from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware  # Importar middleware de sesiones
import logging
import datetime
import traceback
import os
from backend.database import connect_to_mongodb, close_mongodb_connection
from backend.models.user import crear_superadmin_inicial, Usuario
from werkzeug.security import check_password_hash
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import HTTPException, status
from dotenv import load_dotenv  # Para cargar variables de entorno

# Cargar variables de entorno desde .env
load_dotenv()

# Configurar logging
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

app = FastAPI()
security = HTTPBasic()

# Añadir middleware de sesiones (¡IMPORTANTE! Debe ir antes de cualquier middleware que use sesiones)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "una_clave_secreta_muy_larga_y_compleja_1234567890!"),
    session_cookie="erp_session",
    max_age=3600  # 1 hora
)

# Obtener la ruta base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Eventos de inicio/cierre
@app.on_event("startup")
async def startup_event():
    logger.info("Iniciando aplicación...")
    if not await connect_to_mongodb():
        logger.error("¡Error crítico! No se pudo conectar a MongoDB")
        return
    
    # Crear superadmin inicial si no existe
    crear_superadmin_inicial()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Deteniendo aplicación...")
    await close_mongodb_connection()

# Configuración para servir archivos estáticos
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
    templates = Jinja2Templates(directory="")

# Añadir variables globales a todos los templates
templates.env.globals["current_year"] = datetime.datetime.now().year
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

# Función para obtener usuario actual
async def get_current_user(request: Request):
    user_id = request.session.get("user_id")  # Cambiamos a "user_id"
    if not user_id:
        return None
    
    try:
        return Usuario.objects(id=user_id).first()
    except:
        return None

# Middleware para verificar autenticación
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Lista de rutas que no requieren autenticación
    public_routes = ["/", "/login", "/health", "/static", "/logout"]
    
    # Verificar si la ruta es pública
    if any(request.url.path == route or request.url.path.startswith(route) for route in public_routes):
        return await call_next(request)
    
    # Verificar sesión de usuario
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Verificar roles para rutas específicas
    if request.url.path.startswith("/admin") and not user.is_admin():
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": "Acceso no autorizado"}
        )
    
    if request.url.path.startswith("/vendedor") and not user.is_vendedor():
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": "Acceso no autorizado"}
        )
    
    if request.url.path.startswith("/cliente") and not user.is_cliente():
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"error": "Acceso no autorizado"}
        )
    
    return await call_next(request)

# Ruta para la página de inicio
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {
        "request": request,
        "fecha_actual": datetime.datetime.now().strftime("%d/%m/%Y")
    })

# Ruta para login
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Ruta para procesar login
@app.post("/login")
async def login(request: Request):
    form_data = await request.form()
    email = form_data.get("email")
    password = form_data.get("password")
    
    usuario = Usuario.objects(email=email).first()
    
    if not usuario:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Credenciales inválidas"
        })
    
    if not check_password_hash(usuario.password, password):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Credenciales inválidas"
        })
    
    if not usuario.activo:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Cuenta desactivada"
        })
    
    # Guardar solo el ID del usuario en la sesión
    request.session["user_id"] = str(usuario.id)
    
    # Redirigir según rol
    if usuario.is_admin() or usuario.is_superadmin():
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    elif usuario.is_vendedor():
        return RedirectResponse(url="/vendedor/dashboard", status_code=303)
    elif usuario.is_cliente():
        return RedirectResponse(url="/cliente/dashboard", status_code=303)
    else:
        return RedirectResponse(url="/", status_code=303)

# Ruta para logout
@app.get("/logout")
async def logout(request: Request):
    if "user_id" in request.session:
        del request.session["user_id"]
    return RedirectResponse(url="/", status_code=303)

# Ruta para dashboard de administrador
@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    user = await get_current_user(request)
    if not user or not user.is_admin():
        return RedirectResponse(url="/login", status_code=303)
    
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "user": user
    })

# Ruta para dashboard de vendedor
@app.get("/vendedor/dashboard", response_class=HTMLResponse)
async def vendedor_dashboard(request: Request):
    user = await get_current_user(request)
    if not user or not user.is_vendedor():
        return RedirectResponse(url="/login", status_code=303)
    
    return templates.TemplateResponse("vendedor_dashboard.html", {
        "request": request,
        "user": user
    })

# Ruta para dashboard de cliente
@app.get("/cliente/dashboard", response_class=HTMLResponse)
async def cliente_dashboard(request: Request):
    user = await get_current_user(request)
    if not user or not user.is_cliente():
        return RedirectResponse(url="/login", status_code=303)
    
    return templates.TemplateResponse("cliente_dashboard.html", {
        "request": request,
        "user": user
    })

# Ruta para el dashboard (página de inicio original)
@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    try:
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "fecha_actual": datetime.datetime.now().strftime("%d/%m/%Y"),
            "user": user
        })
    except Exception as e:
        logger.error(f"Error al cargar dashboard: {str(e)}")
        logger.error(traceback.format_exc())
        return RedirectResponse(url="/ventas", status_code=303)

# Ruta para registro de productos
@app.get("/registro-productos", response_class=HTMLResponse)
async def serve_registro_productos(request: Request):
    user = await get_current_user(request)
    if not user or not user.is_admin():
        return RedirectResponse(url="/login", status_code=303)
    
    try:
        return templates.TemplateResponse("registro_productos.html", {
            "request": request,
            "user": user
        })
    except Exception as e:
        logger.error(f"Error al cargar registro productos: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Error al cargar página"}
        )

# Rutas para las demás páginas (con protección de acceso)
@app.get("/ventas", response_class=HTMLResponse)
async def serve_ventas(request: Request):
    user = await get_current_user(request)
    if not user or not (user.is_vendedor() or user.is_admin()):
        return RedirectResponse(url="/login", status_code=303)
    
    try:
        return templates.TemplateResponse("ventas.html", {
            "request": request,
            "user": user
        })
    except Exception as e:
        logger.error(f"Error al cargar ventas: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Error al cargar página de ventas"}
        )

@app.get("/compras", response_class=HTMLResponse)
async def serve_compras(request: Request):
    user = await get_current_user(request)
    if not user or not user.is_admin():
        return RedirectResponse(url="/login", status_code=303)
    
    try:
        return templates.TemplateResponse("compras.html", {
            "request": request,
            "user": user
        })
    except Exception as e:
        logger.error(f"Error al cargar compras: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Error al cargar página de compras"}
        )

@app.get("/inventario", response_class=HTMLResponse)
async def serve_inventario(request: Request):
    user = await get_current_user(request)
    if not user or not user.is_admin():
        return RedirectResponse(url="/login", status_code=303)
    
    try:
        return templates.TemplateResponse("inventario.html", {
            "request": request,
            "user": user
        })
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
    
    # Nuevos routers para autenticación y usuarios
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

# Manejo de errores para rutas no encontradas
@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: Exception):
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

logger.info("Aplicación FastAPI completamente inicializada")