from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from app.core.config import settings  # <-- import the instance, not the class

client: MongoClient | None = None
db = None 

def connect_to_mongo():
    global client, db
    client = MongoClient(settings.MONGODB_URI, server_api=ServerApi("1"))

    db = client[settings.MONGODB_DB]

def close_mongo_connection():
    global client
    if client:
        client.close()
        client = None
