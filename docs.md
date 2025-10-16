# NeonVault: Intelligent File Organizer & Security Suite

## 1. Overview

**NeonVault** is a full-stack, intelligent file management and security platform designed to help users organize, secure, and analyze their files with advanced features. It combines a powerful Python FastAPI backend with a modern React frontend, integrating machine learning and enterprise-grade security tools to deliver a seamless and comprehensive user experience.

Whether you're a home user looking to clean up your downloads folder or an enterprise needing to enforce security policies on a shared drive, NeonVault provides the tools to do so efficiently and effectively.

---

## 2. Core Features & Use Cases

### 2.1. Intelligent File Organization
- **Use Case**: Automatically sort a chaotic folder of mixed file types into a clean, structured directory.
- **Features**:
    - **ML-Powered Categorization**: Utilizes a RandomForestClassifier to predict file categories (e.g., images, documents, code).
    - **Rule-Based Operations**: Move, delete, or quarantine files based on user-defined rules (e.g., file type, age, size).
    - **Real-time Feedback**: A modern UI with live progress bars, speech notifications, and email summaries.

### 2.2. Advanced Scanning & Cleaning
- **Use Case**: Perform a deep scan of a hard drive to identify junk files, duplicates, and potential threats.
- **Features**:
    - **Deep Scan Engine**: Recursively scans directories, analyzing file metadata, entropy, and hashes.
    - **Multi-Engine Malware Detection**: Integrates **ClamAV** for local scanning and the **VirusTotal API** for cloud-based analysis.
    - **Secure Quarantine**: Automatically isolates and logs suspicious or infected files for safe review.

### 2.3. ML Model Center
- **Use Case**: Fine-tune the file classification model based on your unique file collection for improved accuracy.
- **Features**:
    - **Custom Training**: Train and evaluate the RandomForestClassifier on your own data.
    - **AI-Powered Suggestions**: The ML model predicts file categories and flags anomalies.
    - **Model Management**: View model status, initiate retraining, and monitor performance from the UI.

### 2.4. Security & Logging
- **Use Case**: Maintain a complete audit trail of all file operations for compliance and security reviews.
- **Features**:
    - **Comprehensive Audit Trail**: All actions (move, delete, scan, quarantine) are logged to an SQLite database.
    - **System Protection**: Critical system directories are automatically excluded to prevent accidental damage.
    - **Configurable Notifications**: Receive alerts via speech, desktop pop-ups, or email.

---

## 3. Technical Architecture

- **Backend**: Python 3.11+, FastAPI, Uvicorn
- **Frontend**: React 18+, Vite, Tailwind CSS
- **Database**: SQLite for persistent logging and application settings.
- **Machine Learning**: `scikit-learn` for the classification model, `pandas` for data handling.
- **Security**: ClamAV for local antivirus scanning, VirusTotal API for cloud-based threat intelligence.
- **Notifications**: SMTP for email notifications, `pyttsx3` for text-to-speech alerts.

---

## 4. Strengths & Limitations

### Strengths
- **Unified Platform**: A single, cohesive system for file management, security, and machine learning.
- **Real-Time Feedback**: Live progress updates, notifications, and alerts keep the user informed.
- **Modern User Experience**: A visually appealing and intuitive UI with a neon/glassmorphism theme.
- **Extensible & Modular**: The backend and frontend are designed for easy feature expansion.
- **Complete Audit Trail**: Every action is logged, providing transparency and traceability.

### Limitations
- **Resource Intensive**: Deep scans and ML training can be demanding on CPU and I/O, especially on large drives.
- **ML Model Cold Start**: The initial model training requires a sufficient amount of labeled data and time to become effective.
- **Potential for False Positives**: Automated threat detection may occasionally flag safe files, requiring manual review.
- **Platform Dependencies**: Relies on external tools like ClamAV and a properly configured Python/Node.js environment.

---

## 5. Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### Installation & Setup
1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-repo/NeonVault.git
   cd NeonVault
   ```
2. **Backend Setup**:
   ```bash
   cd backend
   pip install -r requirements.txt
   # Create a .env file and add your API keys and SMTP settings
   uvicorn main:app --reload
   ```
3. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
4. **Access the application**:
   - **Web UI**: `http://localhost:5173`
   - **API Docs**: `http://localhost:8000/docs`

---

## 6. Authors & License

This project was developed by the Zaalima Internship Project Team. It is licensed under the **MIT License**.