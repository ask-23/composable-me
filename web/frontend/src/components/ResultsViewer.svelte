<script lang="ts">
  /**
   * ResultsViewer.svelte - Tabbed results display
   * Shows resume, cover letter, audit report, and intermediate results
   */

  import type { FinalDocuments, AuditReport } from '../lib/types';
  import MarkdownViewer from './MarkdownViewer.svelte';

  interface Props {
    documents?: FinalDocuments;
    auditReport?: AuditReport;
    intermediateResults?: Record<string, unknown>;
    auditFailed?: boolean;
    auditError?: string;
  }

  let {
    documents,
    auditReport,
    intermediateResults,
    auditFailed = false,
    auditError,
  }: Props = $props();

  type Tab = 'resume' | 'cover_letter' | 'audit' | 'debug';
  let activeTab = $state<Tab>('resume');

  // Derived values
  let hasDocuments = $derived(!!documents);
  let auditStatus = $derived(auditReport?.final_status || 'N/A');
  let auditStatusClass = $derived(
    auditStatus === 'APPROVED' ? 'success' :
    auditStatus === 'REJECTED' ? 'warning' :
    auditStatus === 'AUDIT_CRASHED' ? 'error' : ''
  );
</script>

<div class="results-viewer">
  <!-- Status banner -->
  {#if auditFailed}
    <div class="status-banner warning">
      <strong>Manual Review Required</strong>
      <p>{auditError || 'Audit did not pass. Please review documents carefully.'}</p>
    </div>
  {:else if auditStatus === 'APPROVED'}
    <div class="status-banner success">
      <strong>Audit Passed</strong>
      <p>Documents verified and ready to submit.</p>
    </div>
  {/if}

  <!-- Tab navigation -->
  <div class="tabs">
    <button
      class="tab"
      class:active={activeTab === 'resume'}
      onclick={() => activeTab = 'resume'}
    >
      Resume
    </button>
    <button
      class="tab"
      class:active={activeTab === 'cover_letter'}
      onclick={() => activeTab = 'cover_letter'}
    >
      Cover Letter
    </button>
    <button
      class="tab"
      class:active={activeTab === 'audit'}
      onclick={() => activeTab = 'audit'}
    >
      Audit Report
      <span class="badge {auditStatusClass}">{auditStatus}</span>
    </button>
    <button
      class="tab"
      class:active={activeTab === 'debug'}
      onclick={() => activeTab = 'debug'}
    >
      Debug
    </button>
  </div>

  <!-- Tab content -->
  <div class="tab-content">
    {#if activeTab === 'resume'}
      <div class="document-panel">
        <div class="document-header">
          <h3>Tailored Resume</h3>
          {#if documents?.resume}
            <button class="copy-btn" onclick={() => navigator.clipboard.writeText(documents.resume)}>
              Copy
            </button>
          {/if}
        </div>
        {#if documents?.resume}
          <MarkdownViewer content={documents.resume} />
        {:else}
          <p class="empty">No resume generated.</p>
        {/if}
      </div>

    {:else if activeTab === 'cover_letter'}
      <div class="document-panel">
        <div class="document-header">
          <h3>Cover Letter</h3>
          {#if documents?.cover_letter}
            <button class="copy-btn" onclick={() => navigator.clipboard.writeText(documents.cover_letter)}>
              Copy
            </button>
          {/if}
        </div>
        {#if documents?.cover_letter}
          <MarkdownViewer content={documents.cover_letter} />
        {:else}
          <p class="empty">No cover letter generated.</p>
        {/if}
      </div>

    {:else if activeTab === 'audit'}
      <div class="audit-panel">
        <h3>Audit Report</h3>
        {#if auditReport}
          <div class="audit-summary">
            <div class="audit-stat">
              <span class="label">Status</span>
              <span class="value {auditStatusClass}">{auditStatus}</span>
            </div>
            <div class="audit-stat">
              <span class="label">Retries</span>
              <span class="value">{auditReport.retry_count}</span>
            </div>
          </div>

          {#if auditReport.rejection_reason}
            <div class="audit-section warning">
              <h4>Rejection Reason</h4>
              <p>{auditReport.rejection_reason}</p>
            </div>
          {/if}

          {#if auditReport.crash_error}
            <div class="audit-section error">
              <h4>Crash Error</h4>
              <p>{auditReport.crash_error}</p>
            </div>
          {/if}

          {#if auditReport.resume_audit}
            <div class="audit-section">
              <h4>Resume Audit</h4>
              <pre>{JSON.stringify(auditReport.resume_audit, null, 2)}</pre>
            </div>
          {/if}

          {#if auditReport.cover_letter_audit}
            <div class="audit-section">
              <h4>Cover Letter Audit</h4>
              <pre>{JSON.stringify(auditReport.cover_letter_audit, null, 2)}</pre>
            </div>
          {/if}
        {:else}
          <p class="empty">No audit report available.</p>
        {/if}
      </div>

    {:else if activeTab === 'debug'}
      <div class="debug-panel">
        <h3>Intermediate Results</h3>
        {#if intermediateResults && Object.keys(intermediateResults).length > 0}
          {#each Object.entries(intermediateResults) as [stage, result]}
            <details class="debug-section">
              <summary>{stage}</summary>
              <pre>{JSON.stringify(result, null, 2)}</pre>
            </details>
          {/each}
        {:else}
          <p class="empty">No intermediate results available.</p>
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
  .results-viewer {
    background: var(--color-bg-secondary);
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    overflow: hidden;
  }

  .status-banner {
    padding: 1rem 1.5rem;
    border-bottom: 1px solid var(--color-border);
  }

  .status-banner strong {
    display: block;
    margin-bottom: 0.25rem;
  }

  .status-banner p {
    margin: 0;
    opacity: 0.9;
  }

  .status-banner.success {
    background: rgba(34, 197, 94, 0.1);
    color: var(--color-success);
  }

  .status-banner.warning {
    background: rgba(234, 179, 8, 0.1);
    color: var(--color-warning);
  }

  .tabs {
    display: flex;
    border-bottom: 1px solid var(--color-border);
    background: var(--color-bg);
    overflow-x: auto;
  }

  .tab {
    background: transparent;
    border: none;
    padding: 1rem 1.5rem;
    color: var(--color-text-muted);
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 500;
    border-bottom: 2px solid transparent;
    white-space: nowrap;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .tab:hover {
    color: var(--color-text);
    background: rgba(255, 255, 255, 0.02);
  }

  .tab.active {
    color: var(--color-primary);
    border-bottom-color: var(--color-primary);
  }

  .badge {
    font-size: 0.7rem;
    padding: 0.15rem 0.4rem;
    border-radius: 3px;
    background: var(--color-bg-secondary);
  }

  .badge.success {
    background: rgba(34, 197, 94, 0.2);
    color: var(--color-success);
  }

  .badge.warning {
    background: rgba(234, 179, 8, 0.2);
    color: var(--color-warning);
  }

  .badge.error {
    background: rgba(239, 68, 68, 0.2);
    color: var(--color-error);
  }

  .tab-content {
    padding: 1.5rem;
    min-height: 400px;
  }

  .document-panel,
  .audit-panel,
  .debug-panel {
    max-height: 600px;
    overflow-y: auto;
  }

  .document-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .document-header h3 {
    margin: 0;
  }

  .copy-btn {
    padding: 0.5rem 1rem;
    font-size: 0.8rem;
  }

  .empty {
    color: var(--color-text-muted);
    font-style: italic;
  }

  .audit-summary {
    display: flex;
    gap: 2rem;
    margin-bottom: 1.5rem;
  }

  .audit-stat {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .audit-stat .label {
    font-size: 0.8rem;
    color: var(--color-text-muted);
  }

  .audit-stat .value {
    font-size: 1.1rem;
    font-weight: 600;
  }

  .audit-stat .value.success {
    color: var(--color-success);
  }

  .audit-stat .value.warning {
    color: var(--color-warning);
  }

  .audit-stat .value.error {
    color: var(--color-error);
  }

  .audit-section {
    background: var(--color-bg);
    border-radius: var(--radius);
    padding: 1rem;
    margin-bottom: 1rem;
  }

  .audit-section h4 {
    margin-top: 0;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
  }

  .audit-section pre {
    margin: 0;
    font-size: 0.8rem;
    overflow-x: auto;
    color: var(--color-text-muted);
  }

  .audit-section.warning {
    border-left: 3px solid var(--color-warning);
  }

  .audit-section.error {
    border-left: 3px solid var(--color-error);
  }

  .debug-section {
    background: var(--color-bg);
    border-radius: var(--radius);
    margin-bottom: 0.5rem;
  }

  .debug-section summary {
    padding: 0.75rem 1rem;
    cursor: pointer;
    font-weight: 500;
  }

  .debug-section pre {
    padding: 0 1rem 1rem;
    margin: 0;
    font-size: 0.75rem;
    overflow-x: auto;
    color: var(--color-text-muted);
  }
</style>
