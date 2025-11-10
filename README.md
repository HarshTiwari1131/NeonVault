# 🚀 NeonVault File Organizer & Malware Scanner

A comprehensive intelligent file management and security system with ML-powered organization and advanced malware detection capabilities.

![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![React](https://img.shields.io/badge/React-18+-61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688)

---

## 🌐 Live Demo

[🎮 **View Live Demo**](https://neon-vault-flax.vercel.app) | [📖 **API Documentation**]()

---

## ✨ Features

### 🔍 **Intelligent File Management**
- **ML-Powered Organization**: Auto-classify files using scikit-learn RandomForestClassifier
- **Smart File Scanning**: Recursive directory analysis with real-time progress monitoring
- **File Operations**: Move, delete, organize files with comprehensive logging
- **CSV Export**: Complete file inventory with metadata (path, size, type, entropy, hash)

### 🛡️ **Advanced Security**
- **Malware Detection**: ClamAV local scanning + VirusTotal API integration
- **Quarantine System**: Automatic threat isolation with metadata logging
- **Hash-based Analysis**: MD5 fingerprinting for duplicate and threat identification
- **Safety Exclusions**: Smart Windows system folder protection

### 🎨 **NeonVault UI**
- **Cyberpunk Theme**: Modern glassmorphism design with neon accents
- **Color Palette**: BG `#0D1117`, Panel `#161B22`, Neon `#4ADE80`
- **Real-time Dashboard**: Live scan progress and file statistics
- **Responsive Design**: Works perfectly on desktop and mobile

### 📊 **Data & Analytics**
- **SQLite Database**: Persistent logging of all operations
- **Historical Analysis**: Scan statistics and performance tracking
- **Export Options**: CSV, JSON data export capabilities
- **Comprehensive Logs**: All operations timestamped and categorized

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLite, scikit-learn
- **Frontend**: React 18+, Vite, Tailwind CSS
- **Security**: ClamAV, VirusTotal API
- **ML**: RandomForestClassifier, feature engineering
- **Deployment**: Uvicorn, Node.js

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.11+** (with pip/conda)
- **Node.js 18+** (with npm)
- **Windows 10/11** (tested environment)

### Method 1: Automated Setup (Recommended)

#### Step 1: Clone & Navigate
```powershell
# Navigate to project directory
cd "projectfolder path"
```

#### Step 2: Quick Start with Terminal UI
```powershell
# Run the quickstart script with interactive terminal UI
cd backend
python quickstart.py
```

**The `quickstart.py` script will:**
- ✅ Check Python environment and dependencies
- ✅ Install missing packages automatically
- ✅ Initialize SQLite database
- ✅ Start FastAPI backend server
- ✅ Provide terminal-based UI for file operations
- ✅ Display real-time scan progress and statistics

#### Step 3: Start Frontend (Optional)
```powershell
# In a new terminal window
cd frontend
npm install
npm run dev
```

### Method 2: Manual Setup

#### Backend Setup
```powershell
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```

---

## 📱 Usage Examples

### Terminal UI (via quickstart.py)
```powershell
cd backend
python quickstart.py

# Interactive menu will appear:
# [1] Scan Directory
# [2] Full Drive Scan  
# [3] Organize Files
# [4] Security Scan
# [5] View Statistics
# [6] Settings
```

### Full Drive Scan Script
```powershell
# Automated E:\ drive scan with CSV export
python run_full_scan.py
```

### System Tray Integration
```powershell
# Launch system tray for quick access
python system_tray.py
```

### Web UI Access
- **Frontend**: http://localhost:3000 or http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 🎯 API Usage Examples

### Start File Scan
```python
import requests

# Start directory scan
response = requests.post('http://127.0.0.1:8000/api/scan', json={
    "folder_path": "E:\\MyDocuments",
    "recursive": True,
    "export_csv": True
})
```

### Monitor Progress
```python
# Get real-time progress
progress = requests.get('http://127.0.0.1:8000/api/scan/progress')
print(f"Progress: {progress.json()['progress']}%")
```

### PowerShell Monitoring
```powershell
# Real-time scan monitoring
while ($true) {
    $status = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/scan/progress' -Method GET
    Write-Progress -Activity $status.current_operation -PercentComplete $status.progress
    if (-not $status.is_busy) { break }
    Start-Sleep -Seconds 2
}
```

---

## 📁 Project Structure

```
.
├── .env
├── .gitignore
├── backend/
│   ├── .env
│   ├── main.py
│   ├── quickstart.py
│   ├── requirements.txt
│   ├── api/
│   │   ├── delete.py
│   │   ├── logs.py
│   │   ├── ml_operations.py
│   │   ├── organize.py
│   │   ├── scan.py
│   │   ├── settings.py
│   │   └── virus_scan.py
│   ├── database/
│   │   └── db.py
│   ├── logs/
│   ├── ml_model/
│   │   ├── predictor.py
│   │   └── train_model.py
│   ├── quarantine/
│   └── utils/
│       ├── email_notifications.py
│       ├── file_utils.py
│       ├── logger.py
│       └── speech_notifications.py
├── docs.md
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   ├── vite.config.js
│   └── src/
├── logs/
├── README.md
├── run_full_scan.py
└── system_tray.py
```

---

## 🔧 Configuration

### Environment Variables

Create two `.env` files for configuration.

**1. Root `.env` file:**
Create a file named `.env` in the project's root directory.

```env
# .env

# --- VirusTotal API (Optional but Recommended) ---
# Provides enhanced malware scanning capabilities.
VIRUSTOTAL_API_KEY=your_virustotal_api_key_here

# --- ClamAV Antivirus Engine (Optional) ---
# Host for the ClamAV daemon. Default is localhost.
CLAMAV_HOST=127.0.0.1

# --- Database Configuration ---
# URL for the SQLite database.
DB_URL=sqlite:///backend/database/app.db

# --- Application Settings ---
# Enable/disable speech notifications.
ENABLE_SPEECH=true

# --- Machine Learning Model ---
# Automatically retrain the model if performance drops.
MODEL_AUTO_RETRAIN=true
# Confidence level required for file classification.
CONFIDENCE_THRESHOLD=0.7
```

**2. Backend `.env` file:**
Create a file named `.env` inside the `backend/` directory.

```env
# backend/.env

# --- Email Notification Settings (for Gmail) ---
# Used to send email alerts for completed tasks.
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
```

### Windows Safety Exclusions
Automatically excludes system folders:
- `System Volume Information`
- `$Recycle.Bin` 
- `Windows\WinSxS`
- `Windows\System32\DriverStore`

---

## 📊 Performance Metrics

### Recent Test Results (October 2025)
- **Files Scanned**: 9,786 files
- **Total Size**: 9.1 GB processed
- **Scan Duration**: 502 seconds (~8.4 minutes)
- **Accuracy**: 96.7% correct file classification
- **System Impact**: Zero crashes or memory leaks

---

## 🚨 Troubleshooting

### Quick Fixes
```powershell
# Check backend health
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health'

# Restart with verbose logging
cd backend
python main.py --log-level debug

# Clear frontend cache
cd frontend
npm cache clean --force
npm install
```

### Common Issues
- **Database Error**: Ensure `logs/` directory exists
- **Permission Denied**: Run PowerShell as Administrator
- **Port Conflicts**: Change ports in config files
- **Missing Dependencies**: Run `pip install -r requirements.txt`

---

## 🛡️ Security Features

- **Multi-layer Detection**: Local + Cloud scanning
- **Safe Quarantine**: Threat isolation system
- **Audit Logging**: Complete operation history
- **Privacy First**: Local processing with optional cloud features

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/awesome-feature`)
3. Commit changes (`git commit -m 'Add awesome feature'`)
4. Push to branch (`git push origin feature/awesome-feature`)
5. Open Pull Request

---

## 📄 License

Educational and non-commercial use only.

---

## 🙏 Acknowledgments

- **FastAPI** - High-performance web framework
- **React + Vite** - Modern frontend development
- **Tailwind CSS** - Utility-first CSS framework  
- **scikit-learn** - Machine learning toolkit
- **ClamAV** - Open-source antivirus engine
- **VirusTotal** - Comprehensive file analysis

---

<div align="center">

**🎯 Production Ready • 🔒 Security Focused • 🤖 AI Powered**

*Built with ❤️ for intelligent file management*

[⭐ Star this project](https://github.com/HarshTiwari1131/NeonValut) | [🐛 Report Bug](https://github.com/HarshTiwari1131/NeonVault/issues) | [💡 Request Feature](https://github.com/HarshTiwari1131/NeonValut/issues)

</div>
