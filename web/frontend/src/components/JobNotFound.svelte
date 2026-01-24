<script lang="ts">
  /**
   * JobNotFound.svelte - Friendly 404 state for invalid job IDs
   * Shows helpful guidance when a job cannot be found
   */

  interface Props {
    jobId?: string;
  }

  let { jobId }: Props = $props();
</script>

<div class="not-found">
  <div class="not-found-icon">
    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
      <circle cx="11" cy="11" r="8"/>
      <path d="m21 21-4.35-4.35"/>
      <path d="M11 8v2M11 14h.01"/>
    </svg>
  </div>

  <h2 class="not-found-title">Job Not Found</h2>

  <p class="not-found-description">
    We couldn't find a job with this ID. This can happen when:
  </p>

  <ul class="not-found-reasons">
    <li>The job has expired or been deleted</li>
    <li>The server was restarted and job data was cleared</li>
    <li>The link you followed is incorrect or incomplete</li>
  </ul>

  {#if jobId}
    <p class="not-found-id">
      Looking for: <code>{jobId}</code>
    </p>
  {/if}

  <div class="not-found-actions">
    <a href="/" class="btn-primary">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
        <polyline points="9,22 9,12 15,12 15,22"/>
      </svg>
      Start a New Job
    </a>
  </div>
</div>

<style>
  .not-found {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 3rem 1.5rem;
    background: var(--color-bg-secondary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
  }

  .not-found-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100px;
    height: 100px;
    background: rgba(239, 68, 68, 0.1);
    border-radius: 50%;
    margin-bottom: 1.5rem;
    color: var(--color-error);
  }

  .not-found-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--color-text);
    margin: 0 0 0.75rem 0;
  }

  .not-found-description {
    color: var(--color-text-muted);
    font-size: 0.95rem;
    margin: 0 0 1rem 0;
    max-width: 400px;
  }

  .not-found-reasons {
    text-align: left;
    color: var(--color-text-muted);
    font-size: 0.875rem;
    margin: 0 0 1.5rem 0;
    padding-left: 1.5rem;
    max-width: 400px;
  }

  .not-found-reasons li {
    margin-bottom: 0.375rem;
  }

  .not-found-id {
    color: var(--color-text-muted);
    font-size: 0.8rem;
    margin: 0 0 1.5rem 0;
  }

  .not-found-id code {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    background: var(--color-bg);
    border: 1px solid var(--color-border);
    border-radius: 4px;
    font-family: monospace;
    font-size: 0.75rem;
    color: var(--color-text);
    word-break: break-all;
    max-width: 300px;
  }

  .not-found-actions {
    display: flex;
    gap: 1rem;
  }

  .btn-primary {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    background: var(--color-primary);
    color: white;
    border-radius: var(--radius);
    text-decoration: none;
    font-weight: 500;
    font-size: 0.95rem;
    transition: transform 0.2s, box-shadow 0.2s, background 0.2s;
  }

  .btn-primary:hover {
    background: var(--color-primary-hover);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    text-decoration: none;
  }
</style>
