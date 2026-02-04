/**
 * Retry hook for API calls with exponential backoff.
 * Wraps async functions with automatic retry logic for transient failures.
 */

import { classifyError, isRetryable, ErrorType } from '../errors';

export interface RetryOptions {
  maxRetries?: number;
  baseDelay?: number;
  maxDelay?: number;
  shouldRetry?: (error: unknown, attempt: number) => boolean;
}

export interface RetryState<T> {
  data: T | null;
  error: unknown | null;
  isLoading: boolean;
  isRetrying: boolean;
  attempt: number;
  maxAttempts: number;
}

export interface RetryHookResult<T> {
  getState: () => RetryState<T>;
  execute: () => Promise<T>;
  abort: () => void;
  reset: () => void;
  subscribe: (callback: () => void) => () => void;
}

const DEFAULT_MAX_RETRIES = 3;
const DEFAULT_BASE_DELAY = 1000; // 1 second
const DEFAULT_MAX_DELAY = 10000; // 10 seconds

/**
 * Creates a retry wrapper for async functions.
 * Only retries on network errors or 5xx server errors.
 * Aborts immediately on 4xx client errors.
 */
export function createRetryHandler<T>(
  fn: (signal?: AbortSignal) => Promise<T>,
  options: RetryOptions = {}
): RetryHookResult<T> {
  const {
    maxRetries = DEFAULT_MAX_RETRIES,
    baseDelay = DEFAULT_BASE_DELAY,
    maxDelay = DEFAULT_MAX_DELAY,
    shouldRetry,
  } = options;

  let state: RetryState<T> = {
    data: null,
    error: null,
    isLoading: false,
    isRetrying: false,
    attempt: 0,
    maxAttempts: maxRetries + 1,
  };

  let abortController: AbortController | null = null;
  let subscribers: Set<() => void> = new Set();

  function notifySubscribers() {
    subscribers.forEach((cb) => cb());
  }

  function updateState(updates: Partial<RetryState<T>>) {
    state = { ...state, ...updates };
    notifySubscribers();
  }

  function calculateDelay(attempt: number): number {
    // Exponential backoff with jitter
    const exponentialDelay = baseDelay * Math.pow(2, attempt);
    const jitter = Math.random() * 0.1 * exponentialDelay;
    return Math.min(exponentialDelay + jitter, maxDelay);
  }

  function defaultShouldRetry(error: unknown, attempt: number): boolean {
    if (attempt >= maxRetries) return false;

    // Use custom shouldRetry if provided
    if (shouldRetry) {
      return shouldRetry(error, attempt);
    }

    // Default: only retry on retryable errors
    return isRetryable(error);
  }

  async function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async function execute(): Promise<T> {
    // Create new abort controller
    abortController = new AbortController();
    const signal = abortController.signal;

    updateState({
      isLoading: true,
      error: null,
      attempt: 0,
    });

    let lastError: unknown = null;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      // Check if aborted
      if (signal.aborted) {
        const abortError = new DOMException('Operation aborted', 'AbortError');
        updateState({
          isLoading: false,
          isRetrying: false,
          error: abortError,
        });
        throw abortError;
      }

      updateState({
        attempt,
        isRetrying: attempt > 0,
      });

      try {
        const result = await fn(signal);
        updateState({
          data: result,
          error: null,
          isLoading: false,
          isRetrying: false,
        });
        return result;
      } catch (error) {
        lastError = error;

        // Check if aborted
        if (signal.aborted) {
          updateState({
            isLoading: false,
            isRetrying: false,
            error,
          });
          throw error;
        }

        // Check if we should retry
        const classified = classifyError(error);

        // Never retry client errors (4xx)
        if (classified.type === ErrorType.VALIDATION) {
          updateState({
            error,
            isLoading: false,
            isRetrying: false,
          });
          throw error;
        }

        // Check custom/default retry logic
        if (!defaultShouldRetry(error, attempt)) {
          updateState({
            error,
            isLoading: false,
            isRetrying: false,
          });
          throw error;
        }

        // Wait before retrying (unless this is the last attempt)
        if (attempt < maxRetries) {
          const delay = calculateDelay(attempt);
          await sleep(delay);
        }
      }
    }

    // All retries exhausted
    updateState({
      error: lastError,
      isLoading: false,
      isRetrying: false,
    });
    throw lastError;
  }

  function abort() {
    if (abortController) {
      abortController.abort();
      abortController = null;
    }
    updateState({
      isLoading: false,
      isRetrying: false,
    });
  }

  function reset() {
    abort();
    state = {
      data: null,
      error: null,
      isLoading: false,
      isRetrying: false,
      attempt: 0,
      maxAttempts: maxRetries + 1,
    };
    notifySubscribers();
  }

  return {
    getState: () => state,
    execute,
    abort,
    reset,
    subscribe: (callback: () => void) => {
      subscribers.add(callback);
      return () => subscribers.delete(callback);
    },
  };
}

/**
 * Convenience function to wrap a fetch call with retry logic.
 */
export async function fetchWithRetry<T>(
  url: string,
  init?: RequestInit,
  options?: RetryOptions
): Promise<T> {
  const handler = createRetryHandler<T>(async (signal) => {
    const response = await fetch(url, {
      ...init,
      signal,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw Object.assign(new Error(error.detail || `HTTP ${response.status}`), {
        status: response.status,
        response,
      });
    }

    return response.json();
  }, options);

  return handler.execute();
}
