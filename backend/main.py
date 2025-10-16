import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from dotenv import load_dotenv

# Import API modules
from api.scan import router as scan_router
from api.organize import router as organize_router
from api.delete import router as delete_router
from api.virus_scan import router as virus_router
from api.ml_operations import router as ml_router
from api.logs import router as logs_router
from api.settings import router as settings_router

# Import utilities
from database.db import init_database
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logging
class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Hide logs for GET /api/status and GET /api/health
        return record.getMessage().find("GET /api/status") == -1 and record.getMessage().find("GET /api/health") == -1

# Add filter to uvicorn access logger
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

logger = setup_logger(__name__)

# Global status for frontend progress tracking
class GlobalStatus:
    def __init__(self):
        self.current_operation = None
        self.progress = 0
        self.message = ""
        self.is_busy = False
        self.last_scan_results = {}
        self.ml_model_status = {"trained": False, "accuracy": 0.0}
    
    def update(self, operation: str, progress: int, message: str, is_busy: bool = True):
        self.current_operation = operation
        self.progress = progress
        self.message = message
        self.is_busy = is_busy
        logger.info(f"Status update: {operation} - {progress}% - {message}")

    def complete(self, message: str = "Operation completed"):
        self.progress = 100
        self.message = message
        self.is_busy = False
        logger.info(f"Operation completed: {message}")

# Global status instance
app_status = GlobalStatus()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application on startup"""
    logger.info("Starting Intelligent File Organizer backend...")
    
    # Initialize database
    await init_database()
    
    # Create necessary directories
    os.makedirs("quarantine", exist_ok=True)
    os.makedirs("backend/ml_model", exist_ok=True)
    
    logger.info("Backend initialization complete")
    yield
    logger.info("Shutting down backend...")

# Create FastAPI app
app = FastAPI(
    title="Intelligent File Organizer API",
    description="ML-powered file organization and malware scanning system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(scan_router, prefix="/api", tags=["scanning"])
app.include_router(organize_router, prefix="/api", tags=["organization"])
app.include_router(delete_router, prefix="/api", tags=["deletion"])
app.include_router(virus_router, prefix="/api", tags=["security"])
app.include_router(ml_router, prefix="/api/ml", tags=["machine-learning"])
app.include_router(logs_router, prefix="/api", tags=["logs"])
app.include_router(settings_router, prefix="/api", tags=["settings"])

# Status endpoint
@app.get("/api/status")
async def get_status():
    """Get current application status"""
    return {
        "current_operation": app_status.current_operation,
        "progress": app_status.progress,
        "message": app_status.message,
        "is_busy": app_status.is_busy,
        "last_scan_results": app_status.last_scan_results,
        "ml_model_status": app_status.ml_model_status
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Intelligent File Organizer API is running",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Intelligent File Organizer API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Make app_status available to other modules
app.state.status = app_status

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )