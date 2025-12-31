from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router

app = FastAPI(
    title="Large TIFF Processing Backend",
    version="1.0"
)

# --- CORS setup ---
# Allow your frontend (AI Studio) to call this backend
origins = [
    "*"  # For testing; later replace "*" with your AI Studio domain for security
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Health check endpoint
@app.get("/")
def health_check():
    return {"status": "running"}
