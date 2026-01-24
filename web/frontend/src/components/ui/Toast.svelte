<script lang="ts">
  /**
   * Toast.svelte - Notification toast component
   * Auto-dismisses with configurable duration
   */

  interface Props {
    type?: 'success' | 'warning' | 'error' | 'info';
    message: string;
    duration?: number;
    dismissible?: boolean;
    onclose?: () => void;
  }

  let {
    type = 'info',
    message,
    duration = 5000,
    dismissible = true,
    onclose,
  }: Props = $props();

  let visible = $state(true);
  let progress = $state(100);
  let isPaused = $state(false);

  // Auto-dismiss timer
  $effect(() => {
    if (duration <= 0 || !visible) return;

    let startTime = Date.now();
    let remainingTime = duration;

    const tick = () => {
      if (isPaused) {
        startTime = Date.now();
        return;
      }

      const elapsed = Date.now() - startTime;
      const newRemaining = remainingTime - elapsed;

      if (newRemaining <= 0) {
        dismiss();
        return;
      }

      progress = (newRemaining / duration) * 100;
      requestAnimationFrame(tick);
    };

    const frameId = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(frameId);
    };
  });

  function dismiss() {
    visible = false;
    onclose?.();
  }

  function handleMouseEnter() {
    isPaused = true;
  }

  function handleMouseLeave() {
    isPaused = false;
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      dismiss();
    }
  }
</script>

{#if visible}
  <div
    class="toast toast-{type}"
    role="alert"
    aria-live="polite"
    onmouseenter={handleMouseEnter}
    onmouseleave={handleMouseLeave}
    onkeydown={handleKeyDown}
  >
    <div class="toast-icon">
      {#if type === 'success'}
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
          <polyline points="22 4 12 14.01 9 11.01" />
        </svg>
      {:else if type === 'warning'}
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
      {:else if type === 'error'}
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10" />
          <line x1="15" y1="9" x2="9" y2="15" />
          <line x1="9" y1="9" x2="15" y2="15" />
        </svg>
      {:else}
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="16" x2="12" y2="12" />
          <line x1="12" y1="8" x2="12.01" y2="8" />
        </svg>
      {/if}
    </div>

    <p class="toast-message">{message}</p>

    {#if dismissible}
      <button
        type="button"
        class="toast-close"
        onclick={dismiss}
        aria-label="Dismiss notification"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    {/if}

    {#if duration > 0}
      <div class="toast-progress" style="width: {progress}%"></div>
    {/if}
  </div>
{/if}

<style>
  .toast {
    position: fixed;
    top: var(--spacing-4);
    right: var(--spacing-4);
    display: flex;
    align-items: flex-start;
    gap: var(--spacing-3);
    max-width: 400px;
    padding: var(--spacing-4);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-lg);
    background-color: var(--color-bg);
    border: 1px solid var(--color-border);
    z-index: var(--z-tooltip);
    overflow: hidden;
    animation: slideIn var(--transition-base);
  }

  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  .toast-icon {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .toast-success .toast-icon {
    color: var(--color-success);
  }

  .toast-warning .toast-icon {
    color: var(--color-warning);
  }

  .toast-error .toast-icon {
    color: var(--color-error);
  }

  .toast-info .toast-icon {
    color: var(--color-info);
  }

  .toast-message {
    flex: 1;
    margin: 0;
    font-size: var(--font-size-sm);
    color: var(--color-text);
    line-height: var(--line-height-normal);
  }

  .toast-close {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: var(--spacing-1);
    background: transparent;
    border: none;
    border-radius: var(--radius-sm);
    color: var(--color-text-muted);
    cursor: pointer;
    transition: color var(--transition-fast), background-color var(--transition-fast);
  }

  .toast-close:hover {
    color: var(--color-text);
    background-color: var(--color-bg-secondary);
  }

  .toast-close:focus-visible {
    outline: var(--focus-ring-width) solid var(--focus-ring-color);
    outline-offset: var(--focus-ring-offset);
  }

  .toast-progress {
    position: absolute;
    bottom: 0;
    left: 0;
    height: 3px;
    transition: width 100ms linear;
  }

  .toast-success .toast-progress {
    background-color: var(--color-success);
  }

  .toast-warning .toast-progress {
    background-color: var(--color-warning);
  }

  .toast-error .toast-progress {
    background-color: var(--color-error);
  }

  .toast-info .toast-progress {
    background-color: var(--color-info);
  }
</style>
