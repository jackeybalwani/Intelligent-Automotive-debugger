/**
 * Main Electron Process with Auto-Update
 * Manages the desktop application lifecycle, windows, and auto-updates
 */

const { app, BrowserWindow, ipcMain, Menu, dialog, shell } = require('electron');
const { autoUpdater } = require('electron-updater');
const path = require('path');
const { spawn } = require('child_process');
const isDev = require('electron-is-dev');
const log = require('electron-log');
const fs = require('fs').promises;

// Configure logging
log.transports.file.level = 'info';
autoUpdater.logger = log;
autoUpdater.logger.transports.file.level = 'info';

// Keep a global reference of the window object
let mainWindow = null;
let pythonProcess = null;
let ollamaProcess = null;
let splashWindow = null;
let updateWindow = null;

// Enable live reload for Electron in development
if (isDev) {
  require('electron-reload')(__dirname, {
    electron: path.join(__dirname, '..', 'node_modules', '.bin', 'electron'),
    hardResetMethod: 'exit'
  });
}

// Configure auto-updater
autoUpdater.autoDownload = false;
autoUpdater.autoInstallOnAppQuit = true;

/**
 * Create update window for showing update progress
 */
function createUpdateWindow() {
  updateWindow = new BrowserWindow({
    width: 500,
    height: 350,
    frame: false,
    alwaysOnTop: true,
    resizable: false,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  updateWindow.loadFile(path.join(__dirname, 'update.html'));
  
  updateWindow.on('closed', () => {
    updateWindow = null;
  });
}

/**
 * Create splash screen window
 */
function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 600,
    height: 400,
    frame: false,
    alwaysOnTop: true,
    transparent: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  splashWindow.loadFile(path.join(__dirname, 'splash.html'));
  
  splashWindow.on('closed', () => {
    splashWindow = null;
  });
}

/**
 * Create the main application window
 */
function createMainWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1600,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    show: false,
    icon: path.join(__dirname, '../assets/icons/icon.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: !isDev
    },
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    frame: process.platform !== 'darwin'
  });

  // Load the app
  const startUrl = isDev 
    ? 'http://localhost:3000' 
    : `file://${path.join(__dirname, '../build/index.html')}`;
  
  mainWindow.loadURL(startUrl);

  // Open DevTools in development
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    if (splashWindow) {
      setTimeout(() => {
        splashWindow.close();
        mainWindow.show();
        
        // Check for updates after window is shown
        if (!isDev) {
          checkForUpdates();
        }
      }, 1500);
    } else {
      mainWindow.show();
      
      // Check for updates after window is shown
      if (!isDev) {
        checkForUpdates();
      }
    }
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Handle file drops
  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (url.startsWith('file://')) {
      event.preventDefault();
    }
  });

  // Set up the application menu
  const menu = createApplicationMenu(mainWindow);
  Menu.setApplicationMenu(menu);
}

/**
 * Check for application updates
 */
function checkForUpdates() {
  autoUpdater.checkForUpdates();
}

/**
 * Setup auto-updater event handlers
 */
function setupAutoUpdater() {
  autoUpdater.on('checking-for-update', () => {
    log.info('Checking for updates...');
    if (mainWindow) {
      mainWindow.webContents.send('update-status', 'Checking for updates...');
    }
  });

  autoUpdater.on('update-available', (info) => {
    log.info('Update available:', info);
    
    // Show confirmation dialog
    dialog.showMessageBox(mainWindow, {
      type: 'info',
      title: 'Update Available',
      message: `A new version ${info.version} is available. Current version is ${app.getVersion()}.`,
      detail: 'Would you like to download and install it now?',
      buttons: ['Yes, Update Now', 'Later'],
      defaultId: 0,
      cancelId: 1
    }).then((result) => {
      if (result.response === 0) {
        // User chose to update
        createUpdateWindow();
        autoUpdater.downloadUpdate();
      }
    });
  });

  autoUpdater.on('update-not-available', (info) => {
    log.info('Update not available:', info);
    if (mainWindow) {
      mainWindow.webContents.send('update-status', 'Application is up to date');
    }
  });

  autoUpdater.on('error', (err) => {
    log.error('Update error:', err);
    if (updateWindow) {
      updateWindow.close();
    }
    
    dialog.showErrorBox('Update Error', 
      'An error occurred while checking for updates. Please try again later.');
    
    if (mainWindow) {
      mainWindow.webContents.send('update-error', err.message);
    }
  });

  autoUpdater.on('download-progress', (progressObj) => {
    let log_message = "Download speed: " + progressObj.bytesPerSecond;
    log_message = log_message + ' - Downloaded ' + progressObj.percent + '%';
    log_message = log_message + ' (' + progressObj.transferred + "/" + progressObj.total + ')';
    
    log.info(log_message);
    
    // Send progress to update window
    if (updateWindow) {
      updateWindow.webContents.send('download-progress', progressObj);
    }
    
    // Also send to main window
    if (mainWindow) {
      mainWindow.webContents.send('download-progress', progressObj);
    }
  });

  autoUpdater.on('update-downloaded', (info) => {
    log.info('Update downloaded:', info);
    
    if (updateWindow) {
      updateWindow.close();
    }
    
    // Show confirmation to restart
    dialog.showMessageBox(mainWindow, {
      type: 'info',
      title: 'Update Ready',
      message: 'Update has been downloaded.',
      detail: 'The application will restart to apply the update.',
      buttons: ['Restart Now', 'Restart Later'],
      defaultId: 0,
      cancelId: 1
    }).then((result) => {
      if (result.response === 0) {
        autoUpdater.quitAndInstall();
      }
    });
  });
}

/**
 * Create application menu
 */
function createApplicationMenu(window) {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Open Log Files...',
          accelerator: 'CmdOrCtrl+O',
          click: () => {
            window.webContents.send('menu-open-files');
          }
        },
        {
          label: 'Open DBC File...',
          accelerator: 'CmdOrCtrl+D',
          click: () => {
            window.webContents.send('menu-open-dbc');
          }
        },
        { type: 'separator' },
        {
          label: 'Exit',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        { role: 'selectAll' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'Check for Updates...',
          click: () => {
            checkForUpdates();
          }
        },
        { type: 'separator' },
        {
          label: 'Documentation',
          click: () => {
            shell.openExternal('https://github.com/your-repo/automotive-debugger/wiki');
          }
        },
        {
          label: 'Report Issue',
          click: () => {
            shell.openExternal('https://github.com/your-repo/automotive-debugger/issues');
          }
        },
        { type: 'separator' },
        {
          label: 'About',
          click: () => {
            dialog.showMessageBox(window, {
              type: 'info',
              title: 'About Automotive Debugger',
              message: 'Automotive Debug Log Analyzer',
              detail: `Version: ${app.getVersion()}\nElectron: ${process.versions.electron}\nNode: ${process.versions.node}\n\nAI-powered automotive log analysis and debugging tool.`,
              buttons: ['OK']
            });
          }
        }
      ]
    }
  ];

  return Menu.buildFromTemplate(template);
}

/**
 * Start Python backend server (only in production mode)
 * In development, we expect the backend to be started via npm scripts
 */
async function startPythonBackend() {
  return new Promise((resolve, reject) => {
    // In development mode, don't start our own Python backend
    // The npm start script handles this via concurrently
    if (isDev) {
      log.info('Development mode: Skipping Python backend startup (handled by npm scripts)');
      resolve();
      return;
    }

    // Production mode: start the bundled Python backend
    const pythonExecutable = path.join(process.resourcesPath, 'python-backend', 'main.exe');

    log.info('Starting Python backend:', pythonExecutable);

    try {
      pythonProcess = spawn(pythonExecutable, [], {
        env: {
          ...process.env,
          PYTHONUNBUFFERED: '1'
        }
      });

      pythonProcess.stdout.on('data', (data) => {
        log.info(`Python: ${data}`);
        if (data.toString().includes('Uvicorn running on')) {
          resolve();
        }
      });

      pythonProcess.stderr.on('data', (data) => {
        log.error(`Python Error: ${data}`);
      });

      pythonProcess.on('error', (error) => {
        log.error('Failed to start Python backend:', error);
        reject(error);
      });

      pythonProcess.on('exit', (code) => {
        log.info(`Python backend exited with code ${code}`);
        pythonProcess = null;
      });

      // Set a timeout for startup
      setTimeout(() => {
        resolve(); // Resolve anyway after timeout
      }, 10000);
    } catch (error) {
      log.error('Error starting Python backend:', error);
      reject(error);
    }
  });
}

/**
 * Start Ollama service
 */
async function startOllama() {
  return new Promise((resolve) => {
    // Check if Ollama is already running
    const checkOllama = spawn('ollama', ['list'], {
      shell: true,
      windowsHide: true
    });

    checkOllama.on('error', () => {
      // Ollama not found or not running, try to start it
      log.info('Starting Ollama service...');
      
      ollamaProcess = spawn('ollama', ['serve'], {
        shell: true,
        detached: true,
        windowsHide: true
      });

      ollamaProcess.unref();
      
      // Give Ollama time to start
      setTimeout(resolve, 3000);
    });

    checkOllama.on('exit', (code) => {
      if (code === 0) {
        log.info('Ollama is already running');
        resolve();
      } else {
        // Try to start Ollama
        log.info('Starting Ollama service...');
        
        ollamaProcess = spawn('ollama', ['serve'], {
          shell: true,
          detached: true,
          windowsHide: true
        });

        ollamaProcess.unref();
        
        // Give Ollama time to start
        setTimeout(resolve, 3000);
      }
    });
  });
}

/**
 * Download Llama model if not present
 */
async function ensureLlamaModel() {
  return new Promise((resolve) => {
    log.info('Checking for Llama 3.2:3b model...');
    
    const pullProcess = spawn('ollama', ['pull', 'llama3.2:3b'], {
      shell: true
    });

    pullProcess.stdout.on('data', (data) => {
      log.info(`Ollama: ${data}`);
      if (mainWindow && mainWindow.webContents) {
        mainWindow.webContents.send('model-download-progress', data.toString());
      }
    });

    pullProcess.on('exit', () => {
      log.info('Llama model ready');
      resolve();
    });

    pullProcess.on('error', (error) => {
      log.error('Error downloading model:', error);
      resolve(); // Continue anyway
    });
  });
}

/**
 * App event handlers
 */
app.whenReady().then(async () => {
  // Setup auto-updater
  setupAutoUpdater();
  
  // Create splash window first
  createSplashWindow();

  try {
    // Start services in parallel
    await Promise.all([
      startPythonBackend(),
      startOllama()
    ]);

    // Ensure Llama model is available
    await ensureLlamaModel();

  } catch (error) {
    log.error('Error starting services:', error);
    // Continue anyway - the app can work with limited functionality
  }

  // Create main window
  createMainWindow();

  // Set up IPC handlers
  setupIpcHandlers(ipcMain, mainWindow);
});

app.on('window-all-closed', () => {
  // Cleanup Python process
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
  }

  // On macOS, keep app running even when all windows are closed
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  // On macOS, re-create window when dock icon is clicked
  if (BrowserWindow.getAllWindows().length === 0) {
    createMainWindow();
  }
});

app.on('before-quit', () => {
  // Cleanup processes
  if (pythonProcess) {
    pythonProcess.kill();
  }
  if (ollamaProcess) {
    ollamaProcess.kill();
  }
});

/**
 * IPC Main Process Handlers
 */
function setupIpcHandlers(ipcMain, mainWindow) {
  // Handle file dialog
  ipcMain.handle('dialog:openFile', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ['openFile', 'multiSelections'],
      filters: [
        { name: 'Log Files', extensions: ['log', 'txt', 'asc', 'blf', 'trc', 'csv', 'xml'] },
        { name: 'CAN Files', extensions: ['asc', 'blf', 'trc'] },
        { name: 'DBC Files', extensions: ['dbc'] },
        { name: 'All Files', extensions: ['*'] }
      ]
    });

    // Check file sizes (10MB limit)
    const validFiles = [];
    for (const filePath of result.filePaths) {
      const stats = await fs.stat(filePath);
      if (stats.size <= 10 * 1024 * 1024) { // 10MB
        validFiles.push(filePath);
      } else {
        dialog.showErrorBox('File Too Large', 
          `File ${path.basename(filePath)} exceeds 10MB limit and will be skipped.`);
      }
    }

    return validFiles;
  });

  // Handle folder dialog
  ipcMain.handle('dialog:openFolder', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ['openDirectory']
    });

    return result.filePaths;
  });

  // Handle drag and drop with size check
  ipcMain.handle('files:read', async (event, filePaths) => {
    const files = [];
    
    for (const filePath of filePaths) {
      try {
        const stats = await fs.stat(filePath);
        
        // Check file size (10MB limit)
        if (stats.size > 10 * 1024 * 1024) {
          dialog.showErrorBox('File Too Large', 
            `File ${path.basename(filePath)} exceeds 10MB limit.`);
          continue;
        }
        
        const content = await fs.readFile(filePath, 'utf-8');
        
        files.push({
          path: filePath,
          name: path.basename(filePath),
          size: stats.size,
          content: content,
          type: path.extname(filePath).toLowerCase()
        });
      } catch (error) {
        log.error(`Error reading file ${filePath}:`, error);
      }
    }
    
    return files;
  });

  // Get app version
  ipcMain.handle('app:version', () => {
    return app.getVersion();
  });

  // Open external link
  ipcMain.handle('shell:openExternal', async (event, url) => {
    await shell.openExternal(url);
  });
  
  // Manual update check
  ipcMain.handle('check-for-updates', () => {
    checkForUpdates();
  });
}

// Export functions for testing
module.exports = {
  createMainWindow,
  startPythonBackend,
  startOllama
};
