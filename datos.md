erp/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models/
│   ├── routes/
│   └── crud/
│
├── frontend/
│   ├── js/
│   ├── css/
│   └── templates/
        ├── index.html
        ├── ventas.html
        ├── compras.html

│
├── .env               
├── requirements.txt
├── render.yaml           ✅
└── README.md



uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

.\venv\Scripts\activate

uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

(venv) PS D:\Projects\pyERP> uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000  

Info importante

Los índices se crean directamente en la base de datos MongoDB, no en los archivos de tu aplicación. Aquí te explico cómo y dónde hacerlo:

1. Dónde se crean los índices:
Directamente en MongoDB: Los índices se crean en el servidor de la base de datos MongoDB usando:

El shell de MongoDB (mongosh)

MongoDB Compass (interfaz gráfica)

Otras herramientas de administración de MongoDB

2. Cómo crear los índices:
Opción A: Usando MongoDB Shell (mongosh)
Conéctate a tu base de datos:

bash
mongosh "mongodb://usuario:contraseña@localhost:27017/nombre_db?authSource=admin"
Selecciona tu base de datos:

javascript
use nombre_db
Crea los índices:

javascript
// Para ventas
db.sales.createIndex({ "date": -1 })
db.sales.createIndex({ "client": "text" })
db.sales.createIndex({ "items.product_id": 1 })

// Para compras
db.purchases.createIndex({ "date": -1 })
db.purchases.createIndex({ "supplier": "text" })
db.purchases.createIndex({ "items.product_id": 1 })
Opción B: Usando MongoDB Compass (GUI)
Abre MongoDB Compass y conéctate a tu base de datos

Selecciona la colección sales

Ve a la pestaña "Indexes"

Haz clic en "Create Index"

Define los campos:

text
Key: { "date": -1 }
Repite para los otros índices

Repite el proceso para la colección purchases

3. Explicación de los índices creados:
Colección	Índice	Tipo	Beneficio
sales	{ "date": -1 }	Descendente	Optimiza búsquedas por fecha
sales	{ "client": "text" }	Texto	Acelera búsquedas de texto en clientes
sales	{ "items.product_id": 1 }	Ascendente	Mejora búsquedas por productos
purchases	{ "date": -1 }	Descendente	Optimiza búsquedas por fecha
purchases	{ "supplier": "text" }	Texto	Acelera búsquedas de texto en proveedores
purchases	{ "items.product_id": 1 }	Ascendente	Mejora búsquedas por productos
4. Cuándo crear los índices:
En producción: Durante el despliegue inicial o mantenimiento

En desarrollo: Al configurar la base de datos local

Después de grandes inserciones: Si agregaste muchos registros sin índices

5. Por qué son importantes:
Aceleran consultas en un 100-1000x

Reducen carga del CPU en el servidor

Optimizan operaciones con grandes volúmenes de datos

Mejoran tiempos de respuesta en búsquedas complejas

6. Verificación de índices existentes:
En mongosh:

javascript
// Para ventas
db.sales.getIndexes()

// Para compras
db.purchases.getIndexes()
7. Notas importantes:
Los índices consumen espacio en disco adicional

Afectan el rendimiento de escritura (insert/update)

Ideal para campos usados frecuentemente en:

WHERE

ORDER BY

JOIN

No crear índices en campos que:

Cambian frecuentemente

Tienen baja cardinalidad (ej: campos booleanos)

Los índices son fundamentales para el rendimiento de tu aplicación, especialmente cuando crezca la cantidad de registros en ventas y compras. ¡Te recomiendo implementarlos antes de poner en producción!