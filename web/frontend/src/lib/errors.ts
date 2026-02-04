/**
 * Error taxonomy and classification utilities for Hydra frontend.
 * Provides consistent error handling and user-friendly messages.
 */

export enum ErrorType {
  NETWORK = 'NETWORK',
  VALIDATION = 'VALIDATION',
  SERVER = 'SERVER',
  TIMEOUT = 'TIMEOUT',
  CANCELLED = 'CANCELLED',
  UNKNOWN = 'UNKNOWN',
}

export interface ClassifiedError {
  type: ErrorType;
  message: string;
  details?: string;
  originalError?: unknown;
  statusCode?: number;
}

/**
 * Classify an error into a known type based on its characteristics.
 */
export function classifyError(error: unknown): ClassifiedError {
  // Handle abort/cancellation
  if (error instanceof DOMException && error.name === 'AbortError') {
    return {
      type: ErrorType.CANCELLED,
      message: 'Operation was cancelled',
      originalError: error,
    };
  }

  // Handle fetch/network errors
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return {
      type: ErrorType.NETWORK,
      message: 'Unable to reach the server',
      details: error.message,
      originalError: error,
    };
  }

  // Handle timeout errors
  if (error instanceof Error && error.message.toLowerCase().includes('timeout')) {
    return {
      type: ErrorType.TIMEOUT,
      message: 'Request timed out',
      details: error.message,
      originalError: error,
    };
  }

  // Handle HTTP response errors
  if (error instanceof Response || (error && typeof error === 'object' && 'status' in error)) {
    const response = error as Response;
    const statusCode = response.status;

    if (statusCode >= 400 && statusCode < 500) {
      return {
        type: ErrorType.VALIDATION,
        message: getValidationMessage(statusCode),
        statusCode,
        originalError: error,
      };
    }

    if (statusCode >= 500) {
      return {
        type: ErrorType.SERVER,
        message: 'Server error occurred',
        statusCode,
        originalError: error,
      };
    }
  }

  // Handle Error objects with status property (from API errors)
  if (error instanceof Error) {
    const message = error.message.toLowerCase();

    // Check for status code patterns
    const statusMatch = message.match(/http\s*(\d{3})/i);
    if (statusMatch) {
      const statusCode = parseInt(statusMatch[1], 10);
      if (statusCode >= 400 && statusCode < 500) {
        return {
          type: ErrorType.VALIDATION,
          message: getValidationMessage(statusCode),
          details: error.message,
          statusCode,
          originalError: error,
        };
      }
      if (statusCode >= 500) {
        return {
          type: ErrorType.SERVER,
          message: 'Server error occurred',
          details: error.message,
          statusCode,
          originalError: error,
        };
      }
    }

    // Check for network-related error messages
    if (
      message.includes('network') ||
      message.includes('failed to fetch') ||
      message.includes('connection') ||
      message.includes('offline')
    ) {
      return {
        type: ErrorType.NETWORK,
        message: 'Network connection error',
        details: error.message,
        originalError: error,
      };
    }

    // Check for validation-related messages
    if (
      message.includes('invalid') ||
      message.includes('required') ||
      message.includes('missing')
    ) {
      return {
        type: ErrorType.VALIDATION,
        message: error.message,
        originalError: error,
      };
    }
  }

  // Default to unknown
  return {
    type: ErrorType.UNKNOWN,
    message: error instanceof Error ? error.message : 'An unexpected error occurred',
    originalError: error,
  };
}

function getValidationMessage(statusCode: number): string {
  switch (statusCode) {
    case 400:
      return 'Invalid request data';
    case 401:
      return 'Authentication required';
    case 403:
      return 'Access denied';
    case 404:
      return 'Resource not found';
    case 409:
      return 'Conflict with existing data';
    case 422:
      return 'Validation failed';
    case 429:
      return 'Too many requests';
    default:
      return 'Request validation failed';
  }
}

/**
 * Get a user-friendly error message based on error type.
 */
export function getErrorMessage(type: ErrorType, details?: string): string {
  switch (type) {
    case ErrorType.NETWORK:
      return 'Unable to connect to the server. Please check your internet connection and try again.';
    case ErrorType.VALIDATION:
      return details || 'The information provided is invalid. Please check your input and try again.';
    case ErrorType.SERVER:
      return 'Something went wrong on our end. Our team has been notified and is working on it.';
    case ErrorType.TIMEOUT:
      return 'The request took too long to complete. Please try again.';
    case ErrorType.CANCELLED:
      return 'The operation was cancelled.';
    case ErrorType.UNKNOWN:
    default:
      return details || 'An unexpected error occurred. Please try again or contact support if the problem persists.';
  }
}

/**
 * Get a recovery action suggestion based on error type.
 */
export interface RecoveryAction {
  label: string;
  description?: string;
}

export function getRecoveryAction(type: ErrorType): RecoveryAction | null {
  switch (type) {
    case ErrorType.NETWORK:
      return {
        label: 'Retry',
        description: 'Check your connection and try again',
      };
    case ErrorType.SERVER:
      return {
        label: 'Try Again',
        description: 'The server may be temporarily unavailable',
      };
    case ErrorType.TIMEOUT:
      return {
        label: 'Retry',
        description: 'The operation may succeed on retry',
      };
    case ErrorType.VALIDATION:
      return null; // User needs to fix their input
    case ErrorType.CANCELLED:
      return null; // User initiated cancellation
    case ErrorType.UNKNOWN:
      return {
        label: 'Try Again',
        description: 'If the problem persists, contact support',
      };
    default:
      return null;
  }
}

/**
 * Determine if an error is retryable.
 */
export function isRetryable(error: unknown): boolean {
  const classified = classifyError(error);
  return (
    classified.type === ErrorType.NETWORK ||
    classified.type === ErrorType.TIMEOUT ||
    classified.type === ErrorType.SERVER
  );
}

/**
 * Determine if an error is a client error (should not retry).
 */
export function isClientError(error: unknown): boolean {
  const classified = classifyError(error);
  return (
    classified.type === ErrorType.VALIDATION ||
    classified.type === ErrorType.CANCELLED
  );
}
