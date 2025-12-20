import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path

from app.services.analysis.pipeline.runner import run_pipeline

router = APIRouter(prefix="/analysis", tags=["analysis"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload-cv")
async def upload_cv(file: UploadFile = File(...)):
    # 1) validate
    if file.content_type not in {"application/pdf"}:
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    # 2) save to disk (so your cv_to_json strategy can read it by path)
    run_id = str(uuid.uuid4())
    pdf_path = UPLOAD_DIR / f"{run_id}.pdf"

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file.")

    pdf_path.write_bytes(contents)

    # 3) run pipeline
    ctx = await run_pipeline(cv_path=str(pdf_path), run_id= run_id)

    # 4) return response
    return {
        "cv_json_ready": bool(ctx.cv_json),
    }
