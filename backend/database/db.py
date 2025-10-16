import sqlite3
import aiosqlite
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Create database in backend/database directory
            current_dir = Path(__file__).parent
            db_dir = current_dir
            db_dir.mkdir(exist_ok=True)
            self.db_path = str(db_dir / "history.db")
        else:
            self.db_path = db_path

    async def init_database(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Create tables
            await db.execute("""
                CREATE TABLE IF NOT EXISTS moves (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    source_path TEXT NOT NULL,
                    destination_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_size INTEGER,
                    category TEXT,
                    confidence REAL,
                    dry_run BOOLEAN DEFAULT FALSE
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS scan_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    folder_path TEXT NOT NULL,
                    total_files INTEGER,
                    total_size INTEGER,
                    categories_found TEXT,
                    scan_duration REAL,
                    ml_predictions INTEGER DEFAULT 0
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS quarantine (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    file_path TEXT NOT NULL,
                    original_path TEXT NOT NULL,
                    threat_type TEXT,
                    threat_level TEXT,
                    detection_method TEXT,
                    file_hash TEXT,
                    file_size INTEGER,
                    status TEXT DEFAULT 'quarantined'
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    level TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    result TEXT,
                    user_agent TEXT
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS ml_training_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    accuracy REAL,
                    training_duration REAL,
                    features_count INTEGER,
                    model_version TEXT
                )
            """)

            await db.commit()
            logger.info("Database initialized successfully")

    async def log_move(self, source_path: str, destination_path: str, file_name: str, 
                      file_size: int, category: str, confidence: float, dry_run: bool = False):
        """Log file move operation"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO moves (source_path, destination_path, file_name, file_size, 
                                 category, confidence, dry_run)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (source_path, destination_path, file_name, file_size, category, confidence, dry_run))
            await db.commit()

    async def log_scan_result(self, folder_path: str, total_files: int, total_size: int,
                             categories_found: Dict, scan_duration: float, ml_predictions: int = 0):
        """Log scan operation results"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO scan_results (folder_path, total_files, total_size, 
                                        categories_found, scan_duration, ml_predictions)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (folder_path, total_files, total_size, json.dumps(categories_found), 
                  scan_duration, ml_predictions))
            await db.commit()

    async def log_quarantine(self, file_path: str, original_path: str, threat_type: str,
                           threat_level: str, detection_method: str, file_hash: str, file_size: int):
        """Log quarantined file"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO quarantine (file_path, original_path, threat_type, threat_level,
                                      detection_method, file_hash, file_size)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (file_path, original_path, threat_type, threat_level, detection_method, 
                  file_hash, file_size))
            await db.commit()

    async def log_action(self, level: str, action: str, details: str = None, 
                        result: str = None, user_agent: str = None):
        """Log general application action"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO logs (level, action, details, result, user_agent)
                VALUES (?, ?, ?, ?, ?)
            """, (level, action, details, result, user_agent))
            await db.commit()

    async def get_logs(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get application logs"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT * FROM logs ORDER BY timestamp DESC LIMIT ? OFFSET ?
            """, (limit, offset))
            rows = await cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    async def get_quarantined_files(self) -> List[Dict]:
        """Get all quarantined files"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT * FROM quarantine WHERE status = 'quarantined' ORDER BY timestamp DESC
            """)
            rows = await cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    async def get_recent_moves(self, limit: int = 50) -> List[Dict]:
        """Get recent file moves"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT * FROM moves ORDER BY timestamp DESC LIMIT ?
            """, (limit,))
            rows = await cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    async def get_scan_stats(self, days: int = 30) -> Dict:
        """Get scan statistics for the last N days"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT COUNT(*) as total_scans, 
                       SUM(total_files) as total_files_scanned,
                       SUM(total_size) as total_size_scanned,
                       AVG(scan_duration) as avg_scan_duration
                FROM scan_results 
                WHERE timestamp >= datetime('now', '-{} days')
            """.format(days))
            row = await cursor.fetchone()
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row)) if row else {}

    async def update_setting(self, key: str, value: str):
        """Update or insert a setting"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (key, value))
            await db.commit()

    async def get_setting(self, key: str) -> Optional[str]:
        """Get a setting value"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = await cursor.fetchone()
            return row[0] if row else None

    async def log_ml_training(self, accuracy: float, training_duration: float, 
                             features_count: int, model_version: str):
        """Log ML model training results"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO ml_training_history (accuracy, training_duration, features_count, model_version)
                VALUES (?, ?, ?, ?)
            """, (accuracy, training_duration, features_count, model_version))
            await db.commit()

# Global database instance
db_manager = DatabaseManager()

async def init_database():
    """Initialize the database"""
    await db_manager.init_database()

async def get_db():
    """Get database manager instance"""
    return db_manager