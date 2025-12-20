from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.mongo import connect_to_mongo, close_mongo_connection

from starlette.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.analysis import router as analysis_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    connect_to_mongo()
    yield
    close_mongo_connection()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.WEBSITE_DOMAIN
    ],
    allow_credentials=True,
    allow_methods=["GET", "PUT", "POST", "DELETE", "OPTIONS", "PATCH"],
)

app.include_router(dashboard_router)
app.include_router(analysis_router)

@app.get("/")
def root():
    return {"status": "ok"}
