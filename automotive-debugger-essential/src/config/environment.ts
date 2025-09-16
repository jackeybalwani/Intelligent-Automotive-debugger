/**
 * Environment Configuration
 * Centralized configuration management for the Automotive Debugger
 */

export interface AppConfig {
  // Environment
  environment: 'development' | 'production' | 'test';
  debugMode: boolean;
  logLevel: 'debug' | 'info' | 'warn' | 'error';

  // Backend Configuration
  backend: {
    url: string;
    host: string;
    port: number;
  };

  // API Configuration
  api: {
    baseUrl: string;
    endpoints: {
      upload: string;
      analyze: string;
      export: string;
      nlp: string;
      health: string;
    };
  };

  // WebSocket Configuration
  websocket: {
    url: string;
    reconnectAttempts: number;
    reconnectInterval: number;
    enabled: boolean;
  };

  // File Upload Configuration
  upload: {
    maxFileSize: number;
    allowedFileTypes: string[];
  };

  // AI/LLM Configuration
  ai: {
    ollamaUrl: string;
    model: string;
    enabled: boolean;
  };

  // Feature Flags
  features: {
    export: boolean;
    websockets: boolean;
    autoAnalysis: boolean;
    realTimeUpdates: boolean;
    devTools: boolean;
    performanceMonitor: boolean;
  };

  // Security
  security: {
    corsEnabled: boolean;
    contentSecurityPolicy: boolean;
    httpsOnly: boolean;
  };

  // Update Configuration
  updates: {
    serverUrl: string;
    autoCheck: boolean;
  };

  // Analytics
  analytics: {
    enabled: boolean;
    errorReporting: boolean;
  };
}

class EnvironmentConfig {
  private static instance: EnvironmentConfig;
  private config: AppConfig;

  private constructor() {
    this.config = this.loadConfig();
  }

  public static getInstance(): EnvironmentConfig {
    if (!EnvironmentConfig.instance) {
      EnvironmentConfig.instance = new EnvironmentConfig();
    }
    return EnvironmentConfig.instance;
  }

  private getEnvVar(key: string, defaultValue: string = ''): string {
    return process.env[key] || defaultValue;
  }

  private getEnvBool(key: string, defaultValue: boolean = false): boolean {
    const value = process.env[key];
    if (value === undefined) return defaultValue;
    return value.toLowerCase() === 'true';
  }

  private getEnvNumber(key: string, defaultValue: number = 0): number {
    const value = process.env[key];
    if (value === undefined) return defaultValue;
    const parsed = parseInt(value, 10);
    return isNaN(parsed) ? defaultValue : parsed;
  }

  private loadConfig(): AppConfig {
    // Determine environment
    const nodeEnv = process.env.NODE_ENV || 'development';
    const environment = (nodeEnv === 'production') ? 'production' : 'development';

    // Backend configuration
    const backendHost = this.getEnvVar('REACT_APP_BACKEND_HOST', 'localhost');
    const backendPort = this.getEnvNumber('REACT_APP_BACKEND_PORT', 8000);
    const backendUrl = this.getEnvVar('REACT_APP_BACKEND_URL', `http://${backendHost}:${backendPort}`);

    // API base URL
    const apiBaseUrl = this.getEnvVar('REACT_APP_API_BASE_URL', `${backendUrl}/api`);

    return {
      environment: environment as 'development' | 'production',
      debugMode: this.getEnvBool('REACT_APP_DEBUG_MODE', environment === 'development'),
      logLevel: this.getEnvVar('REACT_APP_LOG_LEVEL', environment === 'development' ? 'debug' : 'error') as any,

      backend: {
        url: backendUrl,
        host: backendHost,
        port: backendPort,
      },

      api: {
        baseUrl: apiBaseUrl,
        endpoints: {
          upload: this.getEnvVar('REACT_APP_API_UPLOAD_ENDPOINT', '/upload'),
          analyze: this.getEnvVar('REACT_APP_API_ANALYZE_ENDPOINT', '/analyze'),
          export: this.getEnvVar('REACT_APP_API_EXPORT_ENDPOINT', '/export'),
          nlp: this.getEnvVar('REACT_APP_API_NLP_ENDPOINT', '/nlp/query'),
          health: this.getEnvVar('REACT_APP_API_HEALTH_ENDPOINT', '/health'),
        },
      },

      websocket: {
        url: this.getEnvVar('REACT_APP_WS_URL', `ws://${backendHost}:${backendPort}/ws`),
        reconnectAttempts: this.getEnvNumber('REACT_APP_WS_RECONNECT_ATTEMPTS', 5),
        reconnectInterval: this.getEnvNumber('REACT_APP_WS_RECONNECT_INTERVAL', 3000),
        enabled: this.getEnvBool('REACT_APP_ENABLE_WEBSOCKETS', true),
      },

      upload: {
        maxFileSize: this.getEnvNumber('REACT_APP_MAX_FILE_SIZE', 10485760), // 10MB
        allowedFileTypes: this.getEnvVar('REACT_APP_ALLOWED_FILE_TYPES', '.log,.txt,.asc,.blf,.trc,.csv,.xml,.dbc').split(','),
      },

      ai: {
        ollamaUrl: this.getEnvVar('REACT_APP_OLLAMA_URL', 'http://localhost:11434'),
        model: this.getEnvVar('REACT_APP_OLLAMA_MODEL', 'llama3.2:3b'),
        enabled: this.getEnvBool('REACT_APP_ENABLE_AI_FEATURES', true),
      },

      features: {
        export: this.getEnvBool('REACT_APP_ENABLE_EXPORT', true),
        websockets: this.getEnvBool('REACT_APP_ENABLE_WEBSOCKETS', true),
        autoAnalysis: this.getEnvBool('REACT_APP_ENABLE_AUTO_ANALYSIS', environment === 'development'),
        realTimeUpdates: this.getEnvBool('REACT_APP_ENABLE_REAL_TIME_UPDATES', true),
        devTools: this.getEnvBool('REACT_APP_ENABLE_DEV_TOOLS', environment === 'development'),
        performanceMonitor: this.getEnvBool('REACT_APP_ENABLE_PERFORMANCE_MONITOR', environment === 'development'),
      },

      security: {
        corsEnabled: this.getEnvBool('REACT_APP_CORS_ENABLED', environment === 'development'),
        contentSecurityPolicy: this.getEnvBool('REACT_APP_ENABLE_CONTENT_SECURITY_POLICY', environment === 'production'),
        httpsOnly: this.getEnvBool('REACT_APP_ENABLE_HTTPS_ONLY', false),
      },

      updates: {
        serverUrl: this.getEnvVar('REACT_APP_UPDATE_SERVER_URL', 'https://releases.automotive-debugger.com'),
        autoCheck: this.getEnvBool('REACT_APP_AUTO_UPDATE_CHECK', environment === 'production'),
      },

      analytics: {
        enabled: this.getEnvBool('REACT_APP_ENABLE_ANALYTICS', environment === 'production'),
        errorReporting: this.getEnvBool('REACT_APP_ENABLE_ERROR_REPORTING', true),
      },
    };
  }

  public getConfig(): AppConfig {
    return this.config;
  }

  public get(key: keyof AppConfig): any {
    return this.config[key];
  }

  // Convenience methods for commonly used values
  public getApiUrl(endpoint: keyof AppConfig['api']['endpoints']): string {
    return `${this.config.api.baseUrl}${this.config.api.endpoints[endpoint]}`;
  }

  public getBackendUrl(): string {
    return this.config.backend.url;
  }

  public getWebSocketUrl(): string {
    return this.config.websocket.url;
  }

  public isDevelopment(): boolean {
    return this.config.environment === 'development';
  }

  public isProduction(): boolean {
    return this.config.environment === 'production';
  }

  public isDebugMode(): boolean {
    return this.config.debugMode;
  }

  // Development helper
  public logConfig(): void {
    if (this.isDevelopment() && this.isDebugMode()) {
      console.log('🔧 Environment Configuration:', this.config);
    }
  }
}

// Export singleton instance
export const config = EnvironmentConfig.getInstance();
export default config;