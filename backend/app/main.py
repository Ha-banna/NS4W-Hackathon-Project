from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.db.mongo import connect_to_mongo, close_mongo_connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    connect_to_mongo()
    yield
    close_mongo_connection()

app = FastAPI(lifespan=lifespan)

@app.get("/")
def root():
    return {"status": "ok"}