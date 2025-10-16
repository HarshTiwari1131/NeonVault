import pyttsx3
import threading
import logging
from typing import Optional
import os
import queue
import atexit

logger = logging.getLogger(__name__)

class SpeechNotifications:
    def __init__(self):
        self.enabled = True
        self._task_queue = queue.Queue()
        self._worker_thread = threading.Thread(target=self._speech_worker)
        self._worker_thread.daemon = True
        self._worker_thread.start()
        atexit.register(self._shutdown)

    def _shutdown(self):
        self._task_queue.put(None)
        self._worker_thread.join(timeout=2)

    def _speech_worker(self):
        """Worker thread that processes speech tasks."""
        while True:
            task = self._task_queue.get()
            if task is None:
                # Shutdown signal
                break
            
            text, priority = task
            try:
                # Initialize engine inside the worker thread for each task
                engine = pyttsx3.init()
                
                voices = engine.getProperty('voices')
                if voices:
                    for voice in voices:
                        if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                            engine.setProperty('voice', voice.id)
                            break
                    else:
                        engine.setProperty('voice', voices[0].id)
                
                engine.setProperty('rate', 180)
                engine.setProperty('volume', 0.8)
                
                logger.info(f"Speaking ({priority}): {text}")
                engine.say(text)
                engine.runAndWait()
                engine.stop() # Cleanly stop the engine
                
            except Exception as e:
                logger.error(f"Error during speech synthesis in worker: {e}")
            finally:
                self._task_queue.task_done()
    
    def enable(self):
        """Enable speech notifications"""
        self.enabled = True
        logger.info("Speech notifications enabled")
    
    def disable(self):
        """Disable speech notifications"""
        self.enabled = False
        logger.info("Speech notifications disabled")
    
    def is_enabled(self) -> bool:
        """Check if speech notifications are enabled"""
        return self.enabled
    
    def speak(self, text: str, priority: str = "normal"):
        """Add text to the speech queue."""
        if not self.is_enabled():
            return
        
        self._task_queue.put((text, priority))
    
    # Predefined notification methods
    def notify_scan_complete(self, file_count: int, duration: float):
        """Notification for scan completion"""
        text = f"Scan complete. Processed {file_count} files in {duration:.1f} seconds."
        self.speak(text, "normal")
    
    def notify_malware_detected(self, threat_name: str, file_name: str):
        """High priority notification for malware detection"""
        text = f"Security alert! {threat_name} detected in {file_name}. File has been quarantined."
        self.speak(text, "high")
    
    def notify_organization_complete(self, moved_count: int):
        """Notification for organization completion"""
        text = f"Organization complete. {moved_count} files have been organized."
        self.speak(text, "normal")
    
    def notify_error(self, operation: str):
        """Notification for errors"""
        text = f"Error during {operation}. Please check the logs for details."
        self.speak(text, "high")
    
    def notify_training_complete(self, accuracy: float):
        """Notification for ML training completion"""
        text = f"Machine learning model training complete. Accuracy: {accuracy:.1f} percent."
        self.speak(text, "normal")
    
    def notify_deletion_complete(self, deleted_count: int, dry_run: bool = False):
        """Notification for file deletion"""
        if dry_run:
            text = f"Dry run complete. {deleted_count} files would be deleted."
        else:
            text = f"Deletion complete. {deleted_count} files have been removed."
        self.speak(text, "normal")

# Global speech notifications instance
speech_notifications = SpeechNotifications()

# Utility functions for easy access
def enable_speech():
    """Enable speech notifications"""
    speech_notifications.enable()

def disable_speech():
    """Disable speech notifications"""
    speech_notifications.disable()

def speak(text: str, priority: str = "normal"):
    """Speak text with given priority"""
    speech_notifications.speak(text, priority)

# Notification shortcuts
def notify_scan_complete(file_count: int, duration: float):
    speech_notifications.notify_scan_complete(file_count, duration)

def notify_malware_detected(threat_name: str, file_name: str):
    speech_notifications.notify_malware_detected(threat_name, file_name)

def notify_organization_complete(moved_count: int):
    speech_notifications.notify_organization_complete(moved_count)

def notify_error(operation: str):
    speech_notifications.notify_error(operation)

def notify_training_complete(accuracy: float):
    speech_notifications.notify_training_complete(accuracy)

def notify_deletion_complete(deleted_count: int, dry_run: bool = False):
    speech_notifications.notify_deletion_complete(deleted_count, dry_run)