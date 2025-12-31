# app/routes.py
from fastapi import APIRouter, UploadFile, File
from app.processing import process_tiff

router = APIRouter()

@router.post("/process")
async def process_image(file: UploadFile = File(...)):
    result = process_tiff(file)
    return {"message": "Processing started", "details": result}
