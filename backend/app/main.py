from fastapi import FastAPI
from app.core.config import settings

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"database_configured": bool(settings.DATABASE_URL)}
