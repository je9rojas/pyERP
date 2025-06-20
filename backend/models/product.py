# models/product.py

from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, EmbeddedDocumentListField
from mongoengine.fields import (
    StringField, 
    IntField, 
    FloatField, 
    DictField, 
    BooleanField,
    ListField
)

class Dimensiones(EmbeddedDocument):
    tipo = StringField(required=True, choices=('aire', 'aceite', 'combustible', 'habitáculo'))
    atributos = DictField()  # Ej: {diametro: 200, altura: 50, rosca: 'M22x1.5'}

class CodigoProducto(EmbeddedDocument):
    marca = StringField(required=True, default='WIX')
    codigo = StringField(required=True)
    region = StringField(choices=('USA', 'Europa', 'Asia', 'Otro'))
    es_principal = BooleanField(default=False)
    es_generico = BooleanField(default=False)

class AplicacionVehiculo(EmbeddedDocument):
    marca_vehiculo = StringField(required=True)  # Ej: Fiat
    modelo = StringField(required=True)          # Ej: Panda
    años = StringField()                         # Ej: "2010-2015"

class Producto(Document):
    nombre = StringField(required=True)
    descripcion = StringField()
    codigos = EmbeddedDocumentListField(CodigoProducto, required=True)
    dimensiones = EmbeddedDocumentField(Dimensiones)
    aplicaciones = EmbeddedDocumentListField(AplicacionVehiculo)
    precio = FloatField(required=True, min_value=0)
    puntos = IntField(default=0, min_value=0)  # Puntos por unidad
    stock = IntField(default=0, min_value=0)
    
    meta = {
        'indexes': [
            {'fields': ['codigos.codigo']},
            {'fields': ['codigos.marca']},
            {'fields': ['aplicaciones.marca_vehiculo']}
        ]
    }
    
    def __str__(self):
        return f"{self.nombre} ({self.codigo_principal})"
    
    @property
    def codigo_principal(self):
        principal = [c for c in self.codigos if c.es_principal]
        return principal[0].codigo if principal else self.codigos[0].codigo