<script lang="ts">
  /**
   * EmptyState.svelte - Reusable empty state component
   * Shows centered content with icon, title, description, and optional CTA
   */

  interface Action {
    label: string;
    href?: string;
    onclick?: () => void;
  }

  interface Props {
    icon?: string;
    title: string;
    description: string;
    action?: Action;
    variant?: 'default' | 'info' | 'success' | 'warning';
  }

  let {
    icon = '',
    title,
    description,
    action,
    variant = 'default',
  }: Props = $props();
</script>

<div class="empty-state {variant}">
  {#if icon}
    <div class="empty-icon">{icon}</div>
  {/if}
  <h3 class="empty-title">{title}</h3>
  <p class="empty-description">{description}</p>
  {#if action}
    {#if action.href}
      <a href={action.href} class="empty-action">{action.label}</a>
    {:else if action.onclick}
      <button class="empty-action" onclick={action.onclick}>{action.label}</button>
    {/if}
  {/if}
</div>

<style>
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 2.5rem 1.5rem;
    border-radius: var(--radius);
    background: var(--color-bg);
    border: 1px dashed var(--color-border);
  }

  /* Variant styles */
  .empty-state.default {
    background: var(--color-bg);
    border-color: var(--color-border);
  }

  .empty-state.info {
    background: rgba(59, 130, 246, 0.05);
    border-color: rgba(59, 130, 246, 0.3);
  }

  .empty-state.info .empty-icon {
    color: var(--color-primary);
  }

  .empty-state.success {
    background: rgba(34, 197, 94, 0.05);
    border-color: rgba(34, 197, 94, 0.3);
  }

  .empty-state.success .empty-icon {
    color: var(--color-success);
  }

  .empty-state.warning {
    background: rgba(234, 179, 8, 0.05);
    border-color: rgba(234, 179, 8, 0.3);
  }

  .empty-state.warning .empty-icon {
    color: var(--color-warning);
  }

  .empty-icon {
    font-size: 2.5rem;
    margin-bottom: 1rem;
    opacity: 0.8;
    color: var(--color-text-muted);
  }

  .empty-title {
    font-size: 1rem;
    font-weight: 600;
    color: var(--color-text);
    margin: 0 0 0.5rem 0;
  }

  .empty-description {
    font-size: 0.875rem;
    color: var(--color-text-muted);
    margin: 0;
    max-width: 320px;
    line-height: 1.5;
  }

  .empty-action {
    display: inline-block;
    margin-top: 1.25rem;
    padding: 0.625rem 1.25rem;
    font-size: 0.875rem;
    font-weight: 500;
    color: white;
    background: var(--color-primary);
    border: none;
    border-radius: var(--radius);
    text-decoration: none;
    cursor: pointer;
    transition: background 0.2s, transform 0.2s;
  }

  .empty-action:hover {
    background: var(--color-primary-hover);
    transform: translateY(-1px);
    text-decoration: none;
  }
</style>
