# models/sale.py

from mongoengine import Document, EmbeddedDocument, EmbeddedDocumentField, EmbeddedDocumentListField
from mongoengine.fields import (
    ReferenceField, 
    FloatField, 
    IntField, 
    DateTimeField, 
    StringField
)
from datetime import datetime

class ItemVenta(EmbeddedDocument):
    producto = ReferenceField('Producto', required=True)
    cantidad = IntField(required=True, min_value=1, default=1)
    precio_unitario = FloatField(required=True, min_value=0)
    puntos_obtenidos = IntField(min_value=0)
    
    def clean(self):
        # Calcular puntos automáticamente si no se especifican
        if self.puntos_obtenidos is None:
            self.puntos_obtenidos = self.producto.puntos * self.cantidad

class Venta(Document):
    cliente = ReferenceField('Usuario', required=True)
    items = EmbeddedDocumentListField(ItemVenta, required=True)
    total = FloatField(required=True, min_value=0)
    puntos_totales = IntField(min_value=0)  # Puntos de productos + bonificación
    puntos_bonificacion = IntField(default=0)  # Puntos adicionales por compra
    fecha = DateTimeField(default=datetime.utcnow)
    estado = StringField(choices=('pendiente', 'completada', 'cancelada'), default='pendiente')
    
    def calcular_totales(self):
        # Calcular total monetario
        self.total = sum(item.precio_unitario * item.cantidad for item in self.items)
        
        # Calcular puntos totales (productos + bonificación)
        puntos_productos = sum(item.puntos_obtenidos for item in self.items)
        self.puntos_totales = puntos_productos + self.puntos_bonificacion
        
        # Actualizar puntos del cliente
        self.cliente.puntos_acumulados += self.puntos_totales
        self.cliente.save()
    
    def save(self, *args, **kwargs):
        self.calcular_totales()
        super().save(*args, **kwargs)