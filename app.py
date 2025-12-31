from fastapi import FastAPI, UploadFile, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
import os, uuid, json
from processor import process_tiff

app = FastAPI()

BASE_DIR = "jobs"
os.makedirs(BASE_DIR, exist_ok=True)

# ---------------------------
# Upload large TIFF (100MB+)
# ---------------------------
@app.post("/upload")
async def upload(file: UploadFile, bg: BackgroundTasks):
    if not file.filename.lower().endswith((".tif", ".tiff")):
        raise HTTPException(status_code=400, detail="Only TIFF files allowed")

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(BASE_DIR, job_id)
    os.makedirs(job_dir)

    tiff_path = os.path.join(job_dir, "input.tiff")

    # Stream upload → disk (NO RAM overload)
    with open(tiff_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            f.write(chunk)

    with open(os.path.join(job_dir, "status.json"), "w") as f:
        json.dump({"status": "UPLOADED"}, f)

    bg.add_task(process_tiff, job_dir)

    return {"job_id": job_id}

# ---------------------------
# Job status
# ---------------------------
@app.get("/status/{job_id}")
def status(job_id: str):
    status_file = os.path.join(BASE_DIR, job_id, "status.json")
    if not os.path.exists(status_file):
        raise HTTPException(status_code=404, detail="Job not found")

    with open(status_file) as f:
        return json.load(f)

# ---------------------------
# Heatmap result
# ---------------------------
@app.get("/result/{job_id}")
def result(job_id: str):
    heatmap_path = os.path.join(BASE_DIR, job_id, "heatmap.png")
    if not os.path.exists(heatmap_path):
        raise HTTPException(status_code=404, detail="Result not ready")

    return FileResponse(heatmap_path, media_type="image/png")
