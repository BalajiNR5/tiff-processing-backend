# app/processing.py
def process_tiff(file):
    return {
        "filename": file.filename,
        "status": "queued"
    }
