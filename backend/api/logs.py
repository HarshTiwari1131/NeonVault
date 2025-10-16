from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from typing import List, Dict, Optional

from database.db import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

class LogFilter(BaseModel):
    level: Optional[str] = None
    action: Optional[str] = None
    limit: int = 100
    offset: int = 0

@router.get("/logs")
async def get_logs(
    level: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get application logs with optional filtering"""
    try:
        db = await get_db()
        logs = await db.get_logs(limit, offset)
        
        # Apply filters
        if level or action:
            filtered_logs = []
            for log in logs:
                if level and log.get('level', '').upper() != level.upper():
                    continue
                if action and action.lower() not in log.get('action', '').lower():
                    continue
                filtered_logs.append(log)
            logs = filtered_logs
        
        return {
            "success": True,
            "logs": logs,
            "total": len(logs),
            "filters": {
                "level": level,
                "action": action,
                "limit": limit,
                "offset": offset
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/levels")
async def get_log_levels():
    """Get available log levels"""
    return {
        "levels": [
            {"value": "DEBUG", "label": "Debug", "color": "#6B7280"},
            {"value": "INFO", "label": "Info", "color": "#3B82F6"},
            {"value": "WARNING", "label": "Warning", "color": "#F59E0B"},
            {"value": "ERROR", "label": "Error", "color": "#EF4444"}
        ]
    }

@router.get("/logs/actions")
async def get_log_actions():
    """Get common log action types"""
    return {
        "actions": [
            "folder_scan",
            "file_organization", 
            "file_deletion",
            "virus_scan",
            "ml_training",
            "quarantine_action",
            "system_startup",
            "system_shutdown"
        ]
    }

@router.delete("/logs/clear")
async def clear_logs(older_than_days: Optional[int] = None):
    """Clear old log entries"""
    try:
        # This would be implemented to clear logs older than specified days
        # For now, just log the action
        db = await get_db()
        await db.log_action(
            "INFO",
            "log_maintenance",
            f"Requested log clearing older than {older_than_days} days" if older_than_days else "Requested full log clearing"
        )
        
        return {
            "success": True,
            "message": f"Log clearing requested" + (f" for entries older than {older_than_days} days" if older_than_days else "")
        }
        
    except Exception as e:
        logger.error(f"Error clearing logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/stats")
async def get_log_statistics():
    """Get log statistics"""
    try:
        db = await get_db()
        logs = await db.get_logs(1000)  # Get recent logs for stats
        
        # Calculate statistics
        level_counts = {}
        action_counts = {}
        
        for log in logs:
            level = log.get('level', 'UNKNOWN')
            action = log.get('action', 'unknown')
            
            level_counts[level] = level_counts.get(level, 0) + 1
            action_counts[action] = action_counts.get(action, 0) + 1
        
        return {
            "success": True,
            "statistics": {
                "total_logs": len(logs),
                "level_distribution": level_counts,
                "action_distribution": action_counts,
                "most_common_level": max(level_counts.items(), key=lambda x: x[1])[0] if level_counts else None,
                "most_common_action": max(action_counts.items(), key=lambda x: x[1])[0] if action_counts else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting log statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))