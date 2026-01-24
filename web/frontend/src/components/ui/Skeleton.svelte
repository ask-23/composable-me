<script lang="ts">
  /**
   * Skeleton.svelte - Loading placeholder with shimmer animation
   * Supports text, circle, and rectangle variants
   */

  interface Props {
    variant?: 'text' | 'circle' | 'rectangle';
    width?: string;
    height?: string;
  }

  let {
    variant = 'text',
    width,
    height,
  }: Props = $props();

  let defaultWidth = $derived(
    variant === 'circle' ? '40px' :
    variant === 'text' ? '100%' :
    '100%'
  );

  let defaultHeight = $derived(
    variant === 'circle' ? '40px' :
    variant === 'text' ? '1em' :
    '100px'
  );

  let computedWidth = $derived(width || defaultWidth);
  let computedHeight = $derived(height || defaultHeight);
</script>

<div
  class="skeleton skeleton-{variant}"
  style="width: {computedWidth}; height: {computedHeight};"
  aria-hidden="true"
  role="presentation"
></div>

<style>
  .skeleton {
    background: linear-gradient(
      90deg,
      var(--color-bg-secondary) 25%,
      var(--color-bg-tertiary) 50%,
      var(--color-bg-secondary) 75%
    );
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite linear;
  }

  @keyframes shimmer {
    0% {
      background-position: 200% 0;
    }
    100% {
      background-position: -200% 0;
    }
  }

  .skeleton-text {
    border-radius: var(--radius-sm);
  }

  .skeleton-circle {
    border-radius: var(--radius-full);
  }

  .skeleton-rectangle {
    border-radius: var(--radius-base);
  }
</style>
