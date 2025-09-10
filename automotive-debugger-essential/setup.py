"""
Setup and Installation Script for Automotive Debug Log Analyzer
Handles all dependencies including Ollama installation
"""

import os
import sys
import subprocess
import platform
import shutil
import json
import urllib.request
import zipfile
import tarfile
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutoDebuggerInstaller:
    """
    Complete installer for Automotive Debug Log Analyzer
    """
    
    def __init__(self):
        self.system = platform.system()
        self.machine = platform.machine()
        self.base_dir = Path.cwd()
        self.deps_installed = []
        
    def run(self):
        """Main installation process"""
        logger.info("🚀 Starting Automotive Debug Log Analyzer Installation")
        logger.info(f"System: {self.system}, Architecture: {self.machine}")
        
        try:
            # Step 1: Check Python version
            self.check_python_version()
            
            # Step 2: Install Node.js dependencies
            self.install_node_dependencies()
            
            # Step 3: Install Python dependencies
            self.install_python_dependencies()
            
            # Step 4: Install and setup Ollama
            self.install_ollama()
            
            # Step 5: Download Llama model
            self.download_llama_model()
            
            # Step 6: Setup databases
            self.setup_databases()
            
            # Step 7: Create desktop shortcuts
            self.create_shortcuts()
            
            # Step 8: Verify installation
            self.verify_installation()
            
            logger.info("✅ Installation completed successfully!")
            logger.info("Run 'npm start' to launch the application")
            
        except Exception as e:
            logger.error(f"❌ Installation failed: {e}")
            sys.exit(1)
    
    def check_python_version(self):
        """Check if Python 3.12 is installed"""
        logger.info("Checking Python version...")
        
        python_version = sys.version_info
        if python_version.major != 3 or python_version.minor < 12:
            logger.error(f"Python 3.12+ required, found {python_version.major}.{python_version.minor}")
            
            if self.system == "Windows":
                logger.info("Downloading Python 3.12...")
                self.download_and_install_python_windows()
            else:
                logger.error("Please install Python 3.12 manually")
                sys.exit(1)
    
    def install_node_dependencies(self):
        """Install Node.js dependencies"""
        logger.info("Installing Node.js dependencies...")
        
        # Check if npm is installed
        if not shutil.which('npm'):
            logger.error("npm not found. Please install Node.js first")
            if self.system == "Windows":
                self.download_and_install_node_windows()
            else:
                logger.error("Please install Node.js manually from https://nodejs.org")
                sys.exit(1)
        
        # Install npm packages
        subprocess.run(['npm', 'install'], check=True, cwd=self.base_dir)
        logger.info("✓ Node.js dependencies installed")
    
    def install_python_dependencies(self):
        """Install Python dependencies"""
        logger.info("Installing Python dependencies...")
        
        # Upgrade pip
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
        
        # Install requirements
        requirements_file = self.base_dir / 'python-backend' / 'requirements.txt'
        if requirements_file.exists():
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', str(requirements_file)
            ], check=True)
        
        logger.info("✓ Python dependencies installed")
    
    def install_ollama(self):
        """Install Ollama for local LLM"""
        logger.info("Installing Ollama...")
        
        # Check if Ollama is already installed
        if shutil.which('ollama'):
            logger.info("✓ Ollama already installed")
            return
        
        if self.system == "Windows":
            self.install_ollama_windows()
        elif self.system == "Darwin":  # macOS
            self.install_ollama_mac()
        else:  # Linux
            self.install_ollama_linux()
    
    def install_ollama_windows(self):
        """Install Ollama on Windows"""
        logger.info("Downloading Ollama for Windows...")
        
        # Download Ollama installer
        ollama_url = "https://ollama.ai/download/OllamaSetup.exe"
        installer_path = self.base_dir / "OllamaSetup.exe"
        
        urllib.request.urlretrieve(ollama_url, installer_path)
        
        # Run installer silently
        logger.info("Installing Ollama...")
        subprocess.run([str(installer_path), '/S'], check=True)
        
        # Clean up
        installer_path.unlink()
        
        logger.info("✓ Ollama installed successfully")
    
    def install_ollama_mac(self):
        """Install Ollama on macOS"""
        logger.info("Installing Ollama via brew...")
        
        # Check if brew is installed
        if not shutil.which('brew'):
            logger.info("Installing Homebrew first...")
            install_brew_cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
            subprocess.run(install_brew_cmd, shell=True, check=True)
        
        # Install Ollama
        subprocess.run(['brew', 'install', 'ollama'], check=True)
        
        logger.info("✓ Ollama installed successfully")
    
    def install_ollama_linux(self):
        """Install Ollama on Linux"""
        logger.info("Installing Ollama for Linux...")
        
        # Download and run install script
        install_cmd = "curl -fsSL https://ollama.ai/install.sh | sh"
        subprocess.run(install_cmd, shell=True, check=True)
        
        logger.info("✓ Ollama installed successfully")
    
    def download_llama_model(self):
        """Download Llama 3.2:3b model"""
        logger.info("Downloading Llama 3.2:3b model (this may take a while)...")
        
        try:
            # Start Ollama service if not running
            if self.system == "Windows":
                subprocess.Popen(['ollama', 'serve'], shell=True)
            
            # Wait for service to start
            import time
            time.sleep(5)
            
            # Pull the model
            subprocess.run(['ollama', 'pull', 'llama3.2:3b'], check=True)
            
            logger.info("✓ Llama 3.2:3b model downloaded")
            
        except Exception as e:
            logger.warning(f"Could not download model automatically: {e}")
            logger.info("Please run 'ollama pull llama3.2:3b' manually after installation")
    
    def setup_databases(self):
        """Initialize SQLite and DuckDB databases"""
        logger.info("Setting up databases...")
        
        # Create database directory
        db_dir = self.base_dir / 'database'
        db_dir.mkdir(exist_ok=True)
        
        # Initialize SQLite database
        import sqlite3
        conn = sqlite3.connect(db_dir / 'app.db')
        
        # Create tables
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                file_path TEXT NOT NULL,
                file_hash TEXT UNIQUE,
                analysis_result JSON,
                ai_insights JSON,
                user_notes TEXT
            );
            
            CREATE TABLE IF NOT EXISTS pattern_library (
                id INTEGER PRIMARY KEY,
                pattern_hash TEXT UNIQUE,
                pattern_type TEXT,
                description TEXT,
                occurrence_count INTEGER DEFAULT 1,
                first_seen DATETIME,
                last_seen DATETIME,
                solution JSON,
                confidence_score REAL
            );
            
            CREATE TABLE IF NOT EXISTS tool_configs (
                tool_name TEXT PRIMARY KEY,
                version TEXT,
                install_path TEXT,
                import_settings JSON,
                last_used DATETIME
            );
        ''')
        
        conn.commit()
        conn.close()
        
        # Initialize DuckDB
        try:
            import duckdb
            duck_conn = duckdb.connect(str(db_dir / 'analytics.duckdb'))
            
            duck_conn.execute('''
                CREATE TABLE IF NOT EXISTS can_messages (
                    timestamp TIMESTAMP,
                    can_id INTEGER,
                    dlc INTEGER,
                    data BLOB,
                    channel INTEGER,
                    error_flag BOOLEAN
                )
            ''')
            
            duck_conn.close()
        except ImportError:
            logger.warning("DuckDB not installed, skipping analytics database setup")
        
        logger.info("✓ Databases initialized")
    
    def create_shortcuts(self):
        """Create desktop shortcuts"""
        logger.info("Creating desktop shortcuts...")
        
        if self.system == "Windows":
            self.create_windows_shortcut()
        elif self.system == "Darwin":
            self.create_mac_app()
        else:
            self.create_linux_desktop()
    
    def create_windows_shortcut(self):
        """Create Windows desktop shortcut"""
        try:
            import win32com.client
            
            desktop = Path.home() / 'Desktop'
            shortcut_path = desktop / 'Automotive Debugger.lnk'
            
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.Targetpath = 'cmd.exe'
            shortcut.Arguments = f'/c "cd /d {self.base_dir} && npm start"'
            shortcut.WorkingDirectory = str(self.base_dir)
            shortcut.IconLocation = str(self.base_dir / 'assets' / 'icons' / 'icon.ico')
            shortcut.save()
            
            logger.info("✓ Desktop shortcut created")
            
        except ImportError:
            logger.warning("pywin32 not installed, skipping shortcut creation")
    
    def create_mac_app(self):
        """Create macOS application"""
        # Implementation for macOS .app creation
        pass
    
    def create_linux_desktop(self):
        """Create Linux desktop entry"""
        desktop_entry = f"""[Desktop Entry]
Name=Automotive Debugger
Comment=AI-powered automotive log analyzer
Exec=sh -c 'cd {self.base_dir} && npm start'
Icon={self.base_dir}/assets/icons/icon.png
Terminal=false
Type=Application
Categories=Development;
"""
        
        desktop_file = Path.home() / '.local' / 'share' / 'applications' / 'automotive-debugger.desktop'
        desktop_file.parent.mkdir(parents=True, exist_ok=True)
        desktop_file.write_text(desktop_entry)
        
        # Make it executable
        os.chmod(desktop_file, 0o755)
        
        logger.info("✓ Desktop entry created")
    
    def verify_installation(self):
        """Verify all components are installed correctly"""
        logger.info("Verifying installation...")
        
        checks = {
            'Node.js': shutil.which('node') is not None,
            'npm': shutil.which('npm') is not None,
            'Python': sys.version_info >= (3, 12),
            'Ollama': shutil.which('ollama') is not None,
            'Database': (self.base_dir / 'database' / 'app.db').exists()
        }
        
        all_good = True
        for component, status in checks.items():
            if status:
                logger.info(f"✓ {component}: OK")
            else:
                logger.error(f"✗ {component}: FAILED")
                all_good = False
        
        if not all_good:
            raise Exception("Installation verification failed")
        
        logger.info("✓ All components verified successfully")
    
    def download_and_install_python_windows(self):
        """Download and install Python on Windows"""
        python_url = "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"
        installer_path = self.base_dir / "python_installer.exe"
        
        logger.info("Downloading Python 3.12...")
        urllib.request.urlretrieve(python_url, installer_path)
        
        logger.info("Installing Python 3.12...")
        subprocess.run([
            str(installer_path),
            '/quiet',
            'InstallAllUsers=1',
            'PrependPath=1'
        ], check=True)
        
        installer_path.unlink()
        logger.info("✓ Python 3.12 installed")
    
    def download_and_install_node_windows(self):
        """Download and install Node.js on Windows"""
        node_url = "https://nodejs.org/dist/v20.10.0/node-v20.10.0-x64.msi"
        installer_path = self.base_dir / "node_installer.msi"
        
        logger.info("Downloading Node.js...")
        urllib.request.urlretrieve(node_url, installer_path)
        
        logger.info("Installing Node.js...")
        subprocess.run(['msiexec', '/i', str(installer_path), '/quiet'], check=True)
        
        installer_path.unlink()
        logger.info("✓ Node.js installed")

def main():
    """Main entry point"""
    installer = AutoDebuggerInstaller()
    installer.run()

if __name__ == "__main__":
    main()
