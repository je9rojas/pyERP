# backend/database.py

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

# Asegúrate de que esta clave coincida con la definida en render.yaml
MONGO_URI = os.getenv("MONGODB_URI")

# Conexión con MongoDB
client = AsyncIOMotorClient(MONGO_URI)
db = client["erp_db"]
