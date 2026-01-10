<script lang="ts">
  /**
   * MarkdownViewer.svelte - Renders markdown content as HTML
   */

  import { marked } from 'marked';

  interface Props {
    content: string;
  }

  let { content }: Props = $props();

  // Configure marked for safe rendering
  marked.setOptions({
    gfm: true,
    breaks: true,
  });

  // Derived HTML content
  let html = $derived(marked.parse(content) as string);
</script>

<div class="markdown-content">
  {@html html}
</div>

<style>
  .markdown-content {
    line-height: 1.7;
  }

  .markdown-content :global(h1) {
    font-size: 1.5rem;
    margin: 1.5rem 0 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--color-border);
  }

  .markdown-content :global(h2) {
    font-size: 1.25rem;
    margin: 1.25rem 0 0.75rem;
  }

  .markdown-content :global(h3) {
    font-size: 1.1rem;
    margin: 1rem 0 0.5rem;
  }

  .markdown-content :global(p) {
    margin: 0.75rem 0;
  }

  .markdown-content :global(ul),
  .markdown-content :global(ol) {
    margin: 0.75rem 0;
    padding-left: 1.5rem;
  }

  .markdown-content :global(li) {
    margin: 0.25rem 0;
  }

  .markdown-content :global(strong) {
    font-weight: 600;
  }

  .markdown-content :global(em) {
    font-style: italic;
  }

  .markdown-content :global(code) {
    background: var(--color-bg);
    padding: 0.15rem 0.4rem;
    border-radius: 3px;
    font-family: monospace;
    font-size: 0.9em;
  }

  .markdown-content :global(pre) {
    background: var(--color-bg);
    padding: 1rem;
    border-radius: var(--radius);
    overflow-x: auto;
    margin: 1rem 0;
  }

  .markdown-content :global(pre code) {
    background: none;
    padding: 0;
  }

  .markdown-content :global(blockquote) {
    border-left: 3px solid var(--color-primary);
    padding-left: 1rem;
    margin: 1rem 0;
    color: var(--color-text-muted);
  }

  .markdown-content :global(hr) {
    border: none;
    border-top: 1px solid var(--color-border);
    margin: 1.5rem 0;
  }

  .markdown-content :global(a) {
    color: var(--color-primary);
  }

  .markdown-content :global(table) {
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
  }

  .markdown-content :global(th),
  .markdown-content :global(td) {
    padding: 0.5rem;
    border: 1px solid var(--color-border);
    text-align: left;
  }

  .markdown-content :global(th) {
    background: var(--color-bg);
    font-weight: 600;
  }
</style>
