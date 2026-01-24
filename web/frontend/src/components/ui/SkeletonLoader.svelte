<script lang="ts">
  /**
   * SkeletonLoader.svelte - Reusable skeleton loading placeholders
   * Uses Svelte 5 runes for reactivity
   *
   * Variants:
   * - text: Single line text placeholder
   * - paragraph: Multiple lines (configurable count)
   * - card: Card-shaped placeholder
   * - progress: Progress bar placeholder
   * - avatar: Circular placeholder
   */

  type Variant = 'text' | 'paragraph' | 'card' | 'progress' | 'avatar';

  interface Props {
    variant?: Variant;
    width?: string;
    height?: string;
    lines?: number;
    animated?: boolean;
    class?: string;
  }

  let {
    variant = 'text',
    width,
    height,
    lines = 3,
    animated = true,
    class: className = '',
  }: Props = $props();

  // Computed style for dimensions
  let style = $derived(() => {
    const styles: string[] = [];
    if (width) styles.push(`width: ${width}`);
    if (height) styles.push(`height: ${height}`);
    return styles.join('; ');
  });

  // Generate array for paragraph lines with varying widths
  let paragraphLines = $derived(
    Array.from({ length: lines }, (_, i) => {
      // Last line is typically shorter
      if (i === lines - 1) return '60%';
      // Random-ish widths for natural appearance
      return `${85 + (i % 3) * 5}%`;
    })
  );
</script>

{#if variant === 'text'}
  <div
    class="skeleton skeleton-text {className}"
    class:animated
    style={style()}
  ></div>

{:else if variant === 'paragraph'}
  <div class="skeleton-paragraph {className}">
    {#each paragraphLines as lineWidth}
      <div
        class="skeleton skeleton-text"
        class:animated
        style="width: {lineWidth}"
      ></div>
    {/each}
  </div>

{:else if variant === 'card'}
  <div
    class="skeleton skeleton-card {className}"
    class:animated
    style={style()}
  ></div>

{:else if variant === 'progress'}
  <div class="skeleton-progress-container {className}">
    <div
      class="skeleton skeleton-progress"
      class:animated
      style={style()}
    ></div>
  </div>

{:else if variant === 'avatar'}
  <div
    class="skeleton skeleton-avatar {className}"
    class:animated
    style={style()}
  ></div>
{/if}

<style>
  .skeleton {
    background: var(--color-bg-tertiary, #f1f5f9);
    border-radius: var(--radius-sm, 4px);
    position: relative;
    overflow: hidden;
  }

  .skeleton.animated::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
      90deg,
      transparent 0%,
      rgba(255, 255, 255, 0.4) 50%,
      transparent 100%
    );
    animation: shimmer 1.5s ease-in-out infinite;
    transform: translateX(-100%);
  }

  @keyframes shimmer {
    0% {
      transform: translateX(-100%);
    }
    100% {
      transform: translateX(100%);
    }
  }

  /* Text variant */
  .skeleton-text {
    height: 1rem;
    width: 100%;
  }

  /* Paragraph variant */
  .skeleton-paragraph {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  /* Card variant */
  .skeleton-card {
    width: 100%;
    height: 120px;
    border-radius: var(--radius, 8px);
  }

  /* Progress variant */
  .skeleton-progress-container {
    width: 100%;
    height: 12px;
    background: var(--color-bg, #ffffff);
    border-radius: 6px;
    overflow: hidden;
  }

  .skeleton-progress {
    width: 100%;
    height: 100%;
    border-radius: 6px;
  }

  /* Avatar variant */
  .skeleton-avatar {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  /* Dark mode support */
  :global([data-theme="dark"]) .skeleton {
    background: var(--color-bg-tertiary, #334155);
  }

  :global([data-theme="dark"]) .skeleton.animated::after {
    background: linear-gradient(
      90deg,
      transparent 0%,
      rgba(255, 255, 255, 0.1) 50%,
      transparent 100%
    );
  }
</style>
