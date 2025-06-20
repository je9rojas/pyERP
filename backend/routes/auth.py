from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from backend.models.user import Usuario
from werkzeug.security import check_password_hash

router = APIRouter()

@router.post("/login")
async def login(request: Request):
    data = await request.json()
    usuario = Usuario.objects(email=data.get("email")).first()
    
    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    if not check_password_hash(usuario.password, data.get("password")):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")
    
    # En un sistema real, aquí crearías una sesión o token JWT
    return JSONResponse({
        "mensaje": "Inicio de sesión exitoso",
        "rol": usuario.rol,
        "redirect": obtener_redireccion_por_rol(usuario.rol)
    })

@router.post("/logout")
async def logout():
    # En un sistema real, aquí invalidarías la sesión o token
    return JSONResponse({"mensaje": "Sesión cerrada"})

def obtener_redireccion_por_rol(rol):
    return {
        "superadmin": "/admin/dashboard",
        "admin": "/admin/dashboard",
        "vendedor": "/vendedor/dashboard",
        "cliente": "/cliente/dashboard"
    }.get(rol, "/")