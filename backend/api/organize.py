from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from pathlib import Path
import asyncio
import logging
from typing import List, Dict, Optional
import time

from utils.file_utils import FileUtils
from ml_model.predictor import ml_predictor
from utils.speech_notifications import notify_organization_complete
from utils.email_notifications import send_notification_email
from database.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

def normalize_category_name(category: str) -> str:
    """Normalize category names to match expected folder structure"""
    category_mapping = {
        'images': 'Images',
        'videos': 'Videos', 
        'audio': 'Audio',
        'documents': 'Documents',
        'archives': 'Archives',
        'code': 'Code',
        'spreadsheets': 'Spreadsheets',
        'presentations': 'Presentations',
        'executables': 'Executables',
        'others': 'Others',
        'suspicious': 'Others',  # Map suspicious files to Others instead of creating separate folder
        'unknown': 'Others',
        'temporary': 'Others',   # Map temporary files to Others
        'empty': 'Others'        # Map empty files to Others
    }
    
    # Handle any unexpected categories by normalizing to Others
    normalized = category_mapping.get(category.lower(), 'Others')
    return normalized

class OrganizeRequest(BaseModel):
    folder_path: str
    destination_base: str = "organized"
    dry_run: bool = False
    use_ml: bool = True
    create_dated_folders: bool = False

class OrganizeRule(BaseModel):
    extensions: List[str]
    destination_folder: str
    use_ml_prediction: bool = True

class OrganizeResponse(BaseModel):
    success: bool
    message: str
    results: Dict
    duration: float

@router.post("/organize", response_model=OrganizeResponse)
async def organize_files(request: OrganizeRequest, background_tasks: BackgroundTasks):
    """Organize files using ML predictions and rules"""
    start_time = time.time()
    
    try:
        source_path = Path(request.folder_path)
        
        if not source_path.exists() or not source_path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid source folder")
        
        logger.info(f"Starting organization: {source_path} -> {request.destination_base}")
        
        # Update global status
        from main import app_status
        app_status.update("organizing", 0, f"Organizing files from {source_path}", True)
        
        # Initialize counters
        moved_count = 0
        failed_count = 0
        category_counts = {}
        operations = []
        
        # Scan directory once to get all files
        files_to_process = [
            metadata async for metadata in FileUtils.scan_directory(source_path, recursive=True)
        ]
        total_files = len(files_to_process)
        
        if total_files == 0:
            app_status.complete("No files found to organize.")
            return OrganizeResponse(
                success=True,
                message="No files found to organize in the specified directory.",
                results={},
                duration=0
            )

        # Scan and organize files
        file_count = 0
        for metadata in files_to_process:
            file_count += 1
            
            # Calculate real progress percentage and update more frequently
            progress = int((file_count / total_files) * 100)
            # Update status every 10 files or every percentage point
            if file_count % 10 == 0 or progress != getattr(app_status, '_last_progress', -1):
                app_status.update("organizing", progress, f"Processing file {file_count} of {total_files}")
                app_status._last_progress = progress
            
            try:
                # Determine destination category
                # Temporary fix: Force rule-based categorization since ML model may be incorrectly trained
                if False and request.use_ml and ml_predictor.is_model_available():
                    prediction = ml_predictor.predict_category(metadata.to_dict())
                    raw_category = prediction['category']
                    confidence = prediction['confidence']
                    method = "ml_prediction"
                    # Debug log ML predictions
                    logger.info(f"ML prediction for {metadata.name} (ext: {metadata.extension}): {raw_category} (confidence: {confidence:.2f})")
                else:
                    raw_category = FileUtils.get_file_category_by_extension(metadata.extension)
                    confidence = 0.8
                    method = "rule_based"
                    # Debug log rule-based categorization
                    logger.info(f"Rule-based category for {metadata.name} (ext: {metadata.extension}): {raw_category}")

                # Normalize category name to match expected categories
                category = normalize_category_name(raw_category)

                # Log category mapping for debugging
                if raw_category != category.lower():
                    logger.info(f"Mapped category '{raw_category}' -> '{category}' for file {metadata.name}")

                # Build destination path
                dest_base = Path(request.destination_base)

                if request.create_dated_folders and metadata.modified_time:
                    date_folder = metadata.modified_time.strftime("%Y-%m")
                    dest_folder = dest_base / date_folder / category
                else:
                    dest_folder = dest_base / category

                dest_file = dest_folder / metadata.name

                # Attempt to move file
                success = await FileUtils.move_file(
                    metadata.path, dest_file, dry_run=request.dry_run
                )

                if success:
                    moved_count += 1
                    if category not in category_counts:
                        category_counts[category] = 0
                    category_counts[category] += 1

                    # Log to database
                    db = await get_db()
                    await db.log_move(
                        str(metadata.path),
                        str(dest_file),
                        metadata.name,
                        metadata.size,
                        category,
                        confidence,
                        request.dry_run
                    )

                    operations.append({
                        "source": str(metadata.path),
                        "destination": str(dest_file),
                        "category": category,
                        "confidence": confidence,
                        "method": method,
                        "dry_run": request.dry_run
                    })
                else:
                    failed_count += 1
                    logger.warning(f"Failed to move {metadata.path}")

            except Exception as e:
                failed_count += 1
                logger.error(f"Error processing {metadata.path}: {e}")
        
        duration = time.time() - start_time

        # Prepare results
        results = {
            "source_folder": str(source_path),
            "destination_base": request.destination_base,
            "total_processed": file_count,
            "moved_count": moved_count,
            "failed_count": failed_count,
            "dry_run": request.dry_run,
            "category_counts": category_counts,
            "duration": duration,
            "operations": operations[:50]  # Limit response size
        }

        # Update status
        if request.dry_run:
            message = f"Dry run completed: {moved_count} files would be organized"
        else:
            message = f"Organization completed: {moved_count} files organized"

        app_status.complete(message)

        # Log to database
        db = await get_db()
        await db.log_action(
            "INFO", 
            "file_organization", 
            f"Organized {moved_count} files from {source_path}",
            f"Categories: {category_counts}"
        )
        # Speech notification
        background_tasks.add_task(notify_organization_complete, moved_count)
        
        # Email notification
        subject = f"Organization Complete: {moved_count} files organized"
        body = f"""
        File organization for the folder '{source_path}' has completed.

        - Files moved: {moved_count}
        - Files failed: {failed_count}
        - Duration: {duration:.2f} seconds
        - Dry run: {request.dry_run}

        Category breakdown:
        """
        for category, count in category_counts.items():
            body += f"- {category.capitalize()}: {count} files\n"
            
        background_tasks.add_task(send_notification_email, subject, body)
        
        logger.info(f"Organization completed: {moved_count} files in {duration:.2f}s")
        
        return OrganizeResponse(
            success=True,
            message=message,
            results=results,
            duration=duration
        )
        
    except Exception as e:
        logger.error(f"Organization error: {e}")
        app_status.complete(f"Organization failed: {str(e)}")
        
        # Log error
        db = await get_db()
        await db.log_action("ERROR", "file_organization", f"Failed to organize {request.folder_path}", str(e))
        
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/organize/categories")
async def get_organization_categories():
    """Get available organization categories"""
    categories = {
        "documents": {
            "name": "Documents",
            "extensions": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"],
            "description": "Text documents and PDFs"
        },
        "images": {
            "name": "Images",
            "extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".svg"],
            "description": "Image files"
        },
        "videos": {
            "name": "Videos", 
            "extensions": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"],
            "description": "Video files"
        },
        "audio": {
            "name": "Audio",
            "extensions": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma"],
            "description": "Audio files"
        },
        "archives": {
            "name": "Archives",
            "extensions": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
            "description": "Compressed archives"
        },
        "code": {
            "name": "Code",
            "extensions": [".py", ".js", ".html", ".css", ".cpp", ".java", ".c"],
            "description": "Source code files"
        },
        "spreadsheets": {
            "name": "Spreadsheets",
            "extensions": [".xlsx", ".xls", ".csv", ".ods"],
            "description": "Spreadsheet files"
        },
        "presentations": {
            "name": "Presentations",
            "extensions": [".pptx", ".ppt", ".odp"],
            "description": "Presentation files"
        },
        "executables": {
            "name": "Executables",
            "extensions": [".exe", ".msi", ".dmg", ".deb", ".rpm"],
            "description": "Executable files"
        },
        "others": {
            "name": "Others",
            "extensions": [],
            "description": "Uncategorized files"
        }
    }
    
    return {"categories": categories}

@router.get("/organize/history")
async def get_organization_history(limit: int = 50):
    """Get recent file organization history"""
    try:
        db = await get_db()
        moves = await db.get_recent_moves(limit)
        
        return {
            "success": True,
            "moves": moves
        }
        
    except Exception as e:
        logger.error(f"Error getting organization history: {e}")
        raise HTTPException(status_code=500, detail=str(e))