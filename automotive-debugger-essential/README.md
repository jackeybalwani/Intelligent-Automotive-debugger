# Automotive Debug Log Analyzer

AI-powered automotive log analysis and debugging tool with support for CAN, LIN, UDS, and various tool outputs.

## Features

### Priority 1 (MVP)
- ✅ **Drag-and-drop file upload** - Multiple file support up to 10MB each
- ✅ **Real-time parsing progress** - Visual feedback during processing
- ✅ **Interactive timeline with zoom** - Navigate through log data
- ✅ **Error filtering/search** - Quick error identification
- ✅ **Natural language query** - Ask questions in plain English
- ✅ **DBC file support** - Signal decoding with single DBC file
- ✅ **Dark/Light theme** - User preference support
- ✅ **Auto-update** - Automatic updates with progress bar

### Supported Formats
- **Raw Logs**: CAN (ASC, BLF, TRC), LIN, UDS, Console logs
- **Tool Outputs**: CANalyzer v18, INCA, ControlDesk, VehicleSpy
- **Data Files**: DBC, CSV, XML, Excel

### AI Features
- Natural language queries using Llama 3.2:3b (Q4_K_M quantization)
- Root cause analysis
- Predictive failure detection
- Pattern recognition
- Error explanation and fix suggestions

## System Requirements

- **OS**: Windows 10/11 (64-bit)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 5GB free space (2GB for Llama model)
- **CPU**: 4 cores minimum, 8 cores recommended
- **Network**: Required for initial setup and model download

## Quick Start

### Option 1: One-Click Installer (Recommended)

1. Download the latest release from [Releases](https://github.com/your-repo/automotive-debugger/releases)
2. Run `AutomotiveDebugger-Setup.exe`
3. Follow the installation wizard
4. Launch from desktop shortcut

### Option 2: Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/your-repo/automotive-debugger.git
cd automotive-debugger
```

2. **Run the setup script**
```bash
# Windows
setup.bat

# Or manually:
python setup.py
```

3. **Start the application**
```bash
npm start
```

## Installation Details

### Prerequisites

The setup script will automatically install:
- Python 3.12+ (if not present)
- Node.js 20+ (if not present)
- Ollama (for local AI)
- Llama 3.2:3b model (2GB download)

### Manual Installation

1. **Install Python 3.12+**
   - Download from [python.org](https://www.python.org/downloads/)
   - Add to PATH during installation

2. **Install Node.js**
   - Download from [nodejs.org](https://nodejs.org/)
   - LTS version recommended

3. **Install Ollama**
   - Windows: Download from [ollama.ai](https://ollama.ai/download)
   - Run installer

4. **Install dependencies**
```bash
# Install Node packages
npm install

# Install Python packages
pip install -r python-backend/requirements.txt

# Download Llama model
ollama pull llama3.2:3b
```

5. **Build and run**
```bash
# Development mode
npm start

# Production build
npm run dist:win
```

## Usage

### 1. Upload Files
- Drag and drop log files onto the upload area
- Or click to browse and select files
- Maximum 10MB per file
- Multiple files can be analyzed together

### 2. Load DBC File (Optional)
- Upload a DBC file for signal decoding
- Supports standard DBC format
- Single DBC file per session

### 3. Start Analysis
- Select files to analyze
- Click "Start Analysis"
- View real-time progress

### 4. View Results
- **Timeline**: Interactive visualization of log events
- **Analysis**: Error detection, patterns, predictions
- **AI Chat**: Ask questions about the logs

### 5. Natural Language Queries
Examples:
- "Why did the ECU reset?"
- "Show all CAN errors"
- "What caused the bus-off?"
- "Find patterns in the data"
- "Predict potential failures"

## Project Structure

```
automotive-debugger/
├── electron/           # Electron main process
├── src/               # React frontend
├── python-backend/    # FastAPI backend
│   ├── parsers/      # Log file parsers
│   ├── analyzers/    # Analysis engines
│   └── ai/           # AI/ML components
├── assets/           # Icons and images
└── dist/            # Build output
```

## Configuration

### AI Model Settings
- Model: Llama 3.2:3b (Q4_K_M quantization)
- Context Window: 8K tokens
- Located in: `~/.ollama/models/`

### File Size Limits
- Maximum file size: 10MB
- Configurable in: `electron/main.js`

### Update Settings
- Auto-update enabled by default
- Manual check: Help → Check for Updates
- Update server configured in `package.json`

## Troubleshooting

### Ollama Service Issues
```bash
# Check if Ollama is running
ollama list

# Start Ollama manually
ollama serve

# Re-download model
ollama pull llama3.2:3b
```

### Python Backend Issues
```bash
# Check Python version
python --version

# Reinstall dependencies
pip install -r python-backend/requirements.txt --force-reinstall

# Run backend manually
cd python-backend
python main.py
```

### Port Conflicts
- Frontend: Port 3000
- Backend: Port 8000
- Ollama: Port 11434

Change ports in:
- Frontend: `package.json`
- Backend: `python-backend/main.py`

## Development

### Build from Source
```bash
# Install dependencies
npm install
pip install -r python-backend/requirements.txt

# Development mode
npm start

# Build for Windows
npm run dist:win
```

### Testing
```bash
# Run tests
npm test

# Python tests
cd python-backend
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Support

- **Documentation**: [Wiki](https://github.com/your-repo/automotive-debugger/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-repo/automotive-debugger/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/automotive-debugger/discussions)

## Acknowledgments

- Ollama for local LLM support
- Llama model by Meta
- Electron framework
- React and FastAPI communities

---

**Version**: 1.0.0  
**Last Updated**: January 2025
