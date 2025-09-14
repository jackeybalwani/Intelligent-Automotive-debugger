# 🚗 Intelligent Automotive Debugger - Setup & Run Instructions

## 📋 Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Running the Application](#running-the-application)
- [Testing the System](#testing-the-system)
- [Troubleshooting](#troubleshooting)
- [Development Mode](#development-mode)

---

## 🔧 Prerequisites

### System Requirements
- **OS**: macOS, Windows 10/11, or Linux
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 5GB free space (2GB for AI model)
- **CPU**: 4 cores minimum, 8 cores recommended

### Required Software
1. **Node.js 20+** - [Download](https://nodejs.org/)
2. **Python 3.12+** - [Download](https://python.org/downloads/)
3. **Ollama** - [Download](https://ollama.ai/download)

---

## 🚀 Quick Start

### Option 1: One-Command Setup (Recommended)
```bash
# Clone and setup everything automatically
git clone https://github.com/jackeybalwani/Intelligent-Automotive-debugger.git
cd Intelligent-Automotive-debugger/automotive-debugger-essential
python setup.py
```

### Option 2: Manual Setup
```bash
# 1. Clone repository
git clone https://github.com/jackeybalwani/Intelligent-Automotive-debugger.git
cd Intelligent-Automotive-debugger/automotive-debugger-essential

# 2. Install Node.js dependencies
npm install

# 3. Install Python dependencies
pip install -r python-backend/requirements.txt

# 4. Install and setup Ollama
# Download from https://ollama.ai/download
ollama pull llama3.2:3b

# 5. Run the application
npm start
```

---

## 🔨 Detailed Setup

### Step 1: Install Node.js Dependencies
```bash
npm install
```
**What this installs:**
- React 18.2 + TypeScript
- Electron 38.1 for desktop app
- Chart.js for visualizations
- Axios for HTTP requests
- Development tools and build scripts

### Step 2: Install Python Dependencies
```bash
cd python-backend
pip install -r requirements.txt
```
**Key packages installed:**
- FastAPI 0.109 (Web framework)
- SQLAlchemy 2.0 (Database ORM)
- Ollama 0.1.7 (AI integration)
- python-can 4.3 (CAN bus support)
- scikit-learn, pandas (Data analysis)

### Step 3: Setup AI Model
```bash
# Install Ollama service
# Download from https://ollama.ai/download and install

# Pull the Llama model (2GB download)
ollama pull llama3.2:3b

# Verify installation
ollama list
```

### Step 4: Initialize Database
```bash
# Database will be automatically created on first run
# Location: python-backend/database/app.db
```

---

## 🏃‍♂️ Running the Application

### Production Mode (Full Application)
```bash
# Start everything (React + Electron + Python backend)
npm start
```
**This launches:**
- React frontend on `http://localhost:3000`
- Python backend on `http://localhost:8000`
- Electron desktop application
- Ollama AI service

### Development Mode (Backend Only)
```bash
# Start only the Python backend for API development
cd python-backend
python start_backend.py
```
**Access points:**
- Backend API: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/health`

### Development Mode (Frontend Only)
```bash
# Start only React development server
npm run react:start
```
**Access:** `http://localhost:3000`

---

## 🧪 Testing the System

### 1. Backend Health Check
```bash
curl http://localhost:8000/api/health
```
**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-14T12:00:00.000000",
  "services": {
    "database": "connected",
    "ollama": true,
    "models_loaded": true
  }
}
```

### 2. Test File Upload
```bash
# Create a test CAN log file
echo "(0.000000) can0 123#0102030405060708" > test.log
echo "(0.001234) can0 456#DEADBEEFCAFEBABE" >> test.log

# Upload via API
curl -X POST -F "files=@test.log" http://localhost:8000/api/upload
```

### 3. Test AI Query
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"query":"What errors are in the log?","context_file_ids":["file_id_here"]}' \
  http://localhost:8000/api/nlp/query
```

### 4. Frontend Testing
1. Open desktop app or visit `http://localhost:3000`
2. Drag and drop a CAN log file
3. Click "Analyze Selected File"
4. Ask AI: "What patterns do you see in this data?"

---

## 🐛 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Kill processes on ports 3000 and 8000
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9
```

#### Ollama Not Running
```bash
# Start Ollama service
ollama serve

# In another terminal, verify
ollama list
```

#### Database Issues
```bash
# Remove and recreate database
rm python-backend/database/app.db
# Restart backend - database will be recreated
```

#### Python Dependencies
```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r python-backend/requirements.txt
```

#### Node.js Issues
```bash
# Clear npm cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Error Messages

**"Address already in use"**
- Another instance is running
- Kill existing processes or use different ports

**"Ollama service is not running"**
- Install and start Ollama service
- Ensure llama3.2:3b model is pulled

**"Database connection failed"**
- Check file permissions in python-backend/database/
- Verify SQLite is available

**"Module not found"**
- Install missing Python dependencies
- Check virtual environment activation

---

## 🛠️ Development Mode

### Backend Development
```bash
# Run with auto-reload for development
cd python-backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
# React hot-reload development
npm run react:start

# Build for production
npm run react:build
```

### Database Development
```bash
# Connect to SQLite database
sqlite3 python-backend/database/app.db

# View tables
.tables

# View uploaded files
SELECT * FROM uploaded_files;

# View analysis sessions
SELECT * FROM analysis_sessions;
```

### API Development
```bash
# Interactive API documentation
open http://localhost:8000/docs

# Alternative API docs
open http://localhost:8000/redoc
```

---

## 📁 Project Structure
```
automotive-debugger-essential/
├── 📄 package.json              # Node.js dependencies & scripts
├── 📄 SETUP_AND_RUN.md         # This file
├── 🗂️  src/                     # React frontend source
│   ├── App.tsx                  # Main React component
│   ├── App.css                  # Styling
│   └── index.tsx                # React entry point
├── 🗂️  python-backend/          # Python backend
│   ├── 📄 start_backend.py      # Easy startup script
│   ├── 📄 main.py               # FastAPI application
│   ├── 📄 requirements.txt      # Python dependencies
│   ├── 🗂️  ai/                  # AI integration
│   ├── 🗂️  analyzers/           # Log analysis engines
│   ├── 🗂️  parsers/             # File format parsers
│   ├── 🗂️  database/            # Database models
│   └── 🗂️  utils/               # Utility functions
├── 🗂️  electron/                # Electron configuration
└── 🗂️  public/                  # Static assets
```

---

## 🔗 Useful Links

- **Backend API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **System Health**: http://localhost:8000/api/health
- **Ollama Documentation**: https://ollama.ai/docs
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **React Documentation**: https://react.dev/

---

## 🆘 Getting Help

1. **Check logs**: Backend logs are displayed in terminal
2. **API Documentation**: Visit `/docs` endpoint for interactive API testing
3. **Database inspection**: Use SQLite browser or command line
4. **Health check**: Always start with `/api/health` endpoint
5. **Create issue**: Report problems on GitHub repository

---

## ✅ Success Indicators

**Application is working correctly when:**
- ✅ Health check returns "healthy" status
- ✅ Ollama shows "llama3.2:3b" model available
- ✅ File upload returns success with file_id
- ✅ Analysis generates results with errors/patterns
- ✅ AI queries return enhanced responses
- ✅ Desktop application launches without errors
- ✅ Database contains uploaded files and analysis sessions

**Ready to analyze automotive logs! 🚗💨**