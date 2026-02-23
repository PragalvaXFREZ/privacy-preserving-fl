import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, clients, inference, internal, metrics, training

app = FastAPI(
    title="Federated Learning Healthcare API",
    description="Privacy-Preserving Federated Learning for Healthcare",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(clients.router, prefix="/api")
app.include_router(training.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(inference.router, prefix="/api")
app.include_router(internal.router, prefix="/api")


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.on_event("startup")
def on_startup():
    """Create required directories on application startup."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(settings.MODEL_PATH) or "./models", exist_ok=True)
