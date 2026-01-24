<script lang="ts">
  /**
   * Button.svelte - Accessible button component
   * Supports multiple variants, sizes, and states
   */

  import type { Snippet } from 'svelte';

  interface Props {
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
    size?: 'sm' | 'md' | 'lg';
    disabled?: boolean;
    loading?: boolean;
    type?: 'button' | 'submit' | 'reset';
    onclick?: (event: MouseEvent) => void;
    children: Snippet;
  }

  let {
    variant = 'primary',
    size = 'md',
    disabled = false,
    loading = false,
    type = 'button',
    onclick,
    children,
  }: Props = $props();

  let isDisabled = $derived(disabled || loading);
</script>

<button
  {type}
  class="btn btn-{variant} btn-{size}"
  class:loading
  disabled={isDisabled}
  aria-disabled={isDisabled}
  aria-busy={loading}
  onclick={onclick}
>
  {#if loading}
    <span class="spinner" aria-hidden="true"></span>
  {/if}
  <span class="btn-content" class:loading-hidden={loading}>
    {@render children()}
  </span>
</button>

<style>
  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-2);
    font-family: var(--font-family-sans);
    font-weight: var(--font-weight-medium);
    line-height: 1;
    border: 1px solid transparent;
    border-radius: var(--radius-base);
    cursor: pointer;
    transition:
      background-color var(--transition-fast),
      border-color var(--transition-fast),
      color var(--transition-fast),
      box-shadow var(--transition-fast);
    position: relative;
  }

  .btn:focus-visible {
    outline: var(--focus-ring-width) solid var(--focus-ring-color);
    outline-offset: var(--focus-ring-offset);
  }

  .btn:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }

  /* Size variants */
  .btn-sm {
    padding: var(--spacing-2) var(--spacing-3);
    font-size: var(--font-size-sm);
    min-height: 32px;
  }

  .btn-md {
    padding: var(--spacing-2) var(--spacing-4);
    font-size: var(--font-size-base);
    min-height: 40px;
  }

  .btn-lg {
    padding: var(--spacing-3) var(--spacing-6);
    font-size: var(--font-size-lg);
    min-height: 48px;
  }

  /* Primary variant */
  .btn-primary {
    background-color: var(--color-primary);
    color: var(--color-text-inverted);
    border-color: var(--color-primary);
  }

  .btn-primary:hover:not(:disabled) {
    background-color: var(--color-primary-600);
    border-color: var(--color-primary-600);
  }

  .btn-primary:active:not(:disabled) {
    background-color: var(--color-primary-700);
    border-color: var(--color-primary-700);
  }

  /* Secondary variant */
  .btn-secondary {
    background-color: var(--color-bg);
    color: var(--color-text);
    border-color: var(--color-border);
  }

  .btn-secondary:hover:not(:disabled) {
    background-color: var(--color-bg-secondary);
    border-color: var(--color-secondary-300);
  }

  .btn-secondary:active:not(:disabled) {
    background-color: var(--color-bg-tertiary);
  }

  /* Ghost variant */
  .btn-ghost {
    background-color: transparent;
    color: var(--color-text);
    border-color: transparent;
  }

  .btn-ghost:hover:not(:disabled) {
    background-color: var(--color-bg-secondary);
  }

  .btn-ghost:active:not(:disabled) {
    background-color: var(--color-bg-tertiary);
  }

  /* Danger variant */
  .btn-danger {
    background-color: var(--color-error);
    color: var(--color-text-inverted);
    border-color: var(--color-error);
  }

  .btn-danger:hover:not(:disabled) {
    background-color: var(--color-error-600);
    border-color: var(--color-error-600);
  }

  .btn-danger:active:not(:disabled) {
    background-color: var(--color-error-700);
    border-color: var(--color-error-700);
  }

  /* Loading state */
  .spinner {
    position: absolute;
    width: 16px;
    height: 16px;
    border: 2px solid currentColor;
    border-right-color: transparent;
    border-radius: var(--radius-full);
    animation: spin 0.6s linear infinite;
  }

  .btn-lg .spinner {
    width: 20px;
    height: 20px;
  }

  .btn-sm .spinner {
    width: 14px;
    height: 14px;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .btn-content {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-2);
  }

  .loading-hidden {
    visibility: hidden;
  }
</style>
