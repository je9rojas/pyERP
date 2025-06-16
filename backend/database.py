from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import asyncio
import logging

# Configurar logging
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.DEBUG)

load_dotenv()

# Configuración de MongoDB
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB_NAME", "erp_db")

# Variables globales para la conexión
client = None
db = None

async def connect_to_mongodb():
    """Establece conexión con MongoDB y verifica la conexión"""
    global client, db
    try:
        logger.debug(f"MONGO_URI: {MONGO_URI}")
        logger.debug(f"DB_NAME: {DB_NAME}")
        
        logger.info(f"Conectando a MongoDB en: {MONGO_URI}")
        client = AsyncIOMotorClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
        
        # Forzar una operación simple para verificar la conexión
        logger.debug("Obteniendo server_info()...")
        server_info = await client.server_info()
        logger.info(f"Conexión exitosa. Versión de MongoDB: {server_info['version']}")
        
        db = client[DB_NAME]
        logger.info(f"Usando base de datos: {DB_NAME}")
        
        # Verificar colección de productos
        logger.debug("Listando colecciones...")
        coll_names = await db.list_collection_names()
        logger.info(f"Colecciones disponibles: {coll_names}")
        
        if "products" in coll_names:
            logger.debug("Contando productos...")
            products_count = await db.products.count_documents({})
            logger.info(f"Total de productos: {products_count}")
            
            if products_count > 0:
                logger.debug("Obteniendo primer producto...")
                first_product = await db.products.find_one()
                logger.info(f"Primer producto: {first_product}")
        else:
            logger.warning("La colección 'products' no existe")
            
        return True
    except Exception as e:
        logger.exception(f"Error crítico de conexión a MongoDB: {str(e)}")
        return False

async def close_mongodb_connection():
    """Cierra la conexión con MongoDB"""
    global client
    if client:
        client.close()
        logger.info("Conexión a MongoDB cerrada")

# Nueva función para obtener la instancia de la base de datos
def get_database():
    """Devuelve la instancia de la base de datos"""
    return db