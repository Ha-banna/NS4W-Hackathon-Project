from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.mongo import connect_to_mongo, close_mongo_connection

from starlette.middleware.cors import CORSMiddleware
from supertokens_python import get_all_cors_headers
from supertokens_python.framework.fastapi import get_middleware
from app.auth.supertokens import init_supertokens

from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    connect_to_mongo()
    yield
    close_mongo_connection()

init_supertokens()

app = FastAPI(lifespan=lifespan)
app.add_middleware(get_middleware())

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.WEBSITE_DOMAIN
    ],
    allow_credentials=True,
    allow_methods=["GET", "PUT", "POST", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type"] + get_all_cors_headers(),
)

@app.get("/")
def root():
    return {"status": "ok"}
