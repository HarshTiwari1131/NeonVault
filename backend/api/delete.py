from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from pathlib import Path
import asyncio
import logging
from typing import List, Dict, Optional
import time
from datetime import datetime, timedelta


from utils.file_utils import FileUtils
from utils.speech_notifications import notify_deletion_complete
from utils.email_notifications import send_notification_email
from database.db import get_db


logger = logging.getLogger(__name__)
router = APIRouter()

class DeleteRequest(BaseModel):
    folder_path: str
    rules: Dict = {}  # {"extensions": [".tmp"], "older_than_days": 30, "size_below_kb": 1}
    dry_run: bool = True
    permanent: bool = False

class DeleteResponse(BaseModel):
    success: bool
    message: str
    results: Dict
    duration: float

@router.post("/delete", response_model=DeleteResponse)
async def delete_files(request: DeleteRequest, background_tasks: BackgroundTasks):
    """Delete files based on rules"""
    start_time = time.time()
    source_path = Path(request.folder_path)
    try:
        from main import app_status
        # If the path is a file, delete it directly
        if source_path.exists() and source_path.is_file():
            logger.info(f"Deleting single file: {source_path}")
            app_status.update("deleting", 0, f"Deleting file {source_path}", True)
            deleted_count = 0
            total_size_deleted = 0
            files_analyzed = 1
            files_to_delete = [{
                "path": str(source_path),
                "name": source_path.name,
                "size": source_path.stat().st_size,
                "modified_time": datetime.fromtimestamp(source_path.stat().st_mtime),
                "reasons": ["direct file delete"]
            }]
            try:
                if not request.dry_run:
                    success = await FileUtils.delete_file(source_path, request.permanent)
                    if success:
                        deleted_count = 1
                        total_size_deleted = source_path.stat().st_size if source_path.exists() else 0
                        db = await get_db()
                        await db.log_action(
                            "INFO",
                            "file_deletion",
                            f"Deleted {source_path.name}",
                            f"Reasons: direct file delete, Size: {FileUtils.format_file_size(files_to_delete[0]['size'])}"
                        )
                else:
                    deleted_count = 1
                    total_size_deleted = files_to_delete[0]["size"]
            except Exception as e:
                logger.error(f"Error deleting {source_path}: {e}")
            duration = time.time() - start_time
            results = {
                "folder_path": str(source_path.parent),
                "rules_applied": request.rules,
                "files_analyzed": files_analyzed,
                "files_deleted": deleted_count,
                "total_size_deleted": total_size_deleted,
                "total_size_deleted_formatted": FileUtils.format_file_size(total_size_deleted),
                "dry_run": request.dry_run,
                "permanent": request.permanent,
                "duration": duration,
                "deleted_files": files_to_delete[:20]
            }
            message = f"Dry run completed: 1 file would be deleted" if request.dry_run else f"Deletion completed: 1 file deleted"
            app_status.complete(message)
            db = await get_db()
            await db.log_action(
                "INFO",
                "bulk_deletion",
                f"Deleted {deleted_count} file from {source_path}",
                f"Rules: {request.rules}, Size freed: {FileUtils.format_file_size(total_size_deleted)}"
            )
            background_tasks.add_task(notify_deletion_complete, deleted_count, request.dry_run)
            logger.info(f"Deletion completed: {deleted_count} file in {duration:.2f}s")
            return DeleteResponse(
                success=True,
                message=message,
                results=results,
                duration=duration
            )
        # If the path is a directory, use rules-based deletion (existing logic)
        if not source_path.exists() or not source_path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid source folder or file")
        logger.info(f"Starting deletion with rules: {request.rules}")
        app_status.update("deleting", 0, f"Analyzing files for deletion in {source_path}", True)
        extensions_to_delete = request.rules.get("extensions", [])
        older_than_days = request.rules.get("older_than_days", None)
        size_below_kb = request.rules.get("size_below_kb", None)
        cutoff_date = None
        if older_than_days:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
        deleted_count = 0
        total_size_deleted = 0
        files_analyzed = 0
        files_to_delete = []
        exclude = ['System Volume Information', '$Recycle.Bin', 'Windows\\WinSxS', 'Windows\\System32\\DriverStore']
        async for metadata in FileUtils.scan_directory(source_path, recursive=True, exclude_dirs=exclude):
            files_analyzed += 1
            if files_analyzed % 10 == 0:
                progress = min(80, int(files_analyzed / 100 * 80))
                app_status.update("deleting", progress, f"Analyzed {files_analyzed} files")
            should_delete = False
            reasons = []
            if extensions_to_delete and metadata.extension.lower() in [ext.lower() for ext in extensions_to_delete]:
                should_delete = True
                reasons.append(f"extension {metadata.extension}")
            if older_than_days and cutoff_date and metadata.modified_time and metadata.modified_time < cutoff_date:
                should_delete = True
                age_days = (datetime.now() - metadata.modified_time).days
                reasons.append(f"older than {age_days} days")
            if size_below_kb and metadata.size < (size_below_kb * 1024):
                should_delete = True
                reasons.append(f"size {FileUtils.format_file_size(metadata.size)}")
            if should_delete:
                files_to_delete.append({
                    "path": metadata.path,
                    "name": metadata.name,
                    "size": metadata.size,
                    "modified_time": metadata.modified_time,
                    "reasons": reasons
                })
        app_status.update("deleting", 85, f"Processing {len(files_to_delete)} files for deletion")
        for i, file_info in enumerate(files_to_delete):
            if i % 5 == 0:
                progress = 85 + int((i / len(files_to_delete)) * 15)
                app_status.update("deleting", progress, f"Deleting file {i+1} of {len(files_to_delete)}")
            try:
                file_path = Path(file_info["path"])
                if not request.dry_run:
                    success = await FileUtils.delete_file(file_path, request.permanent)
                    if success:
                        deleted_count += 1
                        total_size_deleted += file_info["size"]
                        db = await get_db()
                        await db.log_action(
                            "INFO",
                            "file_deletion",
                            f"Deleted {file_info['name']}",
                            f"Reasons: {', '.join(file_info['reasons'])}, Size: {FileUtils.format_file_size(file_info['size'])}"
                        )
                else:
                    deleted_count += 1
                    total_size_deleted += file_info["size"]
            except Exception as e:
                logger.error(f"Error deleting {file_info['path']}: {e}")
        duration = time.time() - start_time
        results = {
            "folder_path": str(source_path),
            "rules_applied": request.rules,
            "files_analyzed": files_analyzed,
            "files_deleted": deleted_count,
            "total_size_deleted": total_size_deleted,
            "total_size_deleted_formatted": FileUtils.format_file_size(total_size_deleted),
            "dry_run": request.dry_run,
            "permanent": request.permanent,
            "duration": duration,
            "deleted_files": files_to_delete[:20]
        }
        if request.dry_run:
            message = f"Dry run completed: {deleted_count} files would be deleted"
        else:
            message = f"Deletion completed: {deleted_count} files deleted"
        app_status.complete(message)
        db = await get_db()
        await db.log_action(
            "INFO",
            "bulk_deletion",
            f"Deleted {deleted_count} files from {source_path}",
            f"Rules: {request.rules}, Size freed: {FileUtils.format_file_size(total_size_deleted)}"
        )
        background_tasks.add_task(notify_deletion_complete, deleted_count, request.dry_run)
        
        # Email notification
        subject = f"Deletion Complete: {deleted_count} files removed"
        body = f"""
        A file deletion task has completed for the folder '{source_path}'.

        - Files deleted: {deleted_count}
        - Total size freed: {results['total_size_deleted_formatted']}
        - Duration: {duration:.2f} seconds
        - Dry run: {request.dry_run}
        - Permanent: {request.permanent}

        Rules applied:
        {request.rules}
        """
        background_tasks.add_task(send_notification_email, subject, body)

        logger.info(f"Deletion completed: {deleted_count} files in {duration:.2f}s")
        return DeleteResponse(
            success=True,
            message=message,
            results=results,
            duration=duration
        )
    except Exception as e:
        import traceback
        error_msg = str(e) or "Unknown error during deletion."
        tb = traceback.format_exc()
        logger.error(f"Deletion error: {error_msg}\nTraceback:\n{tb}")
        from main import app_status
        app_status.complete(f"Deletion failed: {error_msg}")
        # Log error
        db = await get_db()
        await db.log_action("ERROR", "bulk_deletion", f"Failed to delete from {request.folder_path}", error_msg + "\n" + tb)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/delete/preview")
async def preview_deletion(
    folder_path: str,
    extensions: Optional[str] = None,
    older_than_days: Optional[int] = None,
    size_below_kb: Optional[int] = None
):
    """Preview files that would be deleted by rules"""
    try:
        source_path = Path(folder_path)
        
        if not source_path.exists() or not source_path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid source folder")
        
        # Parse rules
        extensions_list = extensions.split(',') if extensions else []
        cutoff_date = None
        if older_than_days:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
        
        files_to_delete = []
        total_size = 0
        
        # Scan and apply rules
        exclude = ['System Volume Information', '$Recycle.Bin', 'Windows\\WinSxS', 'Windows\\System32\\DriverStore']
        async for metadata in FileUtils.scan_directory(source_path, recursive=True, exclude_dirs=exclude):
            should_delete = False
            reasons = []
            
            # Check rules
            if extensions_list and metadata.extension.lower() in [ext.lower().strip() for ext in extensions_list]:
                should_delete = True
                reasons.append(f"extension {metadata.extension}")
            
            if older_than_days and cutoff_date and metadata.modified_time and metadata.modified_time < cutoff_date:
                should_delete = True
                age_days = (datetime.now() - metadata.modified_time).days
                reasons.append(f"older than {age_days} days")
            
            if size_below_kb and metadata.size < (size_below_kb * 1024):
                should_delete = True
                reasons.append(f"size {FileUtils.format_file_size(metadata.size)}")
            
            if should_delete:
                files_to_delete.append({
                    "name": metadata.name,
                    "path": str(metadata.path),
                    "size": metadata.size,
                    "size_formatted": FileUtils.format_file_size(metadata.size),
                    "modified_time": metadata.modified_time.isoformat() if metadata.modified_time else None,
                    "reasons": reasons
                })
                total_size += metadata.size
        
        return {
            "success": True,
            "preview": {
                "folder_path": str(source_path),
                "files_to_delete": len(files_to_delete),
                "total_size": total_size,
                "total_size_formatted": FileUtils.format_file_size(total_size),
                "files": files_to_delete[:100]  # Limit to first 100 files
            }
        }
        
    except Exception as e:
        logger.error(f"Preview deletion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/delete/rules")
async def get_deletion_rules():
    """Get predefined deletion rule templates"""
    templates = {
        "temp_files": {
            "name": "Temporary Files",
            "description": "Remove temporary and cache files",
            "rules": {
                "extensions": [".tmp", ".temp", ".cache", ".log", ".bak"]
            }
        },
        "old_downloads": {
            "name": "Old Downloads",
            "description": "Remove files older than 90 days from Downloads",
            "rules": {
                "older_than_days": 90
            }
        },
        "small_files": {
            "name": "Small Files",
            "description": "Remove files smaller than 1KB",
            "rules": {
                "size_below_kb": 1
            }
        },
        "system_junk": {
            "name": "System Junk",
            "description": "Remove system temporary files and thumbnails",
            "rules": {
                "extensions": [".tmp", ".temp", ".thumbs.db", ".ds_store", "~$"]
            }
        },
        "old_logs": {
            "name": "Old Log Files", 
            "description": "Remove log files older than 30 days",
            "rules": {
                "extensions": [".log", ".trace"],
                "older_than_days": 30
            }
        }
    }
    
    return {"templates": templates}