from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import logging

# Configurar logging
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

load_dotenv()

# Configuración de MongoDB
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB_NAME", "erp_db")

# Variables globales para la conexión
client = None
db = None

def get_database():
    """Devuelve la instancia de la base de datos"""
    global db
    return db

# Alias para compatibilidad con código existente
get_db = get_database

def is_database_connected():
    """Verifica si la conexión a la base de datos está activa"""
    global client
    return client is not None

async def connect_to_mongodb():
    """Establece conexión con MongoDB y verifica la conexión"""
    global client, db
    try:
        logger.info(f"Conectando a MongoDB: {MONGO_URI}")
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[DB_NAME]
        
        # Verificación rápida de conexión
        await client.server_info()
        logger.info(f"Conexión exitosa a MongoDB. Base de datos: {DB_NAME}")
        return True
    except Exception as e:
        logger.error(f"Error de conexión a MongoDB: {str(e)}")
        return False

async def close_mongodb_connection():
    """Cierra la conexión con MongoDB"""
    global client
    if client:
        client.close()
        logger.info("Conexión a MongoDB cerrada")