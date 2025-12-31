from fastapi import APIRouter, UploadFile, BackgroundTasks
from app.processing import process_tiff_background, progress_dict, heatmap_dict
import uuid
import os
import numpy as np
from PIL import Image

router = APIRouter()

# Ensure tmp directory exists
TEMP_DIR = "tmp"
os.makedirs(TEMP_DIR, exist_ok=True)


@router.post("/process")
async def process_tiff(file: UploadFile, background_tasks: BackgroundTasks):
    """
    Upload TIFF file and start background processing.
    Returns a job_id immediately.
    """
    job_id = str(uuid.uuid4())
    temp_path = os.path.join(TEMP_DIR, f"{job_id}.tiff")

    # Save uploaded file
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    # Launch background processing
    background_tasks.add_task(process_tiff_background, temp_path, job_id)

    return {"job_id": job_id, "status": "processing_started"}


@router.get("/status/{job_id}")
def check_status(job_id: str):
    """
    Returns processing progress percentage (0-100) or error (-1).
    """
    progress = progress_dict.get(job_id, 0)
    status = "completed" if progress == 100 else ("error" if progress == -1 else "processing")
    return {"job_id": job_id, "status": status, "progress": progress}


@router.get("/heatmap/{job_id}")
def get_heatmap(job_id: str):
    """
    Returns a downsampled heatmap PNG for the frontend.
    """
    tile_means = heatmap_dict.get(job_id)
    if tile_means is None:
        return {"error": "Heatmap not ready or job_id invalid"}

    # Normalize to 0-255
    normalized = ((tile_means - tile_means.min()) / (tile_means.ptp() + 1e-5) * 255).astype(np.uint8)
    img = Image.fromarray(normalized)
    img_path = os.path.join(TEMP_DIR, f"{job_id}_heatmap.png")
    img.save(img_path)
    return {"heatmap_url": f"/tmp/{job_id}_heatmap.png"}
