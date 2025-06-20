import sys
import os
import asyncio
from pathlib import Path

# Configurar el path correctamente
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent

# Añadir el directorio raíz al path de Python
sys.path.insert(0, str(project_root))

print(f"Buscando módulos en: {sys.path}")

try:
    from backend.database import connect_to_mongodb
    from backend.models.user import Usuario
    print("Módulos importados correctamente!")
except ImportError as e:
    print(f"Error al importar módulos: {e}")
    sys.exit(1)

async def main():
    print("\n=== Creación de Superadmin ===")
    
    if not await connect_to_mongodb():
        print("Error conectando a MongoDB. Verifica la conexión.")
        return
    
    email = input("Ingrese email para superadmin: ")
    password = input("Ingrese contraseña: ")
    nombre = input("Ingrese nombre [Super Administrador]: ") or "Super Administrador"
    
    # Verificar si ya existe
    existing_user = Usuario.objects(email=email).first()
    if existing_user:
        print(f"¡Ya existe un usuario con email {email} (Rol: {existing_user.rol})!")
        return
    
    # Crear superadmin
    superadmin = Usuario(
        email=email,
        nombre=nombre,
        rol='superadmin',
        creado_por='manual'
    )
    superadmin.set_password(password)
    superadmin.save()
    
    print("\n✅ Superadmin creado exitosamente!")
    print(f"  Email: {email}")
    print(f"  Contraseña: {password}")
    print("\nAhora puedes iniciar sesión en http://localhost:8000/login")

if __name__ == "__main__":
    asyncio.run(main())


#.\venv\Scripts\activate
#python scripts/create_superadmin.py
#(venv) PS D:\Projects\pyERP> python scripts/create_superadmin.py