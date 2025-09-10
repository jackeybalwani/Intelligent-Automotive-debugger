@echo off
echo ========================================
echo Automotive Debug Log Analyzer Setup
echo ========================================
echo.

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges...
) else (
    echo This script requires administrator privileges.
    echo Please run as administrator.
    pause
    exit /b 1
)

echo [1/7] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Installing Python 3.12...
    echo Please wait, this may take a few minutes...
    
    REM Download Python installer
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe' -OutFile 'python_installer.exe'"
    
    REM Install Python silently
    python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    
    REM Clean up
    del python_installer.exe
    
    echo Python installed successfully!
) else (
    echo Python is already installed.
)

echo.
echo [2/7] Checking Node.js installation...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Node.js not found. Installing Node.js...
    echo Please wait, this may take a few minutes...
    
    REM Download Node.js installer
    powershell -Command "Invoke-WebRequest -Uri 'https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi' -OutFile 'node_installer.msi'"
    
    REM Install Node.js silently
    msiexec /i node_installer.msi /quiet /norestart
    
    REM Clean up
    del node_installer.msi
    
    echo Node.js installed successfully!
) else (
    echo Node.js is already installed.
)

echo.
echo [3/7] Installing Ollama...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Downloading Ollama...
    
    REM Download Ollama installer
    powershell -Command "Invoke-WebRequest -Uri 'https://ollama.ai/download/OllamaSetup.exe' -OutFile 'OllamaSetup.exe'"
    
    REM Install Ollama
    echo Installing Ollama (this may open a new window)...
    start /wait OllamaSetup.exe /S
    
    REM Clean up
    del OllamaSetup.exe
    
    echo Ollama installed successfully!
) else (
    echo Ollama is already installed.
)

echo.
echo [4/7] Installing Node.js dependencies...
call npm install
if %errorlevel% neq 0 (
    echo Failed to install Node.js dependencies.
    pause
    exit /b 1
)

echo.
echo [5/7] Installing Python dependencies...
pip install -r python-backend\requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install Python dependencies.
    pause
    exit /b 1
)

echo.
echo [6/7] Starting Ollama service...
start /B ollama serve >nul 2>&1
timeout /t 5 /nobreak >nul

echo.
echo [7/7] Downloading Llama 3.2:3b model (2GB)...
echo This will take several minutes depending on your internet speed...
ollama pull llama3.2:3b
if %errorlevel% neq 0 (
    echo Warning: Failed to download AI model.
    echo You can download it later by running: ollama pull llama3.2:3b
) else (
    echo AI model downloaded successfully!
)

echo.
echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo To start the application, run:
echo   npm start
echo.
echo Or use the desktop shortcut after building:
echo   npm run dist:win
echo.

REM Create desktop shortcut
echo Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\Automotive Debugger.lnk'); $Shortcut.TargetPath = 'cmd.exe'; $Shortcut.Arguments = '/c cd /d %CD% && npm start'; $Shortcut.WorkingDirectory = '%CD%'; $Shortcut.IconLocation = '%CD%\assets\icons\icon.ico'; $Shortcut.Save()"

echo Desktop shortcut created!
echo.
echo Press any key to exit...
pause >nul
