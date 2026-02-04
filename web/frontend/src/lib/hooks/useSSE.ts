/**
 * Robust SSE (Server-Sent Events) hook with automatic reconnection.
 * Handles connection drops, exponential backoff, and state tracking.
 */

import type { JobState, SSEProgressEvent, SSECompleteEvent } from '../types';

export type SSEConnectionState =
  | 'connecting'
  | 'connected'
  | 'reconnecting'
  | 'disconnected'
  | 'failed';

export interface SSEState {
  jobState: JobState;
  progress: number;
  logs: string[];
  error: string | null;
  agentModels: Record<string, string>;
}

export interface SSEHookResult {
  state: SSEState;
  connectionState: SSEConnectionState;
  isConnected: boolean;
  reconnectAttempt: number;
  lastEventTime: number | null;
  reconnect: () => void;
  disconnect: () => void;
}

export interface SSEHookOptions {
  jobId: string;
  initialState?: JobState;
  onComplete?: (event: SSECompleteEvent) => void;
  onError?: (error: string) => void;
  maxReconnectAttempts?: number;
  baseReconnectDelay?: number;
  maxReconnectDelay?: number;
}

const DEFAULT_MAX_RECONNECT_ATTEMPTS = 5;
const DEFAULT_BASE_RECONNECT_DELAY = 1000; // 1 second
const DEFAULT_MAX_RECONNECT_DELAY = 30000; // 30 seconds

/**
 * Creates and manages an SSE connection with automatic reconnection.
 * This is a factory function that returns reactive state for Svelte 5.
 */
export function createSSEConnection(options: SSEHookOptions): {
  getState: () => SSEState;
  getConnectionState: () => SSEConnectionState;
  getReconnectAttempt: () => number;
  getLastEventTime: () => number | null;
  isConnected: () => boolean;
  reconnect: () => void;
  disconnect: () => void;
  subscribe: (callback: () => void) => () => void;
} {
  const {
    jobId,
    initialState = 'initialized',
    onComplete,
    onError,
    maxReconnectAttempts = DEFAULT_MAX_RECONNECT_ATTEMPTS,
    baseReconnectDelay = DEFAULT_BASE_RECONNECT_DELAY,
    maxReconnectDelay = DEFAULT_MAX_RECONNECT_DELAY,
  } = options;

  // Internal state
  let state: SSEState = {
    jobState: initialState,
    progress: 0,
    logs: [],
    error: null,
    agentModels: {},
  };

  let connectionState: SSEConnectionState = 'disconnected';
  let reconnectAttempt = 0;
  let lastEventTime: number | null = null;
  let eventSource: EventSource | null = null;
  let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  let isJobComplete = false;
  let subscribers: Set<() => void> = new Set();

  function notifySubscribers() {
    subscribers.forEach((cb) => cb());
  }

  function updateState(updates: Partial<SSEState>) {
    state = { ...state, ...updates };
    notifySubscribers();
  }

  function setConnectionState(newState: SSEConnectionState) {
    connectionState = newState;
    notifySubscribers();
  }

  function calculateReconnectDelay(): number {
    // Exponential backoff: 1s, 2s, 4s, 8s, 16s, capped at maxReconnectDelay
    const delay = baseReconnectDelay * Math.pow(2, reconnectAttempt);
    return Math.min(delay, maxReconnectDelay);
  }

  function scheduleReconnect() {
    if (reconnectAttempt >= maxReconnectAttempts) {
      setConnectionState('failed');
      updateState({
        error: `Connection failed after ${maxReconnectAttempts} attempts. Click "Reconnect" to try again.`,
      });
      onError?.(`Connection failed after ${maxReconnectAttempts} attempts`);
      return;
    }

    const delay = calculateReconnectDelay();
    setConnectionState('reconnecting');
    updateState({
      error: `Connection lost. Reconnecting in ${Math.round(delay / 1000)}s... (attempt ${reconnectAttempt + 1}/${maxReconnectAttempts})`,
    });

    reconnectTimeout = setTimeout(() => {
      reconnectAttempt++;
      connect();
    }, delay);
  }

  function connect() {
    // Don't connect if job is already complete
    if (isJobComplete) return;

    // Clean up existing connection
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }

    setConnectionState('connecting');
    eventSource = new EventSource(`/api/jobs/${jobId}/stream`);

    eventSource.addEventListener('connected', (e) => {
      setConnectionState('connected');
      reconnectAttempt = 0;
      lastEventTime = Date.now();

      try {
        const data = JSON.parse(e.data);
        updateState({
          jobState: data.state,
          progress: data.progress,
          error: null,
        });
      } catch {
        // Ignore parse errors for connected event
      }
      notifySubscribers();
    });

    eventSource.addEventListener('progress', (e) => {
      lastEventTime = Date.now();
      try {
        const data: SSEProgressEvent = JSON.parse(e.data);
        updateState({
          jobState: data.state,
          progress: data.progress,
          agentModels: data.agent_models || state.agentModels,
        });
      } catch {
        // Ignore parse errors
      }
    });

    eventSource.addEventListener('log', (e) => {
      lastEventTime = Date.now();
      try {
        const data = JSON.parse(e.data);
        updateState({
          logs: [...state.logs, data.message],
        });
      } catch {
        // Ignore parse errors
      }
    });

    eventSource.addEventListener('stage_complete', (e) => {
      lastEventTime = Date.now();
      try {
        const data = JSON.parse(e.data);
        updateState({
          logs: [...state.logs, `Stage completed: ${data.stage}`],
        });
      } catch {
        // Ignore parse errors
      }
    });

    eventSource.addEventListener('complete', (e) => {
      lastEventTime = Date.now();
      isJobComplete = true;

      try {
        const data: SSECompleteEvent = JSON.parse(e.data);
        updateState({
          jobState: data.state as JobState,
          progress: 100,
          agentModels: data.agent_models || state.agentModels,
          error: data.state === 'failed' ? data.error_message || null : null,
        });

        onComplete?.(data);
      } catch {
        // Ignore parse errors
      }

      disconnect();
    });

    eventSource.addEventListener('error', (e: Event) => {
      lastEventTime = Date.now();
      // Type assertion for MessageEvent with data property
      const messageEvent = e as MessageEvent;
      if (messageEvent.data) {
        try {
          const errorData = JSON.parse(messageEvent.data);
          const errorMessage =
            errorData.error ||
            errorData.message ||
            errorData.detail ||
            'An unknown error occurred';
          updateState({ error: errorMessage });
          onError?.(errorMessage);
        } catch {
          updateState({ error: messageEvent.data });
          onError?.(messageEvent.data);
        }
      }
    });

    eventSource.onerror = () => {
      if (isJobComplete) return;

      setConnectionState('disconnected');

      // Don't update error state here - let scheduleReconnect handle it
      scheduleReconnect();
    };
  }

  function disconnect() {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }

    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }

    setConnectionState('disconnected');
  }

  function manualReconnect() {
    // Reset reconnect attempts for manual reconnect
    reconnectAttempt = 0;
    isJobComplete = false;
    updateState({ error: null });
    connect();
  }

  // Start connection immediately
  connect();

  return {
    getState: () => state,
    getConnectionState: () => connectionState,
    getReconnectAttempt: () => reconnectAttempt,
    getLastEventTime: () => lastEventTime,
    isConnected: () => connectionState === 'connected',
    reconnect: manualReconnect,
    disconnect,
    subscribe: (callback: () => void) => {
      subscribers.add(callback);
      return () => subscribers.delete(callback);
    },
  };
}
