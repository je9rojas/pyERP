from datetime import datetime, timedelta
from backend.models.user import Usuario
from backend.models.product import Producto
from backend.models.sale import Venta

def obtener_metricas_admin():
    hoy = datetime.now().date()
    
    # Obtener ventas de hoy
    ventas_hoy = Venta.objects(fecha__gte=hoy).count()
    
    # Obtener ingresos de hoy
    ingresos_hoy = sum(v.total for v in Venta.objects(fecha__gte=hoy))
    
    # Obtener productos con bajo stock
    bajo_stock = Producto.objects(stock__lt=5).count()
    
    # Obtener usuarios activos
    usuarios_activos = Usuario.objects(activo=True).count()
    
    return {
        "ventas_hoy": ventas_hoy,
        "ingresos_hoy": ingresos_hoy,
        "bajo_stock": bajo_stock,
        "usuarios_activos": usuarios_activos
    }

def obtener_productos_populares(limite=5):
    # Esta es una implementación simplificada
    # En una aplicación real, usarías agregaciones de MongoDB
    productos = Producto.objects.order_by('-ventas_totales')[:limite]
    return [
        {
            "nombre": p.nombre,
            "categoria": p.categoria.nombre,
            "ventas": p.ventas_totales
        }
        for p in productos
    ]

def obtener_metricas_vendedor(usuario_id):
    hoy = datetime.now().date()
    ventas = Venta.objects(vendedor=usuario_id, fecha__gte=hoy)
    
    return {
        "ventas_hoy": ventas.count(),
        "comisiones_hoy": sum(v.comision for v in ventas),
        "clientes_atendidos": len(set(v.cliente.id for v in ventas)),
        "objetivo_cumplido": min(100, int(ventas.count() / 20 * 100))  # Ejemplo: objetivo de 20 ventas
    }

def obtener_datos_cliente(usuario_id):
    # Obtener pedidos del cliente (en nuestro modelo, las ventas a este cliente)
    pedidos = Venta.objects(cliente=usuario_id)
    pedidos_pendientes = sum(1 for p in pedidos if p.estado == 'pendiente')
    pedidos_completados = sum(1 for p in pedidos if p.estado == 'completado')
    saldo_pendiente = sum(p.total for p in pedidos if p.estado == 'pendiente')
    
    ultimos_pedidos = [
        {"id": str(p.id), "fecha": p.fecha.strftime("%Y-%m-%d"), "total": p.total, "estado": p.estado}
        for p in pedidos.order_by('-fecha')[:2]
    ]
    
    return {
        "pedidos_pendientes": pedidos_pendientes,
        "pedidos_completados": pedidos_completados,
        "saldo_pendiente": saldo_pendiente,
        "ultimos_pedidos": ultimos_pedidos
    }