import asyncio
import requests
import pyclamd
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
logger = logging.getLogger(__name__)

class VirusScanResult:
    def __init__(self, file_path: str, is_infected: bool = False, 
                 threat_name: str = "", detection_method: str = "", 
                 confidence: float = 0.0, details: Dict = None):
        self.file_path = file_path
        self.is_infected = is_infected
        self.threat_name = threat_name
        self.detection_method = detection_method
        self.confidence = confidence
        self.details = details or {}
        self.file_hash = ""

class MalwareScanner:
    def __init__(self):
        self.virustotal_api_key = os.getenv("VIRUSTOTAL_API_KEY")
        self.clamav_host = os.getenv("CLAMAV_HOST", "localhost")
        self.clamav_port = int(os.getenv("CLAMAV_PORT", 3310))
        self.clamav_available = False
        self._check_clamav_connection()
    
    def _check_clamav_connection(self):
        """Check if ClamAV daemon is available"""
        try:
            cd = pyclamd.ClamdUnixSocket()
            if cd.ping():
                self.clamav_available = True
                logger.info("ClamAV connection established")
            else:
                # Try network socket
                cd = pyclamd.ClamdNetworkSocket(host=self.clamav_host, port=self.clamav_port)
                if cd.ping():
                    self.clamav_available = True
                    logger.info(f"ClamAV network connection established: {self.clamav_host}:{self.clamav_port}")
                else:
                    logger.debug("ClamAV daemon not available - using VirusTotal only")
        except Exception as e:
            logger.debug(f"ClamAV not available: {e}")
            self.clamav_available = False
    
    async def scan_file(self, file_path: Path) -> VirusScanResult:
        """Comprehensive file scanning using multiple methods"""
        logger.info(f"Starting virus scan for: {file_path}")
        
        result = VirusScanResult(str(file_path))
        
        # Step 1: ML Anomaly Detection
        ml_anomaly = await self._check_ml_anomaly(file_path)
        if ml_anomaly["is_anomaly"]:
            result.details["ml_anomaly"] = ml_anomaly
            logger.warning(f"ML anomaly detected in {file_path}")
        
        # Step 2: ClamAV Scan (local, fast)
        if self.clamav_available:
            clamav_result = await self._scan_with_clamav(file_path)
            if clamav_result["is_infected"]:
                result.is_infected = True
                result.threat_name = clamav_result["threat_name"]
                result.detection_method = "ClamAV"
                result.confidence = 0.9
                logger.warning(f"ClamAV detected threat: {result.threat_name}")
                return result
        
        # Step 3: VirusTotal API (cloud, thorough)
        if self.virustotal_api_key and (ml_anomaly["is_anomaly"] or not self.clamav_available):
            vt_result = await self._scan_with_virustotal(file_path)
            if vt_result["is_infected"]:
                result.is_infected = True
                result.threat_name = vt_result["threat_name"]
                result.detection_method = "VirusTotal"
                result.confidence = vt_result["confidence"]
                result.details["virustotal"] = vt_result["details"]
                logger.warning(f"VirusTotal detected threat: {result.threat_name}")
        
        # Calculate file hash for quarantine tracking
        result.file_hash = await self._calculate_file_hash(file_path)
        
        return result
    
    async def _check_ml_anomaly(self, file_path: Path) -> Dict:
        """Check for ML-based anomalies"""
        try:
            # Import ML model utilities
            from ml_model.predictor import MLPredictor
            
            predictor = MLPredictor()
            if predictor.is_model_available():
                # Extract features for ML prediction
                features = await self._extract_ml_features(file_path)
                anomaly_score = predictor.predict_anomaly(features)
                
                # Threshold for anomaly detection
                is_anomaly = anomaly_score > 0.7
                
                return {
                    "is_anomaly": is_anomaly,
                    "anomaly_score": anomaly_score,
                    "features": features
                }
            
        except Exception as e:
            logger.error(f"ML anomaly check failed for {file_path}: {e}")
        
        return {"is_anomaly": False, "anomaly_score": 0.0}
    
    async def _extract_ml_features(self, file_path: Path) -> Dict:
        """Extract features for ML anomaly detection"""
        features = {}
        
        try:
            stat = file_path.stat()
            features["file_size"] = stat.st_size
            features["extension"] = file_path.suffix.lower()
            
            # Calculate entropy (high entropy might indicate encryption/packing)
            if stat.st_size < 10 * 1024 * 1024:  # Less than 10MB
                features["entropy"] = await self._calculate_entropy(file_path)
            else:
                features["entropy"] = 0.0
            
            # File age
            from datetime import datetime
            features["age_days"] = (datetime.now().timestamp() - stat.st_mtime) / 86400
            
            # Extension-based risk score
            high_risk_extensions = [".exe", ".scr", ".bat", ".cmd", ".com", ".pif", ".vbs", ".js"]
            features["extension_risk"] = 1.0 if features["extension"] in high_risk_extensions else 0.0
            
        except Exception as e:
            logger.error(f"Error extracting ML features for {file_path}: {e}")
        
        return features
    
    async def _calculate_entropy(self, file_path: Path) -> float:
        """Calculate Shannon entropy of file"""
        try:
            import math
            
            with open(file_path, 'rb') as f:
                # Read first 8KB for entropy calculation
                data = f.read(8192)
            
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
            logger.error(f"Error calculating entropy for {file_path}: {e}")
            return 0.0
    
    async def _scan_with_clamav(self, file_path: Path) -> Dict:
        """Scan file with ClamAV"""
        try:
            cd = pyclamd.ClamdUnixSocket()
            if not cd.ping():
                cd = pyclamd.ClamdNetworkSocket(host=self.clamav_host, port=self.clamav_port)
            
            result = cd.scan_file(str(file_path))
            
            if result is None:
                return {"is_infected": False, "threat_name": ""}
            
            # ClamAV returns {filepath: ('FOUND', 'threat_name')} for infected files
            file_result = result.get(str(file_path))
            if file_result and file_result[0] == 'FOUND':
                return {"is_infected": True, "threat_name": file_result[1]}
            
            return {"is_infected": False, "threat_name": ""}
            
        except Exception as e:
            logger.error(f"ClamAV scan error for {file_path}: {e}")
            return {"is_infected": False, "threat_name": ""}
    
    async def _scan_with_virustotal(self, file_path: Path) -> Dict:
        """Scan file with VirusTotal API"""
        if not self.virustotal_api_key or self.virustotal_api_key == "your_api_key_here":
            logger.warning("VirusTotal API key not configured")
            return {"is_infected": False, "threat_name": "", "confidence": 0.0, "details": {}}
        
        try:
            # Calculate file hash
            file_hash = await self._calculate_file_hash(file_path)
            
            # Check if file is already known to VirusTotal
            vt_result = await self._query_virustotal_hash(file_hash)
            
            if vt_result["found"]:
                return vt_result
            
            # If file is not known, upload it (for files < 32MB)
            file_size = file_path.stat().st_size
            if file_size < 32 * 1024 * 1024:  # 32MB limit
                return await self._upload_to_virustotal(file_path)
            else:
                logger.info(f"File {file_path} too large for VirusTotal upload")
                return {"is_infected": False, "threat_name": "", "confidence": 0.0, "details": {}}
            
        except Exception as e:
            logger.error(f"VirusTotal scan error for {file_path}: {e}")
            return {"is_infected": False, "threat_name": "", "confidence": 0.0, "details": {}}
    
    async def _query_virustotal_hash(self, file_hash: str) -> Dict:
        """Query VirusTotal for file hash"""
        try:
            url = f"https://www.virustotal.com/vtapi/v2/file/report"
            params = {
                "apikey": self.virustotal_api_key,
                "resource": file_hash
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if result["response_code"] == 1:  # File found
                positives = result.get("positives", 0)
                total = result.get("total", 0)
                
                if positives > 0:
                    # Get the most common threat name
                    scans = result.get("scans", {})
                    threat_names = [scan["result"] for scan in scans.values() 
                                  if scan["detected"] and scan["result"]]
                    
                    threat_name = max(set(threat_names), key=threat_names.count) if threat_names else "Unknown"
                    confidence = positives / total if total > 0 else 0.0
                    
                    return {
                        "found": True,
                        "is_infected": True,
                        "threat_name": threat_name,
                        "confidence": confidence,
                        "details": {
                            "positives": positives,
                            "total": total,
                            "scan_date": result.get("scan_date", ""),
                            "permalink": result.get("permalink", "")
                        }
                    }
                else:
                    return {
                        "found": True,
                        "is_infected": False,
                        "threat_name": "",
                        "confidence": 0.0,
                        "details": {"positives": 0, "total": total}
                    }
            
            return {"found": False, "is_infected": False, "threat_name": "", "confidence": 0.0, "details": {}}
            
        except Exception as e:
            logger.error(f"VirusTotal hash query error: {e}")
            return {"found": False, "is_infected": False, "threat_name": "", "confidence": 0.0, "details": {}}
    
    async def _upload_to_virustotal(self, file_path: Path) -> Dict:
        """Upload file to VirusTotal for scanning"""
        try:
            url = "https://www.virustotal.com/vtapi/v2/file/scan"
            
            with open(file_path, 'rb') as f:
                files = {"file": (file_path.name, f)}
                data = {"apikey": self.virustotal_api_key}
                
                response = requests.post(url, files=files, data=data, timeout=60)
                response.raise_for_status()
                result = response.json()
            
            if result["response_code"] == 1:
                # Wait for scan to complete and get results
                scan_id = result["scan_id"]
                await asyncio.sleep(15)  # Wait for scan to process
                
                return await self._get_virustotal_report(scan_id)
            
            return {"is_infected": False, "threat_name": "", "confidence": 0.0, "details": {}}
            
        except Exception as e:
            logger.error(f"VirusTotal upload error for {file_path}: {e}")
            return {"is_infected": False, "threat_name": "", "confidence": 0.0, "details": {}}
    
    async def _get_virustotal_report(self, scan_id: str) -> Dict:
        """Get VirusTotal scan report"""
        try:
            url = "https://www.virustotal.com/vtapi/v2/file/report"
            params = {
                "apikey": self.virustotal_api_key,
                "resource": scan_id
            }
            
            # Poll for results (max 5 attempts)
            for attempt in range(5):
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                result = response.json()
                
                if result["response_code"] == 1:  # Scan complete
                    positives = result.get("positives", 0)
                    total = result.get("total", 0)
                    
                    if positives > 0:
                        scans = result.get("scans", {})
                        threat_names = [scan["result"] for scan in scans.values() 
                                      if scan["detected"] and scan["result"]]
                        
                        threat_name = max(set(threat_names), key=threat_names.count) if threat_names else "Unknown"
                        confidence = positives / total if total > 0 else 0.0
                        
                        return {
                            "is_infected": True,
                            "threat_name": threat_name,
                            "confidence": confidence,
                            "details": {
                                "positives": positives,
                                "total": total,
                                "permalink": result.get("permalink", "")
                            }
                        }
                    else:
                        return {"is_infected": False, "threat_name": "", "confidence": 0.0, "details": {}}
                
                elif result["response_code"] == -2:  # Still queued
                    await asyncio.sleep(10)
                    continue
                else:
                    break
            
            return {"is_infected": False, "threat_name": "", "confidence": 0.0, "details": {}}
            
        except Exception as e:
            logger.error(f"VirusTotal report error for scan {scan_id}: {e}")
            return {"is_infected": False, "threat_name": "", "confidence": 0.0, "details": {}}
    
    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    async def quarantine_file(self, file_path: Path, scan_result: VirusScanResult, 
                            quarantine_dir: Path = None) -> bool:
        """Move infected file to quarantine"""
        try:
            if not quarantine_dir:
                quarantine_dir = Path("quarantine")
            
            quarantine_dir.mkdir(exist_ok=True)
            
            # Create unique filename in quarantine
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            quarantined_name = f"{timestamp}_{file_path.name}"
            quarantine_path = quarantine_dir / quarantined_name
            
            # Move file to quarantine
            import shutil
            shutil.move(str(file_path), str(quarantine_path))
            
            logger.info(f"File quarantined: {file_path} -> {quarantine_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error quarantining file {file_path}: {e}")
            return False

# Global scanner instance
malware_scanner = MalwareScanner()