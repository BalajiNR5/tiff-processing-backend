from fastapi import FastAPI
from app.routes import router

app = FastAPI(
    title="Large TIFF Processing Backend",
    version="1.0"
)

app.include_router(router)

@app.get("/")
def health_check():
    return {"status": "running"}
