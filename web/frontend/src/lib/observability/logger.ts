/**
 * Structured frontend logger for Hydra.
 *
 * Features:
 * - Console output in development
 * - Structured JSON for production (ready for remote transport)
 * - Job ID context when available
 * - Stack trace capture for errors
 * - Non-blocking operation
 */

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
}

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  levelName: string;
  message: string;
  context?: Record<string, unknown>;
  error?: {
    name: string;
    message: string;
    stack?: string;
  };
  jobId?: string;
  userId?: string;
}

interface LoggerConfig {
  minLevel: LogLevel;
  enableConsole: boolean;
  enableRemote: boolean;
  remoteEndpoint?: string;
  batchSize: number;
  flushIntervalMs: number;
}

// Default configuration
const defaultConfig: LoggerConfig = {
  minLevel: import.meta.env.PROD ? LogLevel.INFO : LogLevel.DEBUG,
  enableConsole: true,
  enableRemote: import.meta.env.PROD,
  batchSize: 10,
  flushIntervalMs: 5000,
};

// Global context that gets attached to all log entries
let globalContext: Record<string, unknown> = {};

// Log buffer for batched remote logging
let logBuffer: LogEntry[] = [];
let flushTimer: ReturnType<typeof setTimeout> | null = null;

// Current configuration
let config: LoggerConfig = { ...defaultConfig };

/**
 * Configure the logger.
 */
export function configureLogger(options: Partial<LoggerConfig>): void {
  config = { ...config, ...options };
}

/**
 * Set global context that gets attached to all log entries.
 * Useful for job ID, user session, etc.
 */
export function setLogContext(ctx: Record<string, unknown>): void {
  globalContext = { ...globalContext, ...ctx };
}

/**
 * Clear global context.
 */
export function clearLogContext(): void {
  globalContext = {};
}

/**
 * Create a log entry.
 */
function createLogEntry(
  level: LogLevel,
  message: string,
  error?: Error,
  context?: Record<string, unknown>
): LogEntry {
  const levelNames: Record<LogLevel, string> = {
    [LogLevel.DEBUG]: 'DEBUG',
    [LogLevel.INFO]: 'INFO',
    [LogLevel.WARN]: 'WARN',
    [LogLevel.ERROR]: 'ERROR',
  };

  const entry: LogEntry = {
    timestamp: new Date().toISOString(),
    level,
    levelName: levelNames[level],
    message,
  };

  // Merge global context with local context
  const mergedContext = { ...globalContext, ...context };
  if (Object.keys(mergedContext).length > 0) {
    entry.context = mergedContext;
  }

  // Extract job ID if present
  if (mergedContext.jobId) {
    entry.jobId = mergedContext.jobId as string;
  }

  // Extract user ID if present (note: no PII should be logged)
  if (mergedContext.userId) {
    entry.userId = mergedContext.userId as string;
  }

  // Capture error details
  if (error) {
    entry.error = {
      name: error.name,
      message: error.message,
      stack: error.stack,
    };
  }

  return entry;
}

/**
 * Output to console in development-friendly format.
 */
function consoleOutput(entry: LogEntry): void {
  if (!config.enableConsole) return;

  const prefix = `[${entry.levelName}]`;
  const timestamp = entry.timestamp.split('T')[1]?.split('.')[0] || '';
  const contextStr = entry.context
    ? ` ${JSON.stringify(entry.context)}`
    : '';

  switch (entry.level) {
    case LogLevel.DEBUG:
      console.debug(`${timestamp} ${prefix} ${entry.message}${contextStr}`);
      break;
    case LogLevel.INFO:
      console.info(`${timestamp} ${prefix} ${entry.message}${contextStr}`);
      break;
    case LogLevel.WARN:
      console.warn(`${timestamp} ${prefix} ${entry.message}${contextStr}`);
      break;
    case LogLevel.ERROR:
      console.error(`${timestamp} ${prefix} ${entry.message}${contextStr}`);
      if (entry.error?.stack) {
        console.error(entry.error.stack);
      }
      break;
  }
}

/**
 * Buffer log entry for remote transport.
 */
function bufferForRemote(entry: LogEntry): void {
  if (!config.enableRemote || !config.remoteEndpoint) return;

  logBuffer.push(entry);

  // Flush if buffer is full
  if (logBuffer.length >= config.batchSize) {
    flushLogs();
    return;
  }

  // Set up flush timer if not already set
  if (!flushTimer) {
    flushTimer = setTimeout(flushLogs, config.flushIntervalMs);
  }
}

/**
 * Flush buffered logs to remote endpoint.
 * Non-blocking: errors are logged to console but don't throw.
 */
async function flushLogs(): Promise<void> {
  if (!config.remoteEndpoint || logBuffer.length === 0) return;

  // Clear timer
  if (flushTimer) {
    clearTimeout(flushTimer);
    flushTimer = null;
  }

  // Get buffered logs and clear buffer
  const logsToSend = [...logBuffer];
  logBuffer = [];

  try {
    // Use sendBeacon for reliability on page unload, otherwise fetch
    const payload = JSON.stringify(logsToSend);

    if (typeof navigator !== 'undefined' && navigator.sendBeacon) {
      navigator.sendBeacon(config.remoteEndpoint, payload);
    } else {
      await fetch(config.remoteEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: payload,
        keepalive: true,
      });
    }
  } catch {
    // Silently fail - logging should never break the app
    // In development, we can output to console
    if (!import.meta.env.PROD) {
      console.warn('[Logger] Failed to send logs to remote endpoint');
    }
  }
}

/**
 * Core logging function.
 */
function log(
  level: LogLevel,
  message: string,
  error?: Error,
  context?: Record<string, unknown>
): void {
  if (level < config.minLevel) return;

  const entry = createLogEntry(level, message, error, context);

  // Output to console (non-blocking)
  try {
    consoleOutput(entry);
  } catch {
    // Never let logging break the app
  }

  // Buffer for remote transport (non-blocking)
  try {
    bufferForRemote(entry);
  } catch {
    // Never let logging break the app
  }
}

/**
 * The logger instance.
 */
export const logger = {
  debug(message: string, context?: Record<string, unknown>): void {
    log(LogLevel.DEBUG, message, undefined, context);
  },

  info(message: string, context?: Record<string, unknown>): void {
    log(LogLevel.INFO, message, undefined, context);
  },

  warn(message: string, context?: Record<string, unknown>): void {
    log(LogLevel.WARN, message, undefined, context);
  },

  error(message: string, error?: Error, context?: Record<string, unknown>): void {
    log(LogLevel.ERROR, message, error, context);
  },

  /**
   * Create a child logger with additional context.
   */
  child(ctx: Record<string, unknown>) {
    return {
      debug: (message: string, context?: Record<string, unknown>) =>
        log(LogLevel.DEBUG, message, undefined, { ...ctx, ...context }),
      info: (message: string, context?: Record<string, unknown>) =>
        log(LogLevel.INFO, message, undefined, { ...ctx, ...context }),
      warn: (message: string, context?: Record<string, unknown>) =>
        log(LogLevel.WARN, message, undefined, { ...ctx, ...context }),
      error: (message: string, error?: Error, context?: Record<string, unknown>) =>
        log(LogLevel.ERROR, message, error, { ...ctx, ...context }),
    };
  },

  /**
   * Flush any buffered logs (useful before page unload).
   */
  flush: flushLogs,
};

// Set up flush on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
      flushLogs();
    }
  });

  window.addEventListener('pagehide', () => {
    flushLogs();
  });
}
