# app/main.py
from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="TIFF Image Processing Backend")

app.include_router(router)

@app.get("/")
def health_check():
    return {"status": "running"}
