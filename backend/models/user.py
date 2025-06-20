from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField
from mongoengine.fields import (
    StringField, 
    DateTimeField, 
    IntField, 
    BooleanField
)
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Direccion(EmbeddedDocument):
    calle = StringField(required=True)
    ciudad = StringField(required=True)
    estado = StringField()
    codigo_postal = StringField()
    pais = StringField(default='México')

class Usuario(Document):
    email = StringField(required=True, unique=True)
    password = StringField(required=True)
    nombre = StringField(required=True)
    rol = StringField(choices=('superadmin', 'admin', 'vendedor', 'cliente'), default='cliente')
    direccion = EmbeddedDocumentField(Direccion)
    telefono = StringField()
    puntos_acumulados = IntField(default=0)
    fecha_registro = DateTimeField(default=datetime.utcnow)
    activo = BooleanField(default=True)
    creado_por = StringField()  # ID del usuario que creó este registro
    
    # Métodos para manejar la contraseña
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    # Métodos para verificar roles
    def is_superadmin(self):
        return self.rol == 'superadmin'
    
    def is_admin(self):
        return self.rol in ['superadmin', 'admin']
    
    def is_vendedor(self):
        return self.rol in ['superadmin', 'admin', 'vendedor']
    
    def is_cliente(self):
        return self.rol == 'cliente'

# Crear superadmin inicial si no existe
def crear_superadmin_inicial():
    if not Usuario.objects(rol='superadmin').first():
        superadmin = Usuario(
            email='superadmin@empresa.com',
            nombre='Super Administrador',
            rol='superadmin',
            creado_por='sistema'
        )
        superadmin.set_password('password_seguro')  # Cambiar en producción!
        superadmin.save()