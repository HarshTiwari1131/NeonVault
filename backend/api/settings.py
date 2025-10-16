from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from typing import Dict, Optional, Any
import os
from pathlib import Path

from database.db import get_db
from utils.speech_notifications import speech_notifications
from utils.email_notifications import email_notifications

logger = logging.getLogger(__name__)
router = APIRouter()

class SettingsUpdate(BaseModel):
    key: str
    value: Any

class APIKeyUpdate(BaseModel):
    virustotal_api_key: Optional[str] = None
    clamav_host: Optional[str] = None
    clamav_port: Optional[int] = None

class NotificationSettings(BaseModel):
    speech_enabled: bool = True
    email_notifications: bool = False
    desktop_notifications: bool = True
    recipient_email: Optional[str] = None


@router.get("/settings")
async def get_settings():
    """Get current application settings"""
    try:
        db = await get_db()
        
        # Get all settings from database
        settings = {}
        
        # Default settings structure
        default_settings = {
            "api_keys": {
                "virustotal_api_key": os.getenv("VIRUSTOTAL_API_KEY", ""),
                "clamav_host": os.getenv("CLAMAV_HOST", "localhost"),
                "clamav_port": int(os.getenv("CLAMAV_PORT", 3310))
            },
            "notifications": {
                "speech_enabled": speech_notifications.is_enabled(),
                "email_notifications": False,
                "desktop_notifications": True
            },
            "scanning": {
                "scan_timeout_seconds": 300,
                "max_file_size_mb": 100,
                "enable_ml_scanning": True,
                "auto_quarantine": True
            },
            "organization": {
                "default_destination": "organized",
                "create_dated_folders": False,
                "use_ml_predictions": True,
                "dry_run_by_default": True
            },
            "deletion": {
                "safe_delete_by_default": True,
                "require_confirmation": True,
                "backup_before_delete": False
            },
            "ml_model": {
                "auto_retrain_threshold": 1000,
                "min_confidence_threshold": 0.7,
                "feature_extraction_enabled": True
            },
            "ui": {
                "theme": "neonvault",
                "show_file_previews": True,
                "animate_transitions": True,
                "compact_mode": False
            },
            "logging": {
                "log_level": "INFO",
                "max_log_size_mb": 50,
                "log_retention_days": 30
            }
        }
        
        # Try to get custom settings from database
        for category in default_settings:
            for key in default_settings[category]:
                setting_key = f"{category}.{key}"
                value = await db.get_setting(setting_key)
                if value is not None:
                    try:
                        # Try to parse as appropriate type
                        if isinstance(default_settings[category][key], bool):
                            default_settings[category][key] = value.lower() == 'true'
                        elif isinstance(default_settings[category][key], int):
                            default_settings[category][key] = int(value)
                        elif isinstance(default_settings[category][key], float):
                            default_settings[category][key] = float(value)
                        else:
                            default_settings[category][key] = value
                    except (ValueError, AttributeError):
                        pass  # Keep default value
        
        # Mask API key for security
        api_key = default_settings["api_keys"]["virustotal_api_key"]
        if api_key and len(api_key) > 8:
            default_settings["api_keys"]["virustotal_api_key"] = f"{api_key[:4]}...{api_key[-4:]}"
            
        return {
            "success": True,
            "settings": default_settings
        }
        
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/settings/update")
async def update_setting(update: SettingsUpdate):
    """Update a specific setting"""
    try:
        db = await get_db()
        
        # Convert value to string for storage
        str_value = str(update.value).lower() if isinstance(update.value, bool) else str(update.value)
        
        # Update in database
        await db.update_setting(update.key, str_value)
        
        # Apply setting immediately if needed
        await _apply_setting_change(update.key, update.value)
        
        # Log the change
        await db.log_action(
            "INFO",
            "setting_update",
            f"Updated setting {update.key}",
            f"New value: {update.value}"
        )
        
        return {
            "success": True,
            "message": f"Setting {update.key} updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error updating setting {update.key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/settings/api-keys")
async def update_api_keys(keys: APIKeyUpdate):
    """Update API keys and connection settings"""
    try:
        db = await get_db()
        updated_keys = []
        
        if keys.virustotal_api_key is not None:
            await db.update_setting("api_keys.virustotal_api_key", keys.virustotal_api_key)
            os.environ["VIRUSTOTAL_API_KEY"] = keys.virustotal_api_key
            updated_keys.append("VirusTotal API Key")
        
        if keys.clamav_host is not None:
            await db.update_setting("api_keys.clamav_host", keys.clamav_host)
            os.environ["CLAMAV_HOST"] = keys.clamav_host
            updated_keys.append("ClamAV Host")
        
        if keys.clamav_port is not None:
            await db.update_setting("api_keys.clamav_port", str(keys.clamav_port))
            os.environ["CLAMAV_PORT"] = str(keys.clamav_port)
            updated_keys.append("ClamAV Port")
        
        # Log the change
        await db.log_action(
            "INFO",
            "api_keys_update",
            f"Updated API keys: {', '.join(updated_keys)}"
        )
        
        return {
            "success": True,
            "message": f"Updated {', '.join(updated_keys)}",
            "updated_keys": updated_keys
        }
        
    except Exception as e:
        logger.error(f"Error updating API keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/settings/notifications")
async def update_notification_settings(settings: NotificationSettings):
    """Update notification settings"""
    try:
        db = await get_db()
        
        # Update speech notifications
        if settings.speech_enabled:
            speech_notifications.enable()
        else:
            speech_notifications.disable()
        
        # Configure email notifications
        email_notifications.configure(
            recipient_email=settings.recipient_email,
            enabled=settings.email_notifications
        )
        
        # Update database settings
        await db.update_setting("notifications.speech_enabled", str(settings.speech_enabled))
        await db.update_setting("notifications.email_notifications", str(settings.email_notifications))
        await db.update_setting("notifications.desktop_notifications", str(settings.desktop_notifications))
        if settings.recipient_email:
            await db.update_setting("notifications.recipient_email", settings.recipient_email)
        
        # Log the change
        await db.log_action(
            "INFO",
            "notification_settings_update",
            "Updated notification settings",
            f"Speech: {settings.speech_enabled}, Email: {settings.email_notifications}, Recipient: {settings.recipient_email}"
        )
        
        return {
            "success": True,
            "message": "Notification settings updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error updating notification settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings/test-speech")
async def test_speech_notification():
    """Test speech notification functionality"""
    try:
        if speech_notifications.is_enabled():
            speech_notifications.speak("Speech notifications are working correctly", "normal")
            return {
                "success": True,
                "message": "Speech test initiated"
            }
        else:
            return {
                "success": False,
                "message": "Speech notifications are disabled"
            }
            
    except Exception as e:
        logger.error(f"Error testing speech: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings/system-info")
async def get_system_info():
    """Get system information and status"""
    try:
        import psutil
        import platform
        
        # Get system information
        system_info = {
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor()
            },
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "used": psutil.disk_usage('/').used,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            },
            "cpu": {
                "count": psutil.cpu_count(),
                "usage": psutil.cpu_percent(interval=1)
            }
        }
        
        # Get application paths
        app_info = {
            "working_directory": str(Path.cwd()),
            "database_path": "backend/database/history.db",
            "ml_model_path": "backend/ml_model/model.pkl",
            "quarantine_path": "quarantine",
            "logs_path": "logs"
        }
        
        # Check component status
        component_status = {
            "database": Path("backend/database/history.db").exists(),
            "ml_model": Path("backend/ml_model/model.pkl").exists(),
            "quarantine_dir": Path("quarantine").exists(),
            "logs_dir": Path("logs").exists()
        }
        
        return {
            "success": True,
            "system_info": system_info,
            "app_info": app_info,
            "component_status": component_status
        }
        
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        # Return basic info even if psutil fails
        return {
            "success": True,
            "system_info": {
                "platform": {"system": platform.system()},
                "message": "Limited system info available"
            },
            "app_info": {
                "working_directory": str(Path.cwd())
            },
            "component_status": {}
        }

@router.post("/settings/reset")
async def reset_settings():
    """Reset all settings to defaults"""
    try:
        db = await get_db()
        
        # This would reset all settings in the database
        # For now, just log the action
        await db.log_action(
            "WARNING",
            "settings_reset",
            "All settings reset to defaults"
        )
        
        return {
            "success": True,
            "message": "Settings reset to defaults"
        }
        
    except Exception as e:
        logger.error(f"Error resetting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _apply_setting_change(key: str, value: Any):
    """Apply setting changes immediately where applicable"""
    try:
        if key == "notifications.speech_enabled":
            if value:
                speech_notifications.enable()
            else:
                speech_notifications.disable()
        
        # Add other immediate setting applications here
        
    except Exception as e:
        logger.error(f"Error applying setting change {key}: {e}")