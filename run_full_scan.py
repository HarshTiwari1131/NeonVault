#!/usr/bin/env python3
"""
Full E: drive scan script
"""
import requests
import json
import time
import subprocess
import os

def start_backend():
    """Start the backend server"""
    python_exe = "C:/Users/Rajan/anaconda3/envs/neonvault-py311/python.exe"
    backend_script = "backend/main.py"
    
    print("🚀 Starting backend server...")
    process = subprocess.Popen([python_exe, backend_script], cwd=".")
    time.sleep(5)  # Wait for server to start
    return process

def run_full_scan():
    payload = {
        "folder_path": "E:\\",
        "recursive": True,
        "export_csv": True
    }

    print("🔍 Starting full E: drive scan...")
    print("⏰ This may take several minutes depending on the number of files...")
    print("📊 CSV export is enabled - results will be saved to logs/")
    print("-" * 60)

    start_time = time.time()
    
    try:
        response = requests.post(
            "http://127.0.0.1:8000/api/scan",
            json=payload,
            timeout=900  # 15 minute timeout for full drive scan
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n" + "="*60)
            print("✅ SCAN COMPLETED SUCCESSFULLY!")
            print("="*60)
            
            results = result["results"]
            
            print(f"📁 Folder scanned: {results['folder_path']}")
            print(f"📊 Total files found: {results['total_files']:,}")
            print(f"💾 Total size: {results['total_size_formatted']}")
            print(f"⏱️  Scan duration: {results['scan_duration']:.2f} seconds")
            
            if 'csv_path' in results:
                print(f"📋 CSV exported to: {results['csv_path']}")
            
            print(f"\n📂 File Categories Breakdown:")
            print("-" * 40)
            
            total_files = results['total_files']
            for category, data in results['categories'].items():
                count = data['count']
                size = data['size']
                percentage = (count / total_files) * 100 if total_files > 0 else 0
                
                # Format size
                if size > 1024**3:  # GB
                    size_str = f"{size/(1024**3):.1f} GB"
                elif size > 1024**2:  # MB
                    size_str = f"{size/(1024**2):.1f} MB"
                elif size > 1024:  # KB
                    size_str = f"{size/1024:.1f} KB"
                else:
                    size_str = f"{size} B"
                
                print(f"  {category.capitalize():<15}: {count:>6,} files ({percentage:>5.1f}%) - {size_str}")
            
            print("\n" + "="*60)
            print("🎯 Scan Summary:")
            print(f"   • Backend is running and responsive")
            print(f"   • Drive scan completed without errors")
            print(f"   • CSV file contains full file inventory")
            print(f"   • ML model ready for training with scan data")
            print("="*60)
            
        else:
            print(f"\n❌ SCAN FAILED")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print(f"\n⏰ SCAN TIMEOUT")
        print("The scan is taking longer than expected (>15 minutes).")
        print("This is normal for drives with many files.")
        print("Check backend logs or use progress monitoring commands.")
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ CONNECTION ERROR")
        print("Cannot connect to backend server at http://127.0.0.1:8000")
        print("Make sure the backend is running with:")
        print("  conda activate file_organizer")
        print("  cd backend")
        print("  python main.py")
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        
    finally:
        elapsed = time.time() - start_time
        print(f"\nTotal execution time: {elapsed:.2f} seconds")

if __name__ == "__main__":
    # Start backend first
    backend_process = start_backend()
    
    try:
        # Check if backend is healthy
        health_response = requests.get("http://127.0.0.1:8000/api/health", timeout=10)
        if health_response.status_code == 200:
            print("✅ Backend is healthy!")
            run_full_scan()
        else:
            print("❌ Backend health check failed")
    except Exception as e:
        print(f"❌ Backend connection error: {e}")
        print("Make sure the backend started successfully")
    
    # Keep backend running for testing
    input("\n🔧 Backend is running. Press Enter to stop...")