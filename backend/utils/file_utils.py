import os
import shutil
import aiofiles
import hashlib
import magic
import mimetypes
from pathlib import Path
from typing import List, Dict, Tuple, Optional, AsyncGenerator
import asyncio
import logging
from datetime import datetime
import math

logger = logging.getLogger(__name__)

class FileMetadata:
    def __init__(self, file_path: Path):
        self.path = file_path
        self.name = file_path.name
        self.extension = file_path.suffix.lower()
        self.size = 0
        self.mime_type = ""
        self.modified_time = None
        self.entropy = 0.0
        self.hash_md5 = ""
        
    async def extract_metadata(self) -> Dict:
        """Extract comprehensive file metadata"""
        try:
            stat = self.path.stat()
            self.size = stat.st_size
            self.modified_time = datetime.fromtimestamp(stat.st_mtime)
            
            # Get MIME type
            self.mime_type, _ = mimetypes.guess_type(str(self.path))
            if not self.mime_type:
                try:
                    self.mime_type = magic.from_file(str(self.path), mime=True)
                except:
                    self.mime_type = "application/octet-stream"
            
            # Calculate MD5 hash and entropy for small files
            if self.size < 10 * 1024 * 1024:  # Less than 10MB
                self.hash_md5 = await self._calculate_hash()
                self.entropy = await self._calculate_entropy()
            
            return self.to_dict()
            
        except Exception as e:
            logger.error(f"Error extracting metadata for {self.path}: {e}")
            return self.to_dict()
    
    async def _calculate_hash(self) -> str:
        """Calculate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        try:
            async with aiofiles.open(self.path, 'rb') as f:
                async for chunk in self._read_chunks(f):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {self.path}: {e}")
            return ""
    
    async def _calculate_entropy(self) -> float:
        """Calculate Shannon entropy of file (indicator of randomness/encryption)"""
        try:
            if self.size == 0:
                return 0.0
            
            # Read first 8KB for entropy calculation
            chunk_size = min(8192, self.size)
            async with aiofiles.open(self.path, 'rb') as f:
                data = await f.read(chunk_size)
            
            if not data:
                return 0.0
            
            # Calculate byte frequency
            byte_counts = [0] * 256
            for byte in data:
                byte_counts[byte] += 1
            
            # Calculate entropy
            entropy = 0.0
            data_len = len(data)
            for count in byte_counts:
                if count > 0:
                    frequency = count / data_len
                    entropy -= frequency * math.log2(frequency)
            
            return entropy
            
        except Exception as e:
            logger.error(f"Error calculating entropy for {self.path}: {e}")
            return 0.0
    
    async def _read_chunks(self, file_obj, chunk_size: int = 8192):
        """Async generator for reading file chunks"""
        while True:
            chunk = await file_obj.read(chunk_size)
            if not chunk:
                break
            yield chunk
    
    def to_dict(self) -> Dict:
        """Convert metadata to dictionary"""
        return {
            "path": str(self.path),
            "name": self.name,
            "extension": self.extension,
            "size": self.size,
            "mime_type": self.mime_type,
            "modified_time": self.modified_time.isoformat() if self.modified_time else None,
            "entropy": self.entropy,
            "hash_md5": self.hash_md5
        }

class FileUtils:
    
    @staticmethod
    async def scan_directory(
        directory: Path,
        recursive: bool = True,
        exclude_dirs: Optional[List[str]] = None,
    ) -> AsyncGenerator[FileMetadata, None]:
        """Asynchronously scan directory and yield file metadata
        - exclude_dirs: optional list of directory names to skip anywhere in the path (case-insensitive)
        """
        if not directory.exists() or not directory.is_dir():
            logger.error(f"Directory does not exist: {directory}")
            return
        
        try:
            if recursive:
                pattern = "**/*"
            else:
                pattern = "*"
            
            for file_path in directory.glob(pattern):
                if file_path.is_file():
                    # Skip excluded directories if specified
                    if exclude_dirs:
                        parts_lower = [p.lower() for p in file_path.parts]
                        if any(excl.lower() in parts_lower for excl in exclude_dirs):
                            continue
                    try:
                        metadata = FileMetadata(file_path)
                        await metadata.extract_metadata()
                        yield metadata
                    except Exception as e:
                        logger.error(f"Error processing file {file_path}: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
    
    @staticmethod
    async def move_file(source: Path, destination: Path, dry_run: bool = False) -> bool:
        """Move file to destination with error handling"""
        try:
            if dry_run:
                logger.info(f"DRY RUN: Would move {source} to {destination}")
                return True
            
            # Create destination directory if it doesn't exist
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Handle file name conflicts
            if destination.exists():
                destination = FileUtils._get_unique_filename(destination)
            
            shutil.move(str(source), str(destination))
            logger.info(f"Moved {source} to {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Error moving file {source} to {destination}: {e}")
            return False
    
    @staticmethod
    async def copy_file(source: Path, destination: Path) -> bool:
        """Copy file to destination"""
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            if destination.exists():
                destination = FileUtils._get_unique_filename(destination)
            
            shutil.copy2(str(source), str(destination))
            logger.info(f"Copied {source} to {destination}")
            return True
            
        except Exception as e:
            logger.error(f"Error copying file {source} to {destination}: {e}")
            return False
    
    @staticmethod
    async def delete_file(file_path: Path, permanent: bool = False) -> bool:
        """Delete file (to trash or permanently)"""
        try:
            if permanent:
                file_path.unlink()
                logger.info(f"Permanently deleted {file_path}")
            else:
                # Move to trash/recycle bin (platform-specific)
                trash_dir = Path("trash")
                trash_dir.mkdir(exist_ok=True)
                
                trash_destination = trash_dir / file_path.name
                if trash_destination.exists():
                    trash_destination = FileUtils._get_unique_filename(trash_destination)
                
                shutil.move(str(file_path), str(trash_destination))
                logger.info(f"Moved {file_path} to trash")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    @staticmethod
    def _get_unique_filename(file_path: Path) -> Path:
        """Generate unique filename if file exists"""
        counter = 1
        original_stem = file_path.stem
        suffix = file_path.suffix
        parent = file_path.parent
        
        while file_path.exists():
            new_name = f"{original_stem}_{counter}{suffix}"
            file_path = parent / new_name
            counter += 1
        
        return file_path
    
    @staticmethod
    def get_file_category_by_extension(extension: str) -> str:
        """Categorize file by extension"""
        extension = extension.lower()
        
        categories = {
            "documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".pages"],
            "images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".svg", ".webp"],
            "videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
            "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"],
            "archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
            "code": [".py", ".js", ".html", ".css", ".cpp", ".java", ".c", ".php", ".rb"],
            "spreadsheets": [".xlsx", ".xls", ".csv", ".ods"],
            "presentations": [".pptx", ".ppt", ".odp"],
            "executables": [".exe", ".msi", ".dmg", ".deb", ".rpm", ".app"]
        }
        
        for category, extensions in categories.items():
            if extension in extensions:
                return category
        
        return "others"
    
    @staticmethod
    async def get_directory_stats(directory: Path) -> Dict:
        """Get directory statistics"""
        stats = {
            "total_files": 0,
            "total_size": 0,
            "categories": {},
            "largest_file": {"name": "", "size": 0},
            "oldest_file": {"name": "", "date": None},
            "newest_file": {"name": "", "date": None}
        }
        
        try:
            async for metadata in FileUtils.scan_directory(directory):
                stats["total_files"] += 1
                stats["total_size"] += metadata.size
                
                # Category stats
                category = FileUtils.get_file_category_by_extension(metadata.extension)
                if category not in stats["categories"]:
                    stats["categories"][category] = {"count": 0, "size": 0}
                stats["categories"][category]["count"] += 1
                stats["categories"][category]["size"] += metadata.size
                
                # Largest file
                if metadata.size > stats["largest_file"]["size"]:
                    stats["largest_file"] = {"name": metadata.name, "size": metadata.size}
                
                # Date tracking
                if metadata.modified_time:
                    if not stats["oldest_file"]["date"] or metadata.modified_time < stats["oldest_file"]["date"]:
                        stats["oldest_file"] = {"name": metadata.name, "date": metadata.modified_time}
                    
                    if not stats["newest_file"]["date"] or metadata.modified_time > stats["newest_file"]["date"]:
                        stats["newest_file"] = {"name": metadata.name, "date": metadata.modified_time}
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting directory stats for {directory}: {e}")
            return stats

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"