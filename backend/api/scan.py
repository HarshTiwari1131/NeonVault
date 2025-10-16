from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from pathlib import Path
import asyncio
import logging
from typing import List, Dict, Optional
import time
import csv
from datetime import datetime

from utils.file_utils import FileUtils, FileMetadata
from utils.speech_notifications import notify_scan_complete
from utils.email_notifications import send_notification_email
from database.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

class ScanRequest(BaseModel):
    folder_path: str
    recursive: bool = True
    max_files: Optional[int] = None
    export_csv: bool = False
    csv_path: Optional[str] = None

class ScanResponse(BaseModel):
    success: bool
    message: str
    results: Dict
    duration: float

@router.post("/scan", response_model=ScanResponse)
async def scan_folder(request: ScanRequest, background_tasks: BackgroundTasks):
    """Scan folder and analyze files"""
    start_time = time.time()
    
    try:
        folder_path = Path(request.folder_path)
        
        if not folder_path.exists():
            raise HTTPException(status_code=400, detail="Folder does not exist")
        
        if not folder_path.is_dir():
            raise HTTPException(status_code=400, detail="Path is not a directory")
        
        logger.info(f"Starting scan of folder: {folder_path}")
        
        # Update global status
        from main import app_status
        app_status.update("scanning", 0, f"Scanning {folder_path}", True)
        
        # Initialize counters
        file_count = 0
        total_size = 0
        categories = {}
        file_list = []
        
        # Scan files
        # Exclude protected/system directories on Windows to reduce permission errors during drive scans
        exclude = ['System Volume Information', '$Recycle.Bin', 'Windows\\WinSxS', 'Windows\\System32\\DriverStore']
        async for metadata in FileUtils.scan_directory(folder_path, request.recursive, exclude_dirs=exclude):
            file_count += 1
            total_size += metadata.size
            
            # Update progress every 10 files
            if file_count % 10 == 0:
                app_status.update("scanning", 
                                min(90, int(file_count / 100 * 90)), 
                                f"Processed {file_count} files")
            
            # Categorize file
            category = FileUtils.get_file_category_by_extension(metadata.extension)
            if category not in categories:
                categories[category] = {"count": 0, "size": 0}
            categories[category]["count"] += 1
            categories[category]["size"] += metadata.size
            
            # Add to file list
            file_metadata = metadata.to_dict()
            file_metadata["category"] = category
            file_list.append(file_metadata)
            
            # Break if max files reached
            if request.max_files and file_count >= request.max_files:
                break
        
        duration = time.time() - start_time
        
        # Calculate total disk size for storage analyzed percent
        try:
            if folder_path.drive:
                import shutil
                total_disk_size = shutil.disk_usage(folder_path.drive).total
            else:
                import shutil
                total_disk_size = shutil.disk_usage(str(folder_path)).total
        except Exception as e:
            logger.error(f"Error getting disk size: {e}")
            total_disk_size = 0
        storage_analyzed_percent = (total_size / total_disk_size * 100) if total_disk_size else 0

        # Prepare results (return all files, no limit)
        results = {
            "folder_path": str(folder_path),
            "total_files": file_count,
            "total_size": total_size,
            "total_size_formatted": FileUtils.format_file_size(total_size),
            "categories": categories,
            "scan_duration": duration,
            "files": file_list,  # Return all files
            "total_disk_size": total_disk_size,
            "storage_analyzed_percent": storage_analyzed_percent
        }

        # Optional CSV export of full file list
        if request.export_csv:
            try:
                logs_dir = Path("logs")
                logs_dir.mkdir(exist_ok=True)
                if request.csv_path:
                    csv_out = Path(request.csv_path)
                    if not csv_out.is_absolute():
                        csv_out = logs_dir / request.csv_path
                else:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    drive_tag = folder_path.drive.replace(':','') if hasattr(folder_path, 'drive') else folder_path.name
                    csv_out = logs_dir / f"scan_{drive_tag}_{ts}.csv"

                # Write header and rows
                headers = [
                    "path","name","extension","size","mime_type","modified_time",
                    "category","entropy","hash_md5"
                ]
                with open(csv_out, mode="w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                    for item in file_list:
                        writer.writerow({
                            "path": item.get("path"),
                            "name": item.get("name"),
                            "extension": item.get("extension"),
                            "size": item.get("size", 0),
                            "mime_type": item.get("mime_type"),
                            "modified_time": item.get("modified_time"),
                            "category": item.get("category"),
                            "entropy": item.get("entropy", 0.0),
                            "hash_md5": item.get("hash_md5", "")
                        })

                results["csv_path"] = str(csv_out)
            except Exception as e:
                logger.error(f"CSV export failed: {e}")
                results["csv_error"] = str(e)
        
        # Store results in global status
        app_status.last_scan_results = results
        app_status.complete(f"Scan completed: {file_count} files processed")
        
        # Log to database
        db = await get_db()
        await db.log_scan_result(
            str(folder_path), file_count, total_size, categories, duration
        )
        await db.log_action("INFO", "folder_scan", f"Scanned {folder_path}", f"{file_count} files found")
        
        # Speech notification
        background_tasks.add_task(notify_scan_complete, file_count, duration)
        
        # Email notification
        subject = f"Scan Complete: {file_count} files in {folder_path}"
        body = f"""
        A scan of the folder '{folder_path}' has completed.

        - Total files processed: {file_count}
        - Total size: {results['total_size_formatted']}
        - Duration: {duration:.2f} seconds

        Category breakdown:
        """
        for category, data in categories.items():
            body += f"- {category.capitalize()}: {data['count']} files\n"
        
        background_tasks.add_task(send_notification_email, subject, body)

        logger.info(f"Scan completed: {file_count} files in {duration:.2f}s")
        
        return ScanResponse(
            success=True,
            message=f"Successfully scanned {file_count} files",
            results=results,
            duration=duration
        )
        
    except Exception as e:
        logger.error(f"Scan error: {e}")
        app_status.complete(f"Scan failed: {str(e)}")
        
        # Log error to database
        db = await get_db()
        await db.log_action("ERROR", "folder_scan", f"Failed to scan {request.folder_path}", str(e))
        
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scan/progress")
async def get_scan_progress():
    """Get current scan progress"""
    from main import app_status
    return {
        "current_operation": app_status.current_operation,
        "progress": app_status.progress,
        "message": app_status.message,
        "is_busy": app_status.is_busy
    }

@router.get("/scan/results")
async def get_last_scan_results():
    """Get results from the last scan"""
    from main import app_status
    
    if not app_status.last_scan_results:
        raise HTTPException(status_code=404, detail="No scan results available")
    
    return app_status.last_scan_results

@router.get("/scan/stats")
async def get_scan_statistics():
    """Get scan statistics from database"""
    try:
        db = await get_db()
        stats = await db.get_scan_stats(30)  # Last 30 days
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting scan stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))