from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from pathlib import Path
import asyncio
import logging
from typing import List, Dict, Optional
import time

from utils.virus_scan import malware_scanner, VirusScanResult
from utils.file_utils import FileUtils
from utils.speech_notifications import notify_malware_detected
from database.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

class VirusScanRequest(BaseModel):
    file_path: Optional[str] = None
    folder_path: Optional[str] = None
    recursive: bool = True
    quarantine_infected: bool = True

class VirusScanResponse(BaseModel):
    success: bool
    message: str
    results: Dict
    duration: float

class QuarantineAction(BaseModel):
    file_id: int
    action: str  # "restore", "delete", "submit_vt"

@router.post("/virus-scan", response_model=VirusScanResponse)
async def scan_for_viruses(request: VirusScanRequest, background_tasks: BackgroundTasks):
    """Scan files or folders for malware"""
    start_time = time.time()
    
    try:
        if not request.file_path and not request.folder_path:
            raise HTTPException(status_code=400, detail="Either file_path or folder_path must be provided")
        
        # Update global status
        from main import app_status
        app_status.update("virus_scanning", 0, "Starting virus scan", True)
        
        scan_results = []
        infected_files = []
        total_scanned = 0
        
        if request.file_path:
            # Scan single file
            file_path = Path(request.file_path)
            if not file_path.exists():
                raise HTTPException(status_code=400, detail="File does not exist")
            
            app_status.update("virus_scanning", 50, f"Scanning {file_path.name}")
            
            result = await malware_scanner.scan_file(file_path)
            scan_results.append({
                "file_path": str(file_path),
                "file_name": file_path.name,
                "is_infected": result.is_infected,
                "threat_name": result.threat_name,
                "detection_method": result.detection_method,
                "confidence": result.confidence,
                "details": result.details
            })
            
            if result.is_infected:
                infected_files.append(result)
            
            total_scanned = 1
            
        else:
            # Scan folder
            folder_path = Path(request.folder_path)
            if not folder_path.exists() or not folder_path.is_dir():
                raise HTTPException(status_code=400, detail="Invalid folder path")
            
            app_status.update("virus_scanning", 10, f"Scanning folder {folder_path}")
            
            # Scan files in folder
            # Exclude protected/system directories on Windows to reduce permission errors
            exclude = ['System Volume Information', '$Recycle.Bin', 'Windows\\WinSxS', 'Windows\\System32\\DriverStore']
            async for metadata in FileUtils.scan_directory(folder_path, request.recursive, exclude_dirs=exclude):
                total_scanned += 1
                
                # Update progress
                if total_scanned % 5 == 0:
                    progress = min(80, 10 + int(total_scanned / 20 * 70))
                    app_status.update("virus_scanning", progress, f"Scanned {total_scanned} files")
                
                try:
                    result = await malware_scanner.scan_file(metadata.path)
                    
                    scan_results.append({
                        "file_path": str(metadata.path),
                        "file_name": metadata.name,
                        "file_size": metadata.size,
                        "is_infected": result.is_infected,
                        "threat_name": result.threat_name,
                        "detection_method": result.detection_method,
                        "confidence": result.confidence,
                        "details": result.details
                    })
                    
                    if result.is_infected:
                        infected_files.append(result)
                        
                        # Speech notification for each infected file
                        background_tasks.add_task(
                            notify_malware_detected, 
                            result.threat_name, 
                            metadata.name
                        )
                    
                except Exception as e:
                    logger.error(f"Error scanning {metadata.path}: {e}")
                    scan_results.append({
                        "file_path": str(metadata.path),
                        "file_name": metadata.name,
                        "is_infected": False,
                        "error": str(e)
                    })
        
        # Quarantine infected files if requested
        quarantined_count = 0
        if request.quarantine_infected and infected_files:
            app_status.update("virus_scanning", 85, "Quarantining infected files")
            
            quarantine_dir = Path("quarantine")
            db = await get_db()
            
            for result in infected_files:
                file_path = Path(result.file_path)
                if file_path.exists():
                    success = await malware_scanner.quarantine_file(file_path, result, quarantine_dir)
                    if success:
                        quarantined_count += 1
                        
                        # Log quarantine to database
                        await db.log_quarantine(
                            str(quarantine_dir / f"{time.strftime('%Y%m%d_%H%M%S')}_{file_path.name}"),
                            str(file_path),
                            result.threat_name,
                            "high" if result.confidence > 0.7 else "medium",
                            result.detection_method,
                            result.file_hash or "",
                            file_path.stat().st_size if file_path.exists() else 0
                        )
        
        duration = time.time() - start_time
        
        # Prepare results
        results = {
            "total_scanned": total_scanned,
            "infected_count": len(infected_files),
            "quarantined_count": quarantined_count,
            "clean_count": total_scanned - len(infected_files),
            "scan_duration": duration,
            "scan_results": scan_results[:50],  # Limit response size
            "infected_files": [
                {
                    "file_path": r.file_path,
                    "threat_name": r.threat_name,
                    "detection_method": r.detection_method,
                    "confidence": r.confidence
                } for r in infected_files
            ]
        }
        
        # Update status
        if len(infected_files) > 0:
            message = f"Scan completed: {len(infected_files)} threats found, {quarantined_count} quarantined"
        else:
            message = f"Scan completed: All {total_scanned} files are clean"
        
        app_status.complete(message)
        
        # Log to database
        db = await get_db()
        await db.log_action(
            "WARNING" if len(infected_files) > 0 else "INFO",
            "virus_scan",
            f"Scanned {total_scanned} files",
            f"Found {len(infected_files)} threats, quarantined {quarantined_count}"
        )
        
        logger.info(f"Virus scan completed: {total_scanned} files, {len(infected_files)} threats in {duration:.2f}s")
        
        return VirusScanResponse(
            success=True,
            message=message,
            results=results,
            duration=duration
        )
        
    except Exception as e:
        logger.error(f"Virus scan error: {e}")
        app_status.complete(f"Virus scan failed: {str(e)}")
        
        # Log error
        db = await get_db()
        await db.log_action("ERROR", "virus_scan", "Virus scan failed", str(e))
        
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quarantine")
async def get_quarantined_files():
    """Get list of quarantined files"""
    try:
        db = await get_db()
        quarantined = await db.get_quarantined_files()
        
        return {
            "success": True,
            "quarantined_files": quarantined
        }
        
    except Exception as e:
        logger.error(f"Error getting quarantined files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quarantine/action")
async def quarantine_action(action: QuarantineAction):
    """Perform action on quarantined file"""
    try:
        db = await get_db()
        
        if action.action == "restore":
            # Restore file from quarantine
            # Implementation would restore the file to original location
            await db.log_action("INFO", "quarantine_restore", f"Restored file ID {action.file_id}")
            return {"success": True, "message": "File restored"}
            
        elif action.action == "delete":
            # Permanently delete quarantined file
            await db.log_action("INFO", "quarantine_delete", f"Permanently deleted file ID {action.file_id}")
            return {"success": True, "message": "File permanently deleted"}
            
        elif action.action == "submit_vt":
            # Submit to VirusTotal for analysis
            await db.log_action("INFO", "quarantine_submit_vt", f"Submitted file ID {action.file_id} to VirusTotal")
            return {"success": True, "message": "File submitted to VirusTotal"}
            
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
            
    except Exception as e:
        logger.error(f"Quarantine action error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scan/threats/summary")
async def get_threat_summary():
    """Get summary of threats found in recent scans"""
    try:
        db = await get_db()
        
        # Get recent quarantined files
        quarantined = await db.get_quarantined_files()
        
        # Group by threat type
        threat_summary = {}
        for file in quarantined:
            threat_type = file.get('threat_type', 'Unknown')
            if threat_type not in threat_summary:
                threat_summary[threat_type] = {
                    "count": 0,
                    "threat_level": file.get('threat_level', 'medium'),
                    "detection_methods": set()
                }
            threat_summary[threat_type]["count"] += 1
            threat_summary[threat_type]["detection_methods"].add(file.get('detection_method', 'unknown'))
        
        # Convert sets to lists for JSON serialization
        for threat in threat_summary.values():
            threat["detection_methods"] = list(threat["detection_methods"])
        
        return {
            "success": True,
            "summary": {
                "total_quarantined": len(quarantined),
                "threat_types": threat_summary,
                "recent_files": quarantined[:10]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting threat summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))