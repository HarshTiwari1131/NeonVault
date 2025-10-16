import logging
import os
from datetime import datetime
from pathlib import Path

def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Setup logger with file and console handlers"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # File handler
    file_handler = logging.FileHandler(
        log_dir / f"file_organizer_{datetime.now().strftime('%Y%m%d')}.log"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

class DatabaseLogger:
    """Logger that also saves to database"""
    
    def __init__(self, db_manager, logger_name: str):
        self.db = db_manager
        self.logger = setup_logger(logger_name)
    
    async def info(self, action: str, details: str = None, result: str = None):
        """Log info level message"""
        self.logger.info(f"{action}: {details or ''}")
        await self.db.log_action("INFO", action, details, result)
    
    async def warning(self, action: str, details: str = None, result: str = None):
        """Log warning level message"""
        self.logger.warning(f"{action}: {details or ''}")
        await self.db.log_action("WARNING", action, details, result)
    
    async def error(self, action: str, details: str = None, result: str = None):
        """Log error level message"""
        self.logger.error(f"{action}: {details or ''}")
        await self.db.log_action("ERROR", action, details, result)
    
    async def debug(self, action: str, details: str = None, result: str = None):
        """Log debug level message"""
        self.logger.debug(f"{action}: {details or ''}")
        await self.db.log_action("DEBUG", action, details, result)