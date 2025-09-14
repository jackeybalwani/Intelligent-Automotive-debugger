# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## System Architecture

This is an **Intelligent Automotive Debugger** - a desktop application that analyzes automotive log files using AI. The system follows a three-tier architecture:

### Frontend (React + Electron)
- **Location**: `/src/` - React 18.2 + TypeScript frontend
- **Port**: 3000 (dev), bundled in Electron for production
- **Key Components**: Drag-drop upload, real-time progress, AI chat interface

### Backend (Python FastAPI)
- **Location**: `/python-backend/` - FastAPI 0.109 with async/await
- **Port**: 8000
- **Entry Point**: `main.py` - FastAPI application with WebSocket support

### Core Backend Modules
- **`parsers/`**: Auto-detection and format-specific parsing (CAN, LIN, UDS, DBC)
  - `auto_detector.py` - Smart format detection engine
  - `can_parser.py`, `dbc_parser.py` - Core automotive protocol parsers
- **`analyzers/`**: Analysis engines for error detection and pattern analysis
  - `error_detector.py` - J1939, UDS, bus-off detection
  - `pattern_analyzer.py` - Message frequency and bus load analysis
- **`ai/`**: Local AI integration
  - `ollama_manager.py` - Manages Llama 3.2:3b model (8K context)
  - `nlp_engine.py` - Natural language query processing
- **`database/`**: SQLAlchemy models for SQLite persistence

## Development Commands

### Start Development Environment
```bash
# Start all services (React + Electron + Python backend)
npm start

# Individual services
npm run react:start                    # Frontend only
cd python-backend && python main.py   # Backend only
npm run electron:start                 # Electron only (after frontend running)
```

### Build and Distribution
```bash
npm run build          # Development build
npm run dist           # Cross-platform distribution
npm run dist:win       # Windows installer
npm test               # Run React frontend tests
```

### Setup and Dependencies
```bash
python setup.py                                          # Automated setup script (recommended)
npm install                                              # Node.js dependencies
pip install -r python-backend/requirements.txt          # Python dependencies
ollama pull llama3.2:3b                                 # AI model (2GB download)
cd python-backend && pytest                             # Run Python backend tests
```

## Architecture Patterns

### Data Flow
1. **File Upload**: Frontend drag-drop → FastAPI `/api/upload` → Auto-detection → Database
2. **Analysis**: File selection → `/api/analyze` → Multiple analyzer modules → Results aggregation
3. **AI Queries**: Natural language → `/api/nlp/query` → Ollama/Llama → Enhanced response

### Real-time Communication
- **WebSocket** at `/ws` for progress updates during file processing and analysis
- **Broadcast pattern** for multi-client updates via `broadcast_update()` function

### Database Schema
- **SQLite** with SQLAlchemy ORM
- **Key tables**: `uploaded_files`, `analysis_sessions`, `analysis_history`, `pattern_library`
- **Models location**: `python-backend/database/models.py`

### File Processing Pipeline
1. **Auto-detection** via extension, magic bytes, and content analysis
2. **Chunked processing** (10K message chunks) for large automotive logs
3. **Format-specific parsers** with common interface pattern

## Technology Integration

### AI Stack
- **Ollama service** running locally on default port
- **Llama 3.2:3b model** with Q4_K_M quantization
- **Automotive expertise** built into system prompts

### Frontend Stack
- **Electron 38.1** with context isolation and preload scripts
- **React 18.2** with TypeScript for type safety
- **WebSocket client** for real-time updates

### Automotive Protocols Supported
- **CAN** (ASC, BLF, TRC formats)
- **DBC** signal definitions for message decoding
- **LIN** protocol messages
- **UDS** diagnostic services
- **J1939** commercial vehicle protocols

## File Locations

### Configuration
- **Main Electron process**: `electron/main.js`
- **Package scripts**: `package.json` (build, start, distribution)
- **Python requirements**: `python-backend/requirements.txt`

### Key Entry Points
- **React app**: `src/App.tsx` - Main application component
- **FastAPI app**: `python-backend/main.py` - Backend server with all endpoints
- **Database init**: `python-backend/database/models.py` - Schema and session management

## Development Notes

### Error Handling
- **Frontend**: React error boundaries and async error handling
- **Backend**: Comprehensive exception catching with logging
- **Database**: Session management with proper cleanup in finally blocks

### File Constraints
- **Upload limit**: 10MB per file (configurable in `electron/main.js`)
- **Supported formats**: CAN ASC/BLF/TRC, LIN, UDS, DBC, PCAP
- **Storage**: Local filesystem with database metadata tracking

### Performance Considerations
- **Chunked parsing** for large automotive logs
- **Streaming responses** for real-time analysis feedback
- **Memory optimization** through generator patterns in parsers

## System Requirements and Troubleshooting

### Prerequisites
- **OS**: Windows 10/11 (64-bit), macOS, or Linux
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 5GB free space (2GB for AI model)
- **CPU**: 4 cores minimum, 8 cores recommended

### Port Configuration
- **Frontend (React)**: Port 3000
- **Backend (FastAPI)**: Port 8000
- **Ollama AI Service**: Port 11434 (default)

### Common Troubleshooting Commands
```bash
# Check Ollama service status
ollama list

# Restart Ollama service
ollama serve

# Re-download AI model
ollama pull llama3.2:3b

# Backend health check
curl http://localhost:8000/api/health

# Check backend manually
cd python-backend && python main.py
```