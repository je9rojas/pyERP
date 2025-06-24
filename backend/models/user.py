# backend/models/user.py
from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField
from mongoengine.fields import (
    StringField, 
    DateTimeField, 
    IntField, 
    BooleanField,
    URLField,
    EmailField
)
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import logging

logger = logging.getLogger("uvicorn")

class Direccion(EmbeddedDocument):
    calle = StringField(required=True)
    ciudad = StringField(required=True)
    estado = StringField()
    codigo_postal = StringField()
    pais = StringField(default='México')

class Usuario(Document):
    meta = {'collection': 'usuarios'}
    
    public_id = StringField(default=lambda: str(uuid.uuid4()), unique=True)
    email = EmailField(required=True, unique=True)
    password = StringField(required=True)
    nombre = StringField(required=True)
    apellido = StringField()
    rol = StringField(choices=('superadmin', 'admin', 'vendedor', 'cliente'), default='cliente')
    direccion = EmbeddedDocumentField(Direccion)
    telefono = StringField()
    avatar = URLField(default='https://ui-avatars.com/api/?name=Usuario&background=random')
    ultimo_acceso = DateTimeField(default=datetime.utcnow)
    fecha_registro = DateTimeField(default=datetime.utcnow)
    activo = BooleanField(default=True)
    creado_por = StringField()  # ID del usuario que creó este registro
    
    # Métodos para manejar la contraseña
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        try:
            return check_password_hash(self.password, password)
        except Exception as e:
            logger.error(f"Error verificando contraseña: {str(e)}")
            return False
    
    # Métodos para verificar roles
    def is_superadmin(self):
        return self.rol == 'superadmin'
    
    def is_admin(self):
        return self.rol in ['superadmin', 'admin']
    
    def is_vendedor(self):
        return self.rol in ['superadmin', 'admin', 'vendedor']
    
    def is_cliente(self):
        return self.rol == 'cliente'
    
    def get_avatar_url(self):
        if self.avatar:
            return self.avatar
        return f"https://ui-avatars.com/api/?name={self.nombre.split()[0]}+{self.apellido or ''}&background=random"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "public_id": self.public_id,
            "nombre": self.nombre,
            "email": self.email,
            "rol": self.rol,
            "telefono": self.telefono,
            "avatar": self.get_avatar_url(),
            "ultimo_acceso": self.ultimo_acceso.isoformat(),
            "activo": self.activo
        }

# Crear superadmin inicial si no existe
def crear_superadmin_inicial():
    if not Usuario.objects(rol='superadmin').first():
        logger.info("Creando superadmin inicial...")
        superadmin = Usuario(
            email='superadmin@empresa.com',
            nombre='Super',
            apellido='Administrador',
            rol='superadmin',
            creado_por='sistema'
        )
        superadmin.set_password('password_seguro')  # Cambiar en producción!
        superadmin.save()
        logger.info(f"Superadmin creado con ID: {superadmin.id}")
    else:
        logger.info("Superadmin ya existe, omitiendo creación")