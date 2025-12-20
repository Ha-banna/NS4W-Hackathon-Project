from fastapi import APIRouter, HTTPException
from app.db import mongo 

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/cv-result/{id}")
def get_cv_result(id: str):
    doc = mongo.db["cv_results"].find_one({"_id": int(id)})
    return doc

@router.get("/cv-results")
def get_cv_results():
    docs = list(mongo.db["cv_results"].find())
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs