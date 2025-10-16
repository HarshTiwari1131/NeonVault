#!/usr/bin/env python3
"""
NeonVault - Intelligent File Organizer CLI
Terminal Interface for File Management, ML Training, and Security Scanning
"""

import sys
import os
import asyncio
import time
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv("../.env")  # Load from parent directory if present

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from api.scan import scan_folder, ScanRequest
from api.organize import organize_files, OrganizeRequest
from api.delete import delete_files, DeleteRequest
from api.ml_operations import train_ml_model, TrainRequest
from api.virus_scan import scan_for_viruses, VirusScanRequest
from ml_model.train_model import ml_trainer
from utils.file_utils import FileUtils
from database.db import init_database

class NeonVaultCLI:
    def __init__(self):
        self.logo = """
╔═══════════════════════════════════════════════════════════════╗
║                        🌟 NEONVAULT 🌟                       ║
║              Intelligent File Organizer with ML               ║
║                    Security • Organization • AI               ║
╚═══════════════════════════════════════════════════════════════╝
        """
        
        self.menu_options = {
            "1": ("📂 Scan Files", self.scan_files),
            "2": ("🤖 Train ML Model", self.train_model),
            "3": ("📁 Organize Files", self.organize_files),
            "4": ("🛡️ Threat Scan", self.threat_scan),
            "5": ("🗑️ Clean Junk Files", self.clean_files),
            "6": ("📊 System Status", self.show_status),
            "7": ("⚙️ Settings", self.show_settings),
            "0": ("❌ Exit", self.exit_app)
        }
    
    def display_logo(self):
        """Display the NeonVault logo"""
        print("\033[92m" + self.logo + "\033[0m")  # Green color
        print("🔥 Welcome to NeonVault - Your Intelligent File Management System")
        print("=" * 65)
    
    def display_menu(self):
        """Display the main menu"""
        print("\n🎯 Main Menu:")
        print("-" * 40)
        for key, (desc, _) in self.menu_options.items():
            print(f"  {key}. {desc}")
        print("-" * 40)
    
    def get_user_choice(self) -> str:
        """Get user's menu choice"""
        while True:
            choice = input("\n💫 Enter your choice (0-7): ").strip()
            if choice in self.menu_options:
                return choice
            print("❌ Invalid choice. Please enter a number between 0-7.")
    
    async def scan_files(self):
        """Scan files in a directory"""
        print("\n📂 File Scanner")
        print("=" * 30)
        
        folder_path = input("📁 Enter folder path to scan: ").strip().strip('"')
        if not folder_path or not Path(folder_path).exists():
            print("❌ Invalid or non-existent folder path.")
            return
        
        recursive = input("🔄 Scan subdirectories? (y/N): ").strip().lower() == 'y'
        export_csv = input("📊 Export to CSV? (y/N): ").strip().lower() == 'y'
        
        print(f"\n🔍 Scanning {folder_path}...")
        start_time = time.time()
        
        try:
            # Import the background tasks class
            from fastapi import BackgroundTasks
            background_tasks = BackgroundTasks()
            
            req = ScanRequest(
                folder_path=folder_path,
                recursive=recursive,
                max_files=None,
                export_csv=export_csv
            )
            
            result = await scan_folder(req, background_tasks)
            duration = time.time() - start_time
            
            print(f"\n✅ Scan completed in {duration:.2f} seconds!")
            print(f"📊 Results:")
            print(f"   • Files found: {result.results['total_files']}")
            print(f"   • Total size: {result.results['total_size_formatted']}")
            print(f"   • Categories: {len(result.results.get('categories', {}))}")
            
            if export_csv:
                print(f"📄 CSV exported to logs/ directory")
                
        except Exception as e:
            print(f"❌ Scan failed: {str(e)}")
    
    async def train_model(self):
        """Train the ML model"""
        print("\n🤖 ML Model Training")
        print("=" * 35)
        
        # Check if scan data exists
        logs_dir = Path("logs")
        csv_files = sorted(logs_dir.glob("scan_*.csv"), reverse=True) if logs_dir.exists() else []
        
        if not csv_files:
            print("❌ No scan data found. Please run a file scan first.")
            return
        
        latest_scan = csv_files[0]
        print(f"📊 Found scan data: {latest_scan.name}")
        
        proceed = input("🚀 Start training? (Y/n): ").strip().lower()
        if proceed == 'n':
            return
        
        print("\n🔄 Training ML model...")
        start_time = time.time()
        
        try:
            # Load training data directly from CSV instead of using FastAPI endpoint
            import csv
            import glob
            
            logs_dir = Path("logs")
            csv_files = sorted(logs_dir.glob("scan_*.csv"), reverse=True)
            
            if not csv_files:
                print("❌ No scan data found. Please run a file scan first.")
                return
            
            latest_csv = csv_files[0]
            training_data = []
            
            with open(latest_csv, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert numeric fields
                    for k in ["size", "entropy"]:
                        if k in row and row[k] != '':
                            try:
                                row[k] = float(row[k])
                            except Exception:
                                row[k] = 0
                    training_data.append(row)
            
            if len(training_data) < 10:
                print(f"❌ Insufficient training data. Need at least 10 files, got {len(training_data)}")
                return
            
            # Train the model directly
            result = await ml_trainer.train_model(training_data)
            duration = time.time() - start_time
            
            if result.get("success"):
                print(f"\n✅ Training completed in {duration:.2f} seconds!")
                print(f"🎯 Model accuracy: {result.get('accuracy', 0):.2%}")
                print(f"📊 Training samples: {result.get('training_samples', 0)}")
                print(f"🔧 Features: {result.get('features_count', 0)}")
            else:
                print(f"\n❌ Training failed: {result.get('error', 'Unknown error')}")
            
        except Exception as e:
            print(f"❌ Training failed: {str(e)}")
    
    async def organize_files(self):
        """Organize files using ML or rules"""
        print("\n📁 File Organizer")
        print("=" * 30)
        
        folder_path = input("📂 Enter folder path to organize: ").strip().strip('"')
        if not folder_path or not Path(folder_path).exists():
            print("❌ Invalid or non-existent folder path.")
            return
        
        destination = input("📁 Destination folder (default: organized): ").strip() or "organized"
        use_ml = input("🤖 Use ML model for categorization? (Y/n): ").strip().lower() != 'n'
        dry_run = input("👀 Dry run (preview only)? (Y/n): ").strip().lower() != 'n'
        
        print(f"\n📂 Organizing files in {folder_path}...")
        
        try:
            # Import the background tasks class
            from fastapi import BackgroundTasks
            background_tasks = BackgroundTasks()
            
            req = OrganizeRequest(
                folder_path=folder_path,
                destination_base=destination,
                dry_run=dry_run,
                use_ml=use_ml,
                create_dated_folders=False
            )
            
            result = await organize_files(req, background_tasks)
            
            print(f"\n✅ Organization completed!")
            print(f"📊 {result.message}")
            print(f"📁 Files processed: {result.results.get('files_processed', 0)}")
            
            if dry_run:
                print("💡 This was a preview. Set dry_run=False to actually move files.")
                
        except Exception as e:
            print(f"❌ Organization failed: {str(e)}")
    
    async def threat_scan(self):
        """Scan for threats and malware"""
        print("\n🛡️ Threat Scanner")
        print("=" * 30)
        
        # Check for VirusTotal API key
        vt_api_key = os.getenv('VIRUSTOTAL_API_KEY')
        if not vt_api_key:
            print("⚠️ VirusTotal API key not found in environment variables.")
            print("💡 Please add VIRUSTOTAL_API_KEY to your .env file for full threat scanning.")
        
        scan_type = input("🔍 Scan type (1=Single file, 2=Directory): ").strip()
        
        if scan_type == "1":
            file_path = input("📄 Enter file path: ").strip().strip('"')
            if not file_path or not Path(file_path).exists():
                print("❌ Invalid or non-existent file path.")
                return
            
            target_path = file_path
        elif scan_type == "2":
            folder_path = input("📁 Enter folder path: ").strip().strip('"')
            if not folder_path or not Path(folder_path).exists():
                print("❌ Invalid or non-existent folder path.")
                return
            
            target_path = folder_path
        else:
            print("❌ Invalid scan type.")
            return
        
        print(f"\n🔍 Scanning {target_path} for threats...")
        
        try:
            # Import the background tasks class
            from fastapi import BackgroundTasks
            background_tasks = BackgroundTasks()
            
            # Create the request based on target type
            if Path(target_path).is_file():
                req = VirusScanRequest(
                    file_path=target_path,
                    quarantine_infected=True
                )
            else:
                req = VirusScanRequest(
                    folder_path=target_path,
                    recursive=True,
                    quarantine_infected=True
                )
            
            result = await scan_for_viruses(req, background_tasks)
            
            print(f"\n✅ Threat scan completed!")
            print(f"🛡️ {result.message}")
            
            scan_results = result.results
            if scan_results.get('threats_found', 0) > 0:
                print(f"⚠️ Threats detected: {scan_results['threats_found']}")
                print(f"🔒 Files quarantined: {scan_results.get('quarantined', 0)}")
            else:
                print("✅ No threats detected - your files are safe!")
                
        except Exception as e:
            print(f"❌ Threat scan failed: {str(e)}")
    
    async def clean_files(self):
        """Clean junk and temporary files"""
        print("\n🗑️ File Cleaner")
        print("=" * 25)
        
        folder_path = input("📂 Enter folder path to clean: ").strip().strip('"')
        if not folder_path or not Path(folder_path).exists():
            print("❌ Invalid or non-existent folder path.")
            return
        
        # Default junk file extensions
        default_extensions = ".tmp,.log,.cache,.bak,~,.old,.temp"
        extensions = input(f"🗂️ Extensions to delete ({default_extensions}): ").strip() or default_extensions
        
        older_days = input("📅 Delete files older than days (30): ").strip()
        older_days = int(older_days) if older_days.isdigit() else 30
        
        size_kb = input("📏 Delete files smaller than KB (1): ").strip()
        size_kb = int(size_kb) if size_kb.isdigit() else 1
        
        dry_run = input("👀 Dry run (preview only)? (Y/n): ").strip().lower() != 'n'
        
        print(f"\n🧹 Cleaning files in {folder_path}...")
        
        try:
            # Import the background tasks class
            from fastapi import BackgroundTasks
            background_tasks = BackgroundTasks()
            
            req = DeleteRequest(
                folder_path=folder_path,
                rules={
                    'extensions': [ext.strip() for ext in extensions.split(',') if ext.strip()],
                    'older_than_days': older_days,
                    'size_below_kb': size_kb
                },
                dry_run=dry_run,
                permanent=False
            )
            
            result = await delete_files(req, background_tasks)
            
            print(f"\n✅ Cleaning completed!")
            print(f"🗑️ {result.message}")
            print(f"📊 Files processed: {result.results.get('files_processed', 0)}")
            
            if dry_run:
                print("💡 This was a preview. Set dry_run=False to actually delete files.")
                
        except Exception as e:
            print(f"❌ Cleaning failed: {str(e)}")
    
    async def show_status(self):
        """Show system status"""
        print("\n📊 System Status")
        print("=" * 30)
        
        try:
            # Check ML model status
            model_info = ml_trainer.get_model_info()
            
            print("🤖 ML Model:")
            if model_info.get('trained'):
                metadata = model_info.get('metadata', {})
                print(f"   ✅ Status: Trained")
                print(f"   🎯 Accuracy: {metadata.get('accuracy', 0):.2%}")
                print(f"   📊 Samples: {metadata.get('training_samples', 0)}")
                print(f"   🔧 Features: {metadata.get('features_count', 0)}")
            else:
                print("   ❌ Status: Not trained")
            
            # Check scan data
            logs_dir = Path("logs")
            csv_files = sorted(logs_dir.glob("scan_*.csv"), reverse=True) if logs_dir.exists() else []
            
            print(f"\n📂 Scan Data:")
            if csv_files:
                latest = csv_files[0]
                print(f"   📄 Latest scan: {latest.name}")
                print(f"   📅 Available scans: {len(csv_files)}")
            else:
                print("   ❌ No scan data found")
            
            # Check environment
            print(f"\n⚙️ Environment:")
            print(f"   🔑 VirusTotal API: {'✅ Configured' if os.getenv('VIRUSTOTAL_API_KEY') else '❌ Missing'}")
            print(f"   📁 Quarantine dir: {'✅ Ready' if Path('quarantine').exists() else '❌ Missing'}")
            
        except Exception as e:
            print(f"❌ Status check failed: {str(e)}")
    
    async def show_settings(self):
        """Show and modify settings"""
        print("\n⚙️ Settings")
        print("=" * 20)
        
        print("📝 Environment Variables:")
        print(f"   VIRUSTOTAL_API_KEY: {'Set' if os.getenv('VIRUSTOTAL_API_KEY') else 'Not set'}")
        
        if not os.getenv('VIRUSTOTAL_API_KEY'):
            set_key = input("\n🔑 Enter VirusTotal API key (or press Enter to skip): ").strip()
            if set_key:
                env_file = Path("../.env")
                if env_file.exists():
                    with open(env_file, 'a') as f:
                        f.write(f"\nVIRUSTOTAL_API_KEY={set_key}\n")
                else:
                    with open(env_file, 'w') as f:
                        f.write(f"VIRUSTOTAL_API_KEY={set_key}\n")
                print("✅ API key saved to .env file")
                os.environ['VIRUSTOTAL_API_KEY'] = set_key
        
        print(f"\n📊 Current Working Directory: {os.getcwd()}")
        print(f"📁 Quarantine Directory: {Path('quarantine').absolute()}")
        print(f"📄 Logs Directory: {Path('logs').absolute()}")
    
    def exit_app(self):
        """Exit the application"""
        print("\n👋 Thank you for using NeonVault!")
        print("🌟 Your files are organized, secure, and intelligent.")
        sys.exit(0)
    
    async def run(self):
        """Main application loop"""
        # Initialize database
        try:
            await init_database()
        except Exception as e:
            print(f"⚠️ Database initialization warning: {e}")
        
        # Create necessary directories
        Path("quarantine").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
        self.display_logo()
        
        while True:
            try:
                self.display_menu()
                choice = self.get_user_choice()
                
                _, action = self.menu_options[choice]
                
                if choice == "0":
                    action()
                else:
                    await action()
                
                input("\n⏸️ Press Enter to continue...")
                print("\n" + "="*65)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                sys.exit(0)
            except Exception as e:
                print(f"\n❌ An error occurred: {str(e)}")
                input("⏸️ Press Enter to continue...")

def main():
    """Entry point"""
    cli = NeonVaultCLI()
    try:
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()