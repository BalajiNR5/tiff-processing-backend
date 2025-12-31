from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
import shutil
import os
import uuid

from app.processing import process_tiff_background

router = APIRouter()

UPLOAD_DIR = "tmp"
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE = 250_000_000  # 250 MB safety cap for free tier

@router.post("/process")
async def process_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    # Validate file type
    if not file.filename.lower().endswith((".tif", ".tiff")):
        raise HTTPException(status_code=400, detail="Only TIFF files are supported")

    # Generate unique job ID
    job_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{job_id}.tiff")

    # --- STREAM FILE TO DISK (NO RAM LOAD) ---
    size = 0
    with open(file_path, "wb") as buffer:
        while True:
            chunk = await file.read(1024 * 1024)  # 1 MB chunks
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_FILE_SIZE:
                buffer.close()
                os.remove(file_path)
                raise HTTPException(status_code=413, detail="File too large for free tier")
            buffer.write(chunk)

    # --- BACKGROUND PROCESSING ---
    background_tasks.add_task(
        process_tiff_background,
        file_path,
        job_id
    )

    return {
        "job_id": job_id,
        "status": "processing_started"
    }
