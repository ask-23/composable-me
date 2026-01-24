<script lang="ts">
  /**
   * Card.svelte - Container component with slots
   * Supports multiple visual variants
   */

  import type { Snippet } from 'svelte';

  interface Props {
    variant?: 'default' | 'elevated' | 'outlined';
    header?: Snippet;
    children: Snippet;
    footer?: Snippet;
  }

  let {
    variant = 'default',
    header,
    children,
    footer,
  }: Props = $props();
</script>

<div class="card card-{variant}">
  {#if header}
    <div class="card-header">
      {@render header()}
    </div>
  {/if}

  <div class="card-body">
    {@render children()}
  </div>

  {#if footer}
    <div class="card-footer">
      {@render footer()}
    </div>
  {/if}
</div>

<style>
  .card {
    display: flex;
    flex-direction: column;
    border-radius: var(--radius-lg);
    overflow: hidden;
  }

  /* Default variant */
  .card-default {
    background-color: var(--color-bg);
    border: 1px solid var(--color-border);
  }

  /* Elevated variant */
  .card-elevated {
    background-color: var(--color-bg);
    box-shadow: var(--shadow-lg);
  }

  /* Outlined variant */
  .card-outlined {
    background-color: transparent;
    border: 2px solid var(--color-border);
  }

  .card-header {
    padding: var(--spacing-4) var(--spacing-6);
    border-bottom: 1px solid var(--color-border);
  }

  .card-body {
    padding: var(--spacing-6);
    flex: 1;
  }

  .card-footer {
    padding: var(--spacing-4) var(--spacing-6);
    border-top: 1px solid var(--color-border);
    background-color: var(--color-bg-secondary);
  }
</style>
