from fastapi import FastAPI
from app.api.optimizer_api import router as optimizer_router
from app.core.config import get_settings
from app.core.database import init_db, engine
import uvicorn
from contextlib import asynccontextmanager

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database connection pool on startup and clean up on shutdown."""
    init_db()
    yield
    engine.dispose()

app = FastAPI(
    title="DB Optimizer API",
    description="AI-powered database query optimization service",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(optimizer_router)

@app.get("/")
def root():
    return {"message": "Welcome to the DB Optimizer API!"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_DEBUG
    ) 


