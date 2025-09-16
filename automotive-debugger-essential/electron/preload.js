const { contextBridge, ipcRenderer } = require('electron');

/**
 * Secure IPC Bridge for Automotive Debugger
 * Exposes safe APIs to the renderer process
 */
contextBridge.exposeInMainWorld('electron', {
  // File system operations
  openFileDialog: () => ipcRenderer.invoke('dialog:openFile'),
  openFolderDialog: () => ipcRenderer.invoke('dialog:openFolder'),
  saveFileDialog: (defaultPath) => ipcRenderer.invoke('save-file-dialog', defaultPath),
  readFiles: (filePaths) => ipcRenderer.invoke('files:read', filePaths),

  // Application control
  minimizeApp: () => ipcRenderer.invoke('window:minimize'),
  maximizeApp: () => ipcRenderer.invoke('window:maximize'),
  closeApp: () => ipcRenderer.invoke('window:close'),
  restoreApp: () => ipcRenderer.invoke('window:restore'),
  isMaximized: () => ipcRenderer.invoke('window:isMaximized'),

  // System information
  getAppVersion: () => ipcRenderer.invoke('app:version'),
  getPlatform: () => process.platform,
  getNodeVersion: () => process.versions.node,
  getElectronVersion: () => process.versions.electron,
  getChromeVersion: () => process.versions.chrome,

  // Backend communication helpers
  isBackendRunning: () => ipcRenderer.invoke('backend:isRunning'),
  startBackend: () => ipcRenderer.invoke('backend:start'),
  stopBackend: () => ipcRenderer.invoke('backend:stop'),
  getBackendStatus: () => ipcRenderer.invoke('backend:status'),

  // External links
  openExternal: (url) => ipcRenderer.invoke('shell:openExternal', url),

  // Auto-updater
  checkForUpdates: () => ipcRenderer.invoke('check-for-updates'),
  downloadUpdate: () => ipcRenderer.invoke('download-update'),
  installUpdate: () => ipcRenderer.invoke('install-update'),

  // Event listeners
  onBackendStatusChange: (callback) => {
    const handler = (_, ...args) => callback(...args);
    ipcRenderer.on('backend-status-change', handler);
    return () => ipcRenderer.removeListener('backend-status-change', handler);
  },

  onAppUpdate: (callback) => {
    const handler = (_, ...args) => callback(...args);
    ipcRenderer.on('app-update', handler);
    return () => ipcRenderer.removeListener('app-update', handler);
  },

  onUpdateStatus: (callback) => {
    const handler = (_, ...args) => callback(...args);
    ipcRenderer.on('update-status', handler);
    return () => ipcRenderer.removeListener('update-status', handler);
  },

  onUpdateError: (callback) => {
    const handler = (_, ...args) => callback(...args);
    ipcRenderer.on('update-error', handler);
    return () => ipcRenderer.removeListener('update-error', handler);
  },

  onDownloadProgress: (callback) => {
    const handler = (_, ...args) => callback(...args);
    ipcRenderer.on('download-progress', handler);
    return () => ipcRenderer.removeListener('download-progress', handler);
  },

  onModelDownloadProgress: (callback) => {
    const handler = (_, ...args) => callback(...args);
    ipcRenderer.on('model-download-progress', handler);
    return () => ipcRenderer.removeListener('model-download-progress', handler);
  },

  // Menu actions
  onMenuAction: (action, callback) => {
    const handler = (_, ...args) => callback(...args);
    ipcRenderer.on(`menu-${action}`, handler);
    return () => ipcRenderer.removeListener(`menu-${action}`, handler);
  },

  // Window events
  onWindowEvent: (event, callback) => {
    const handler = (_, ...args) => callback(...args);
    ipcRenderer.on(`window-${event}`, handler);
    return () => ipcRenderer.removeListener(`window-${event}`, handler);
  },

  // Analytics and logging (secure)
  logInfo: (message, data) => ipcRenderer.invoke('log:info', message, data),
  logError: (message, error) => ipcRenderer.invoke('log:error', message, error),
  logWarn: (message, data) => ipcRenderer.invoke('log:warn', message, data),

  // Development helpers (only available in development)
  ...(process.env.NODE_ENV === 'development' && {
    openDevTools: () => ipcRenderer.invoke('dev:openDevTools'),
    reloadApp: () => ipcRenderer.invoke('dev:reload'),
    getProcessInfo: () => ({
      versions: process.versions,
      platform: process.platform,
      arch: process.arch,
      pid: process.pid
    })
  })
});

// Security: Remove access to Node.js globals
delete window.require;
delete window.exports;
delete window.module;

// Expose version info
window.APP_VERSION = process.env.npm_package_version || '1.0.0';
window.ELECTRON_VERSION = process.versions.electron;
window.NODE_VERSION = process.versions.node;