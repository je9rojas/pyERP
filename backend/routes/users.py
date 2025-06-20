from fastapi import APIRouter, HTTPException, Request
from backend.models.user import Usuario
from werkzeug.security import generate_password_hash

router = APIRouter()

@router.post("/")
async def crear_usuario(request: Request):
    data = await request.json()
    
    # Verificar si el usuario ya existe
    if Usuario.objects(email=data.get("email")).first():
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # Crear nuevo usuario
    nuevo_usuario = Usuario(
        email=data["email"],
        nombre=data["nombre"],
        rol=data.get("rol", "cliente")
    )
    nuevo_usuario.set_password(data["password"])
    
    try:
        nuevo_usuario.save()
        return {"mensaje": "Usuario creado", "id": str(nuevo_usuario.id)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{user_id}")
async def actualizar_usuario(user_id: str, request: Request):
    data = await request.json()
    usuario = Usuario.objects(id=user_id).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Actualizar campos
    if "nombre" in data:
        usuario.nombre = data["nombre"]
    if "email" in data:
        usuario.email = data["email"]
    if "password" in data:
        usuario.set_password(data["password"])
    if "rol" in data:
        usuario.rol = data["rol"]
    if "activo" in data:
        usuario.activo = data["activo"]
    
    try:
        usuario.save()
        return {"mensaje": "Usuario actualizado"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{user_id}")
async def eliminar_usuario(user_id: str):
    usuario = Usuario.objects(id=user_id).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if usuario.rol == "superadmin":
        raise HTTPException(status_code=403, detail="No se puede eliminar al superadmin")
    
    try:
        usuario.delete()
        return {"mensaje": "Usuario eliminado"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))