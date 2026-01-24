<script lang="ts">
  /**
   * Badge.svelte - Status indicator / chip component
   * Supports multiple variants and sizes
   */

  import type { Snippet } from 'svelte';

  interface Props {
    variant?: 'default' | 'success' | 'warning' | 'error' | 'info';
    size?: 'sm' | 'md';
    children: Snippet;
  }

  let {
    variant = 'default',
    size = 'md',
    children,
  }: Props = $props();
</script>

<span class="badge badge-{variant} badge-{size}" role="status">
  {@render children()}
</span>

<style>
  .badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-family: var(--font-family-sans);
    font-weight: var(--font-weight-medium);
    line-height: 1;
    border-radius: var(--radius-full);
    white-space: nowrap;
  }

  /* Size variants */
  .badge-sm {
    padding: var(--spacing-1) var(--spacing-2);
    font-size: var(--font-size-xs);
  }

  .badge-md {
    padding: var(--spacing-1) var(--spacing-3);
    font-size: var(--font-size-sm);
  }

  /* Color variants */
  .badge-default {
    background-color: var(--color-secondary-100);
    color: var(--color-secondary-700);
  }

  .badge-success {
    background-color: var(--color-success-100);
    color: var(--color-success-700);
  }

  .badge-warning {
    background-color: var(--color-warning-100);
    color: var(--color-warning-700);
  }

  .badge-error {
    background-color: var(--color-error-100);
    color: var(--color-error-700);
  }

  .badge-info {
    background-color: var(--color-info-100);
    color: var(--color-info-700);
  }
</style>
