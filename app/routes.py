from fastapi import APIRouter, UploadFile, BackgroundTasks
from app.processing import process_tiff_background
import uuid
import os

# Create router
router = APIRouter()

# Ensure tmp directory exists
TEMP_DIR = "tmp"
os.makedirs(TEMP_DIR, exist_ok=True)

@router.post("/process")
async def process_tiff(file: UploadFile, background_tasks: BackgroundTasks):
    """
    Endpoint to upload TIFF file and start background processing.
    Returns a job_id to track the task.
    """

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Save uploaded file to temporary directory
    temp_path = os.path.join(TEMP_DIR, f"{job_id}.tiff")
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    # Add background task to process the TIFF
    background_tasks.add_task(process_tiff_background, temp_path, job_id)

    # Return job_id immediately to frontend
    return {"job_id": job_id, "status": "processing_started"}


@router.get("/status/{job_id}")
def check_status(job_id: str):
    """
    Optional: Return status of processing.
    For now, just a placeholder that always says 'processing'.
    """
    # You can enhance this later to track real-time progress
    return {"job_id": job_id, "status": "processing"}
