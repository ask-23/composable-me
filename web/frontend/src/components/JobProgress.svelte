<script lang="ts">
  /**
   * JobProgress.svelte - Real-time progress tracker with SSE
   * Shows current agent, their role, and fun facts
   */

  import {
    STAGES,
    STAGE_INFO,
    type JobState,
    type SSEProgressEvent,
    type SSECompleteEvent,
  } from "../lib/types";

  interface Props {
    jobId: string;
    initialState?: JobState;
    onComplete?: (event: SSECompleteEvent) => void;
  }

  let { jobId, initialState = "initialized", onComplete }: Props = $props();

  let state = $state<JobState>(initialState);
  let progress = $state(0);
  let logs = $state<string[]>([]);
  let error = $state<string | null>(null);
  let isConnected = $state(false);
  let elapsedSeconds = $state(0);
  let agent_models = $state<Record<string, string>>({});

  // Timer for elapsed time
  let timerInterval: ReturnType<typeof setInterval> | null = null;

  // Derived values
  let currentStageIndex = $derived(STAGES.indexOf(state));
  let stageInfo = $derived(STAGE_INFO[state]);
  let isComplete = $derived(state === "completed" || state === "failed");
  let elapsedTime = $derived(formatTime(elapsedSeconds));

  function formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  }

  // Start timer on mount
  $effect(() => {
    if (!isComplete) {
      timerInterval = setInterval(() => {
        elapsedSeconds += 1;
      }, 1000);
    }

    return () => {
      if (timerInterval) {
        clearInterval(timerInterval);
      }
    };
  });

  // Stop timer on complete
  $effect(() => {
    if (isComplete && timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
  });

  // SSE connection effect
  $effect(() => {
    if (isComplete) return;

    const eventSource = new EventSource(`/api/jobs/${jobId}/stream`);

    eventSource.addEventListener("connected", (e) => {
      isConnected = true;
      const data = JSON.parse(e.data);
      state = data.state;
      progress = data.progress;
    });

    eventSource.addEventListener("progress", (e) => {
      const data: SSEProgressEvent = JSON.parse(e.data);
      state = data.state;
      progress = data.progress;
      // Update agent models if provided in progress event
      if (data.agent_models) {
        agent_models = data.agent_models;
      }
    });

    eventSource.addEventListener("log", (e) => {
      const data = JSON.parse(e.data);
      logs = [...logs, data.message];
    });

    eventSource.addEventListener("stage_complete", (e) => {
      const data = JSON.parse(e.data);
      logs = [...logs, `Stage completed: ${data.stage}`];
    });

    eventSource.addEventListener("complete", (e) => {
      const data: SSECompleteEvent = JSON.parse(e.data);
      state = data.state as JobState;
      progress = 100;
      if (data.agent_models) agent_models = data.agent_models;

      // Capture error message if job failed
      if (data.state === "failed" && data.error_message) {
        error = data.error_message;
      }

      eventSource.close();
      onComplete?.(data);
    });

    eventSource.addEventListener("error", (e) => {
      // @ts-ignore
      if (e.data) {
        try {
          // @ts-ignore
          const errorData = JSON.parse(e.data);
          error =
            errorData.error ||
            errorData.message ||
            errorData.detail ||
            "An unknown error occurred";
        } catch {
          // @ts-ignore
          error = e.data;
        }
      } else {
        error = "An error occurred during processing";
      }
      eventSource.close();
    });

    eventSource.onerror = () => {
      if (!isComplete) {
        error = "Connection lost. Refresh to reconnect.";
      }
      isConnected = false;
    };

    return () => {
      eventSource.close();
    };
  });
</script>

<div class="progress-container">
  <!-- Header with timer -->
  <div class="progress-header">
    <h2>Processing Your Application</h2>
    <div class="timer">
      <span class="timer-icon">&#9201;</span>
      <span>{elapsedTime}</span>
    </div>
  </div>

  <!-- Progress bar -->
  <div class="progress-bar-container">
    <div class="progress-bar" style="width: {progress}%">
      <div class="progress-glow"></div>
    </div>
    <span class="progress-percent">{progress}%</span>
  </div>

  <!-- Stage indicators -->
  <div class="stages">
    {#each STAGES as stageName, i}
      <div
        class="stage"
        class:active={i === currentStageIndex && !isComplete}
        class:complete={i < currentStageIndex ||
          (i === currentStageIndex && isComplete && state === "completed")}
        class:pending={i > currentStageIndex &&
          !(isComplete && state === "completed")}
        class:failed={isComplete &&
          state === "failed" &&
          i >= currentStageIndex}
      >
        <div class="stage-dot">
          {#if i < currentStageIndex || (i === currentStageIndex && isComplete && state === "completed")}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="3"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
          {:else if i === currentStageIndex && !isComplete}
            <span class="pulse"></span>
          {:else}
            <span class="dot"></span>
          {/if}
        </div>
        <span class="stage-label">{STAGE_INFO[stageName].label}</span>
      </div>
    {/each}
  </div>

  <!-- Current Agent Info Card -->
  <div
    class="agent-card"
    class:success={state === "completed"}
    class:error={state === "failed"}
  >
    <div class="agent-header">
      <div class="agent-icon">
        {#if state === "completed"}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="32"
            height="32"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
        {:else if state === "failed"}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="32"
            height="32"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="15" y1="9" x2="9" y2="15" />
            <line x1="9" y1="9" x2="15" y2="15" />
          </svg>
        {:else}
          <div class="agent-spinner"></div>
        {/if}
      </div>
      <div class="agent-title">
        <div class="agent-title-row">
          <h3>{stageInfo.agentName}</h3>
          {#if agent_models[state]}
            <span class="model-badge">{agent_models[state]}</span>
          {/if}
        </div>
        <p class="agent-status">{stageInfo.description}</p>
      </div>
    </div>

    <div class="agent-body">
      <div class="agent-role">
        <strong>What I do:</strong>
        <p>{stageInfo.role}</p>
      </div>

      <div class="agent-funfact">
        <span class="funfact-icon">&#128161;</span>
        <p>{stageInfo.funFact}</p>
      </div>
    </div>
  </div>

  <!-- Connection status -->
  {#if !isConnected && !isComplete}
    <div class="connecting">
      <span class="connecting-spinner"></span>
      Connecting to server...
    </div>
  {/if}

  <!-- Error message -->
  {#if error}
    <div class="error-banner">
      <p>{error}</p>
    </div>
  {/if}

  <!-- Execution log (collapsible) -->
  {#if logs.length > 0}
    <details class="log-container">
      <summary>Execution Log ({logs.length} entries)</summary>
      <ul class="log-list">
        {#each logs.slice(-20) as entry}
          <li>{entry}</li>
        {/each}
      </ul>
    </details>
  {/if}
</div>

<style>
  .progress-container {
    padding: 1.5rem;
  }

  .progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
  }

  .progress-header h2 {
    margin: 0;
    font-size: 1.25rem;
  }

  .timer {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--color-text-muted);
    font-family: monospace;
    font-size: 1rem;
  }

  .timer-icon {
    font-size: 1.2rem;
  }

  .progress-bar-container {
    position: relative;
    height: 12px;
    background: var(--color-bg);
    border-radius: 6px;
    overflow: hidden;
    margin-bottom: 2rem;
  }

  .progress-bar {
    height: 100%;
    background: linear-gradient(90deg, var(--color-primary), #60a5fa);
    border-radius: 6px;
    transition: width 0.5s ease-out;
    position: relative;
  }

  .progress-glow {
    position: absolute;
    right: 0;
    top: 0;
    bottom: 0;
    width: 30px;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3));
    animation: glow 1.5s ease-in-out infinite;
  }

  @keyframes glow {
    0%,
    100% {
      opacity: 0.3;
    }
    50% {
      opacity: 0.8;
    }
  }

  .progress-percent {
    position: absolute;
    right: 0;
    top: -1.5rem;
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--color-primary);
  }

  .stages {
    display: flex;
    justify-content: space-between;
    margin-bottom: 2rem;
    overflow-x: auto;
    padding-bottom: 0.5rem;
  }

  .stage {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    min-width: 70px;
  }

  .stage-dot {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--color-bg);
    border: 2px solid var(--color-border);
    color: var(--color-text-muted);
    transition: all 0.3s;
  }

  .stage.complete .stage-dot {
    background: var(--color-success);
    border-color: var(--color-success);
    color: white;
  }

  .stage.active .stage-dot {
    border-color: var(--color-primary);
    box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.2);
  }

  .pulse {
    width: 10px;
    height: 10px;
    background: var(--color-primary);
    border-radius: 50%;
    animation: pulse 1.5s ease-in-out infinite;
  }

  @keyframes pulse {
    0%,
    100% {
      transform: scale(1);
      opacity: 1;
    }
    50% {
      transform: scale(1.4);
      opacity: 0.7;
    }
  }

  .dot {
    width: 8px;
    height: 8px;
    background: var(--color-border);
    border-radius: 50%;
  }

  .stage-label {
    font-size: 0.7rem;
    color: var(--color-text-muted);
    text-align: center;
    white-space: nowrap;
  }

  .stage.active .stage-label,
  .stage.complete .stage-label {
    color: var(--color-text);
    font-weight: 500;
  }

  /* Agent Card */
  .agent-card {
    background: var(--color-bg);
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
  }

  .agent-card.success {
    border-color: var(--color-success);
    background: rgba(34, 197, 94, 0.05);
  }

  .agent-card.error {
    border-color: var(--color-error);
    background: rgba(239, 68, 68, 0.05);
  }

  .agent-header {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .agent-icon {
    flex-shrink: 0;
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--color-primary);
  }

  .agent-card.success .agent-icon {
    color: var(--color-success);
  }

  .agent-card.error .agent-icon {
    color: var(--color-error);
  }

  .agent-spinner {
    width: 32px;
    height: 32px;
    border: 3px solid var(--color-border);
    border-top-color: var(--color-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .agent-title-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.25rem;
  }

  .agent-title h3 {
    margin: 0;
    font-size: 1.1rem;
    color: var(--color-primary);
  }

  .model-badge {
    font-size: 0.7rem;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    background: var(--color-bg-secondary);
    color: var(--color-text-muted);
    border: 1px solid var(--color-border);
    font-family: monospace;
  }

  .agent-card.success .agent-title h3 {
    color: var(--color-success);
  }

  .agent-card.error .agent-title h3 {
    color: var(--color-error);
  }

  .agent-status {
    margin: 0;
    color: var(--color-text-muted);
    font-size: 0.9rem;
  }

  .agent-body {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .agent-role {
    color: var(--color-text);
    font-size: 0.9rem;
    line-height: 1.5;
  }

  .agent-role strong {
    color: var(--color-text-muted);
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .agent-role p {
    margin: 0.25rem 0 0 0;
  }

  .agent-funfact {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    background: rgba(59, 130, 246, 0.1);
    border-radius: calc(var(--radius) / 2);
    padding: 0.75rem 1rem;
    font-size: 0.85rem;
    color: var(--color-text-muted);
  }

  .funfact-icon {
    font-size: 1.2rem;
    flex-shrink: 0;
  }

  .agent-funfact p {
    margin: 0;
    line-height: 1.4;
  }

  /* Connection status */
  .connecting {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    padding: 1rem;
    color: var(--color-text-muted);
    font-size: 0.9rem;
  }

  .connecting-spinner {
    width: 16px;
    height: 16px;
    border: 2px solid var(--color-border);
    border-top-color: var(--color-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  .error-banner {
    margin-top: 1rem;
    padding: 1rem;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid var(--color-error);
    border-radius: var(--radius);
    color: var(--color-error);
  }

  .log-container {
    margin-top: 1.5rem;
    background: var(--color-bg);
    border-radius: var(--radius);
    overflow: hidden;
  }

  .log-container summary {
    padding: 0.75rem 1rem;
    cursor: pointer;
    font-weight: 500;
    color: var(--color-text-muted);
  }

  .log-container summary:hover {
    color: var(--color-text);
  }

  .log-list {
    list-style: none;
    padding: 0 1rem 1rem;
    margin: 0;
    max-height: 200px;
    overflow-y: auto;
    font-family: monospace;
    font-size: 0.75rem;
  }

  .log-list li {
    padding: 0.25rem 0;
    color: var(--color-text-muted);
    border-bottom: 1px solid var(--color-border);
  }

  .log-list li:last-child {
    border-bottom: none;
  }
</style>
