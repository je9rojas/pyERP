# 📁 backend/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from mongoengine import connect as mongoengine_connect
from dotenv import load_dotenv
import os
import logging

# Configurar logging
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

load_dotenv()

# Configuración de MongoDB
MONGO_URI = os.getenv("MONGODB_URI", "mongodb+srv://db_admin:dQ6n5znkCVO0ANm6@erp-cluster.fzyhb.mongodb.net/erp_db?retryWrites=true&w=majority&appName=ERP-cluster")
DB_NAME = os.getenv("MONGO_DB_NAME", "erp_db")

# Variables globales para la conexión
async_client = None
async_db = None

def get_database():
    """Devuelve la instancia de la base de datos asíncrona"""
    global async_db
    if async_db is None:
        raise RuntimeError("Database not initialized")
    return async_db

def is_database_connected():
    """Verifica si la conexión a la base de datos está activa"""
    global async_client
    return async_client is not None

async def connect_to_mongodb():
    """Establece conexión con MongoDB y verifica la conexión"""
    global async_client, async_db
    try:
        logger.info(f"Conectando a MongoDB: {MONGO_URI}")
        
        # Conexión asíncrona para Motor (FastAPI)
        async_client = AsyncIOMotorClient(MONGO_URI)
        async_db = async_client[DB_NAME]
        
        # Verificación rápida de conexión asíncrona
        await async_client.server_info()
        logger.info(f"Conexión asíncrona exitosa a MongoDB. Base de datos: {DB_NAME}")
        
        # Conexión síncrona para MongoEngine (modelos)
        # IMPORTANTE: Usar connect() en lugar de mongoengine_connect
        from mongoengine import connect
        connect(host=MONGO_URI, alias='default')
        
        logger.info("Conexión síncrona para MongoEngine establecida")
        return True
    except Exception as e:
        logger.error(f"Error de conexión a MongoDB: {str(e)}")
        return False

async def close_mongodb_connection():
    """Cierra la conexión con MongoDB"""
    global async_client
    if async_client:
        async_client.close()
        logger.info("Conexión a MongoDB cerrada")