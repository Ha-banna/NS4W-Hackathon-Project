from fastapi import APIRouter, HTTPException
from app.db.mongo import db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/cv-result/{id}")
def get_cv_results(id: str):
    doc = db["cv_results"].find_one({"_id": id})

    return doc

@router.get("/cv-results")
def get_cv_results():
    doc = db["cv_results"].find()

    return doc