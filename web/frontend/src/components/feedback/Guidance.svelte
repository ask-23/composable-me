<script lang="ts">
  /**
   * Guidance.svelte - Inline guidance/tip component
   * Shows contextual tips with optional dismissal
   */

  interface Props {
    variant?: 'tip' | 'info' | 'warning';
    dismissible?: boolean;
    storageKey?: string;
  }

  let {
    variant = 'tip',
    dismissible = false,
    storageKey,
  }: Props = $props();

  let dismissed = $state(false);

  // Check localStorage on mount for persisted dismissal
  $effect(() => {
    if (storageKey && typeof window !== 'undefined') {
      dismissed = localStorage.getItem(storageKey) === 'dismissed';
    }
  });

  function handleDismiss() {
    dismissed = true;
    if (storageKey && typeof window !== 'undefined') {
      localStorage.setItem(storageKey, 'dismissed');
    }
  }

  // Icon based on variant
  const icons = {
    tip: '💡',
    info: 'ℹ️',
    warning: '⚠️',
  };
</script>

{#if !dismissed}
  <div class="guidance {variant}" role="note">
    <span class="guidance-icon">{icons[variant]}</span>
    <div class="guidance-content">
      <slot />
    </div>
    {#if dismissible}
      <button
        class="guidance-dismiss"
        onclick={handleDismiss}
        aria-label="Dismiss"
        type="button"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
          <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
        </svg>
      </button>
    {/if}
  </div>
{/if}

<style>
  .guidance {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.875rem 1rem;
    border-radius: var(--radius);
    font-size: 0.875rem;
    line-height: 1.5;
  }

  /* Variant styles */
  .guidance.tip {
    background: rgba(234, 179, 8, 0.08);
    border: 1px solid rgba(234, 179, 8, 0.2);
    color: var(--color-text);
  }

  .guidance.info {
    background: rgba(59, 130, 246, 0.08);
    border: 1px solid rgba(59, 130, 246, 0.2);
    color: var(--color-text);
  }

  .guidance.warning {
    background: rgba(239, 68, 68, 0.08);
    border: 1px solid rgba(239, 68, 68, 0.2);
    color: var(--color-text);
  }

  .guidance-icon {
    flex-shrink: 0;
    font-size: 1rem;
    line-height: 1.5;
  }

  .guidance-content {
    flex: 1;
    min-width: 0;
  }

  .guidance-content :global(strong) {
    font-weight: 600;
  }

  .guidance-dismiss {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    padding: 0;
    background: transparent;
    border: none;
    border-radius: 4px;
    color: var(--color-text-muted);
    cursor: pointer;
    transition: color 0.2s, background 0.2s;
  }

  .guidance-dismiss:hover {
    color: var(--color-text);
    background: rgba(255, 255, 255, 0.1);
  }
</style>
