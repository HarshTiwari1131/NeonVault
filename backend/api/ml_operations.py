from fastapi import APIRouter, HTTPException, BackgroundTasks 
from pydantic import BaseModel
import asyncio
import logging
from typing import List, Dict, Optional
import time
from pathlib import Path

from ml_model.train_model import ml_trainer
from ml_model.predictor import ml_predictor
from utils.file_utils import FileUtils
from utils.speech_notifications import notify_training_complete
from database.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

class TrainRequest(BaseModel):
    data_source: str = "last_scan"  # "last_scan", "folder_path", "database"
    folder_path: Optional[str] = None
    min_files: int = 100

class TrainResponse(BaseModel):
    success: bool
    message: str
    results: Dict
    duration: float

class PredictRequest(BaseModel):
    file_metadata: Dict

class PredictResponse(BaseModel):
    category: str
    confidence: float
    method: str
    probabilities: Dict

@router.post("/train", response_model=TrainResponse)
async def train_ml_model(request: TrainRequest, background_tasks: BackgroundTasks):
    """Train the ML model with file data"""
    start_time = time.time()
    
    try:
        # Update global status
        from main import app_status
        app_status.update("ml_training", 0, "Preparing training data", True)
        
        # Collect training data
        training_data = []
        
        if request.data_source == "last_scan":
            # Use data from last scan
            if not app_status.last_scan_results:
                raise HTTPException(status_code=400, detail="No recent scan data available")
            
            training_data = app_status.last_scan_results.get("files", [])
            
        elif request.data_source == "folder_path":
            if not request.folder_path:
                raise HTTPException(status_code=400, detail="folder_path required for folder data source")
            
            folder_path = Path(request.folder_path)
            if not folder_path.exists():
                raise HTTPException(status_code=400, detail="Folder does not exist")
            
            app_status.update("ml_training", 10, f"Scanning {folder_path} for training data")
            
            # Collect file metadata
            async for metadata in FileUtils.scan_directory(folder_path, recursive=True):
                file_data = metadata.to_dict()
                training_data.append(file_data)
                
                if len(training_data) % 50 == 0:
                    progress = min(50, 10 + int(len(training_data) / 500 * 40))
                    app_status.update("ml_training", progress, f"Collected {len(training_data)} training samples")
        
        elif request.data_source == "database":
            # Use historical data from database
            app_status.update("ml_training", 10, "Loading training data from database")
            # Implementation would load from database scan history
            # For now, use last scan data as fallback
            if app_status.last_scan_results:
                training_data = app_status.last_scan_results.get("files", [])
        
        # Validate training data
        if len(training_data) < request.min_files:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient training data. Need at least {request.min_files} files, got {len(training_data)}"
            )
        
        app_status.update("ml_training", 60, f"Training model with {len(training_data)} samples")
        
        # Train the model
        training_result = await ml_trainer.train_model(training_data)
        
        if not training_result["success"]:
            raise HTTPException(status_code=500, detail=f"Training failed: {training_result.get('error', 'Unknown error')}")
        
        # Update global ML model status
        app_status.ml_model_status = {
            "trained": True,
            "accuracy": training_result["accuracy"],
            "training_samples": training_result["training_samples"],
            "features_count": training_result["features_count"],
            "model_version": training_result["model_version"]
        }
        
        duration = time.time() - start_time
        
        # Log to database
        db = await get_db()
        await db.log_ml_training(
            training_result["accuracy"],
            training_result["training_duration"],
            training_result["features_count"],
            training_result["model_version"]
        )
        
        await db.log_action(
            "INFO",
            "ml_training",
            f"Trained ML model with {len(training_data)} samples",
            f"Accuracy: {training_result['accuracy']:.3f}, Duration: {training_result['training_duration']:.2f}s"
        )
        
        # Update status
        message = f"Model training completed with {training_result['accuracy']:.1%} accuracy"
        app_status.complete(message)
        
        # Speech notification
        background_tasks.add_task(notify_training_complete, training_result['accuracy'] * 100)
        
        logger.info(f"ML training completed: {training_result['accuracy']:.3f} accuracy in {duration:.2f}s")
        
        return TrainResponse(
            success=True,
            message=message,
            results=training_result,
            duration=duration
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ML training error: {e}")
        app_status.complete(f"ML training failed: {str(e)}")
        
        # Log error
        db = await get_db()
        await db.log_action("ERROR", "ml_training", "ML training failed", str(e))
        
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict", response_model=PredictResponse)
async def predict_file_category(request: PredictRequest):
    """Predict file category using ML model"""
    try:
        if not ml_predictor.is_model_available():
            raise HTTPException(status_code=503, detail="ML model not available. Please train the model first.")
        
        result = ml_predictor.predict_category(request.file_metadata)
        
        return PredictResponse(
            category=result["category"],
            confidence=result["confidence"],
            method=result["method"],
            probabilities=result["probabilities"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ML prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model/info")
async def get_model_info():
    """Get information about the current ML model"""
    try:
        # Get model info from trainer
        model_info = ml_trainer.get_model_info()
        
        # Add predictor status
        model_info["predictor_loaded"] = ml_predictor.is_model_available()
        
        # Get feature importance if available
        if ml_predictor.is_model_available():
            model_info["feature_importance"] = ml_predictor.get_feature_importance()
        
        return {
            "success": True,
            "model_info": model_info
        }
        
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/model/reload")
async def reload_model():
    """Reload the ML model from disk"""
    try:
        success = ml_predictor.load_model()
        
        if success:
            # Update global status
            from main import app_status
            model_info = ml_trainer.get_model_info()
            if model_info.get("trained"):
                metadata = model_info.get("metadata", {})
                app_status.ml_model_status = {
                    "trained": True,
                    "accuracy": metadata.get("accuracy", 0.0),
                    "training_samples": metadata.get("training_samples", 0),
                    "features_count": metadata.get("features_count", 0),
                    "model_version": metadata.get("model_version", "unknown")
                }
            
            return {"success": True, "message": "Model reloaded successfully"}
        else:
            return {"success": False, "message": "Failed to reload model"}
            
    except Exception as e:
        logger.error(f"Error reloading model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model/performance")
async def get_model_performance():
    """Get ML model performance metrics"""
    try:
        db = await get_db()
        
        # Get training history from database
        # This would be implemented to query ml_training_history table
        performance_data = {
            "current_accuracy": 0.0,
            "training_history": [],
            "feature_importance": {},
            "prediction_stats": {
                "total_predictions": 0,
                "avg_confidence": 0.0,
                "category_distribution": {}
            }
        }
        
        # Get current model info
        model_info = ml_trainer.get_model_info()
        if model_info.get("trained"):
            metadata = model_info.get("metadata", {})
            performance_data["current_accuracy"] = metadata.get("accuracy", 0.0)
        
        # Get feature importance
        if ml_predictor.is_model_available():
            performance_data["feature_importance"] = ml_predictor.get_feature_importance()
        
        return {
            "success": True,
            "performance": performance_data
        }
        
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/anomaly/detect")
async def detect_anomaly(request: PredictRequest):
    """Detect if a file is anomalous using ML"""
    try:
        if not ml_predictor.is_model_available():
            raise HTTPException(status_code=503, detail="ML model not available")
        
        anomaly_score = ml_predictor.predict_anomaly(request.file_metadata)
        
        return {
            "success": True,
            "anomaly_score": anomaly_score,
            "is_anomalous": anomaly_score > 0.7,
            "risk_level": "high" if anomaly_score > 0.8 else "medium" if anomaly_score > 0.5 else "low"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Anomaly detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))