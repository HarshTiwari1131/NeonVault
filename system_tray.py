import pystray
import requests
from PIL import Image, ImageDraw
import threading
import sys
import os
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileOrganizerTray:
    def __init__(self):
        self.api_base_url = "http://localhost:8000/api"
        self.icon = None
        self.running = False
        
    def create_icon_image(self):
        """Create a simple icon image"""
        # Create a simple 64x64 icon
        image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw a simple folder icon with green accent
        draw.rectangle([10, 20, 54, 50], fill=(70, 75, 82, 255), outline=(74, 222, 128, 255), width=2)
        draw.rectangle([15, 15, 35, 25], fill=(74, 222, 128, 255))
        
        return image
    
    def on_clicked(self, icon, item):
        """Handle menu item clicks"""
        if str(item) == "Quick Scan":
            self.quick_scan()
        elif str(item) == "Organize Now":
            self.organize_files()
        elif str(item) == "Open Dashboard":
            self.open_dashboard()
        elif str(item) == "Exit":
            self.quit_application(icon)
    
    def quick_scan(self):
        """Perform a quick scan of Downloads folder"""
        try:
            downloads_path = str(Path.home() / "Downloads")
            
            # Make API request for scanning
            response = requests.post(f"{self.api_base_url}/scan", 
                json={
                    "folder_path": downloads_path,
                    "recursive": False,
                    "max_files": 100
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                file_count = result["results"]["total_files"]
                self.show_notification(f"Quick scan completed: {file_count} files found")
            else:
                self.show_notification("Quick scan failed")
                
        except Exception as e:
            logger.error(f"Quick scan error: {e}")
            self.show_notification("Quick scan error")
    
    def organize_files(self):
        """Organize files in Downloads folder"""
        try:
            downloads_path = str(Path.home() / "Downloads")
            
            # Make API request for organization
            response = requests.post(f"{self.api_base_url}/organize",
                json={
                    "folder_path": downloads_path,
                    "destination_base": str(Path.home() / "organized"),
                    "dry_run": False,
                    "use_ml": True
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                moved_count = result["results"]["moved_count"]
                self.show_notification(f"Organization completed: {moved_count} files organized")
            else:
                self.show_notification("Organization failed")
                
        except Exception as e:
            logger.error(f"Organization error: {e}")
            self.show_notification("Organization error")
    
    def open_dashboard(self):
        """Open the web dashboard"""
        try:
            import webbrowser
            webbrowser.open("http://localhost:3000")
        except Exception as e:
            logger.error(f"Error opening dashboard: {e}")
    
    def show_notification(self, message):
        """Show system notification"""
        try:
            if self.icon:
                self.icon.notify(message, "File Organizer")
        except Exception as e:
            logger.error(f"Notification error: {e}")
    
    def quit_application(self, icon):
        """Quit the application"""
        self.running = False
        icon.stop()
    
    def check_backend_status(self):
        """Check if backend is running"""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def run(self):
        """Run the system tray application"""
        # Check if backend is running
        if not self.check_backend_status():
            logger.error("Backend not running. Please start the backend first.")
            sys.exit(1)
        
        # Create menu items
        menu = pystray.Menu(
            pystray.MenuItem("Quick Scan", self.on_clicked),
            pystray.MenuItem("Organize Now", self.on_clicked),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open Dashboard", self.on_clicked),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.on_clicked)
        )
        
        # Create and run icon
        self.icon = pystray.Icon(
            "file_organizer",
            self.create_icon_image(),
            "Intelligent File Organizer",
            menu
        )
        
        self.running = True
        logger.info("File Organizer system tray started")
        
        # Show startup notification
        threading.Timer(1.0, lambda: self.show_notification("File Organizer is running")).start()
        
        # Run the icon (this blocks)
        self.icon.run()

def main():
    """Main entry point"""
    app = FileOrganizerTray()
    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {e}")

if __name__ == "__main__":
    main()