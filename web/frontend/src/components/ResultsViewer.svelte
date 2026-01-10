<script lang="ts">
  /**
   * ResultsViewer.svelte - Gorgeous results display with TLDR summary
   * Shows verdict, executive summary, resume, cover letter, and action items
   */

  import type {
    FinalDocuments,
    AuditReport,
    ExecutiveBrief,
  } from "../lib/types";
  import MarkdownViewer from "./MarkdownViewer.svelte";

  interface Props {
    documents?: FinalDocuments;
    auditReport?: AuditReport;
    executiveBrief?: ExecutiveBrief;
    intermediateResults?: Record<string, unknown>;
    auditFailed?: boolean;
    auditError?: string;
    agentModels?: Record<string, string>;
  }

  let {
    documents,
    auditReport,
    executiveBrief,
    intermediateResults,
    auditFailed = false,
    auditError,
    agentModels = {},
  }: Props = $props();

  type Tab = "summary" | "resume" | "cover_letter" | "audit" | "debug";
  let activeTab = $state<Tab>("summary");

  // Derived values
  let hasDocuments = $derived(!!documents?.resume || !!documents?.cover_letter);
  let auditStatus = $derived(auditReport?.final_status || "PENDING");

  // Verdict mapping - prioritize executive brief recommendation
  let verdict = $derived(() => {
    // Use executive brief recommendation if available
    if (executiveBrief?.decision?.recommendation) {
      const rec = executiveBrief.decision.recommendation;
      switch (rec) {
        case "STRONG_PROCEED":
          return { label: "STRONG PROCEED", class: "success", icon: "🚀" };
        case "PROCEED":
          return { label: "PROCEED", class: "success", icon: "✓" };
        case "PROCEED_WITH_CAUTION":
          return { label: "CAUTION", class: "warning", icon: "⚠️" };
        case "PASS":
          return { label: "PASS", class: "error", icon: "✗" };
      }
    }

    // Fallback to audit status
    if (auditFailed)
      return { label: "NEEDS REVIEW", class: "warning", icon: "⚠️" };
    switch (auditStatus) {
      case "APPROVED":
        return { label: "APPROVED", class: "success", icon: "✓" };
      case "REJECTED":
        return { label: "REJECTED", class: "error", icon: "✗" };
      case "AUDIT_CRASHED":
        return { label: "INCOMPLETE", class: "error", icon: "!" };
      default:
        return { label: "MIXED", class: "warning", icon: "◐" };
    }
  });

  // Extract action items from executive brief or audit report
  let actionItems = $derived(() => {
    const items: string[] = [];

    // Use executive brief action items if available
    if (executiveBrief?.action_items?.immediate) {
      items.push(...executiveBrief.action_items.immediate);
    }

    // Add fallbacks
    if (auditError) items.push(auditError);
    if (auditReport?.rejection_reason) items.push(auditReport.rejection_reason);

    // Add generic recommendations if nothing else
    if (items.length === 0 && auditStatus === "APPROVED") {
      items.push("Your documents are ready to submit!");
      items.push(
        "Consider updating your LinkedIn profile to match your tailored resume",
      );
    }
    return items;
  });

  // Generate executive summary from executive brief or intermediate results
  let executiveSummary = $derived(() => {
    const summary: string[] = [];

    // Use executive brief if available
    if (executiveBrief?.decision) {
      const decision = executiveBrief.decision;
      const fitScore = decision.fit_score || 0;

      summary.push(`## ${decision.recommendation?.replace(/_/g, " ")}`);
      summary.push("");
      summary.push(`**Fit Score**: ${fitScore}%`);
      summary.push("");

      if (decision.rationale) {
        summary.push(decision.rationale);
        summary.push("");
      }

      if (executiveBrief.strategic_angle?.primary_hook) {
        summary.push(
          `🎯 **Your Hook**: "${executiveBrief.strategic_angle.primary_hook}"`,
        );
        summary.push("");
      }

      if (decision.deal_makers && decision.deal_makers.length > 0) {
        summary.push("✅ **Deal Makers**:");
        for (const maker of decision.deal_makers) {
          summary.push(`- ${maker}`);
        }
        summary.push("");
      }

      if (
        executiveBrief.gap_strategy?.critical_gaps &&
        executiveBrief.gap_strategy.critical_gaps.length > 0
      ) {
        summary.push("⚠️ **Gaps to Address**:");
        for (const gap of executiveBrief.gap_strategy.critical_gaps) {
          summary.push(`- **${gap.gap}**: ${gap.mitigation}`);
        }
      }

      return summary.join("\n");
    }

    // Fallback to intermediate results analysis
    const gapAnalysis = intermediateResults?.gap_analysis as
      | Record<string, unknown>
      | undefined;
    const differentiation = intermediateResults?.differentiation as
      | Record<string, unknown>
      | undefined;

    summary.push(
      "**The Hydra team has completed your application materials.**",
    );
    summary.push("");

    if (gapAnalysis) {
      const gaps = (gapAnalysis.gaps as unknown[])?.length || 0;
      const matches = (gapAnalysis.matches as unknown[])?.length || 0;
      if (matches > 0 || gaps > 0) {
        summary.push(
          `📊 **Gap Analysis**: Found ${matches} skill matches and ${gaps} areas addressed through narrative framing.`,
        );
      }
    }

    if (differentiation) {
      const differentiators =
        (differentiation.differentiators as unknown[])?.length || 0;
      if (differentiators > 0) {
        summary.push(
          `🎯 **Differentiation**: Identified ${differentiators} unique value propositions that set you apart.`,
        );
      }
    }

    summary.push("");
    summary.push(
      `🔍 **Audit Status**: ${auditStatus === "APPROVED" ? "All verification checks passed" : "Some items flagged for review"}`,
    );

    if (auditReport?.retry_count && auditReport.retry_count > 0) {
      summary.push(
        `🔄 **Refinements**: Documents were refined ${auditReport.retry_count} time(s) to meet quality standards.`,
      );
    }

    return summary.join("\n");
  });
</script>

<div class="results-viewer">
  <!-- TLDR Hero Section -->
  <div class="tldr-hero {verdict().class}">
    <div class="verdict-badge">
      <span class="verdict-icon">{verdict().icon}</span>
      <span class="verdict-label">{verdict().label}</span>
    </div>
    <div class="tldr-title">
      <h2>Your Application Materials Are Ready</h2>
      <p class="tldr-subtitle">
        {#if hasDocuments}
          Hydra's 6-agent team has tailored your resume and cover letter for
          this role.
        {:else}
          Processing encountered an issue. Check the audit report for details.
        {/if}
      </p>
    </div>
  </div>

  <!-- Tab navigation -->
  <div class="tabs">
    <button
      class="tab"
      class:active={activeTab === "summary"}
      onclick={() => (activeTab = "summary")}
    >
      📋 Summary
    </button>
    <button
      class="tab"
      class:active={activeTab === "resume"}
      onclick={() => (activeTab = "resume")}
    >
      📄 Resume
    </button>
    <button
      class="tab"
      class:active={activeTab === "cover_letter"}
      onclick={() => (activeTab = "cover_letter")}
    >
      ✉️ Cover Letter
    </button>
    <button
      class="tab"
      class:active={activeTab === "audit"}
      onclick={() => (activeTab = "audit")}
    >
      🔍 Audit
      <span class="badge {verdict().class}">{auditStatus}</span>
    </button>
    <button
      class="tab"
      class:active={activeTab === "debug"}
      onclick={() => (activeTab = "debug")}
    >
      🐛 Debug
    </button>
  </div>

  <!-- Tab content -->
  <div class="tab-content">
    {#if activeTab === "summary"}
      <div class="summary-panel">
        <div class="executive-summary">
          <h3>Executive Summary</h3>
          <MarkdownViewer content={executiveSummary()} />
        </div>

        {#if actionItems().length > 0}
          <div class="action-items">
            <h3>Next Steps</h3>
            <ul>
              {#each actionItems() as item}
                <li>{item}</li>
              {/each}
            </ul>
          </div>
        {/if}

        {#if Object.keys(agentModels).length > 0}
          <div class="agent-summary">
            <h3>Agents Involved</h3>
            <div class="agent-grid">
              {#each Object.entries(agentModels) as [stage, model]}
                <div class="agent-chip">
                  <span class="agent-stage">{stage.replace(/_/g, " ")}</span>
                  <span class="agent-model">{model.split("/").pop()}</span>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    {:else if activeTab === "resume"}
      <div class="document-panel">
        <div class="document-header">
          <h3>Tailored Resume</h3>
          {#if documents?.resume}
            <button
              class="copy-btn"
              onclick={() => navigator.clipboard.writeText(documents.resume)}
            >
              📋 Copy
            </button>
          {/if}
        </div>
        {#if documents?.resume}
          <div class="document-content">
            <MarkdownViewer content={documents.resume} />
          </div>
        {:else}
          <p class="empty">No resume generated.</p>
        {/if}
      </div>
    {:else if activeTab === "cover_letter"}
      <div class="document-panel">
        <div class="document-header">
          <h3>Cover Letter</h3>
          {#if documents?.cover_letter}
            <button
              class="copy-btn"
              onclick={() =>
                navigator.clipboard.writeText(documents.cover_letter)}
            >
              📋 Copy
            </button>
          {/if}
        </div>
        {#if documents?.cover_letter}
          <div class="document-content">
            <MarkdownViewer content={documents.cover_letter} />
          </div>
        {:else}
          <p class="empty">No cover letter generated.</p>
        {/if}
      </div>
    {:else if activeTab === "audit"}
      <div class="audit-panel">
        <h3>Audit Report</h3>
        {#if auditReport}
          <div class="audit-summary">
            <div class="audit-stat">
              <span class="label">Status</span>
              <span class="value {verdict().class}">{auditStatus}</span>
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
              <h4>Error</h4>
              <p>{auditReport.crash_error}</p>
            </div>
          {/if}

          {#if auditReport.resume_audit}
            <details class="audit-details">
              <summary>Resume Audit Details</summary>
              <pre>{JSON.stringify(auditReport.resume_audit, null, 2)}</pre>
            </details>
          {/if}

          {#if auditReport.cover_letter_audit}
            <details class="audit-details">
              <summary>Cover Letter Audit Details</summary>
              <pre>{JSON.stringify(
                  auditReport.cover_letter_audit,
                  null,
                  2,
                )}</pre>
            </details>
          {/if}
        {:else}
          <p class="empty">No audit report available.</p>
        {/if}
      </div>
    {:else if activeTab === "debug"}
      <div class="debug-panel">
        <h3>Intermediate Results</h3>
        {#if intermediateResults && Object.keys(intermediateResults).length > 0}
          {#each Object.entries(intermediateResults) as [stage, result]}
            <details class="debug-section">
              <summary>
                {stage.replace(/_/g, " ")}
                {#if agentModels[stage]}
                  <span class="model-tag"
                    >{agentModels[stage].split("/").pop()}</span
                  >
                {/if}
              </summary>
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

  /* TLDR Hero Section */
  .tldr-hero {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    padding: 1.5rem 2rem;
    background: linear-gradient(
      135deg,
      rgba(59, 130, 246, 0.1) 0%,
      rgba(147, 51, 234, 0.1) 100%
    );
    border-bottom: 1px solid var(--color-border);
  }

  .tldr-hero.success {
    background: linear-gradient(
      135deg,
      rgba(34, 197, 94, 0.15) 0%,
      rgba(16, 185, 129, 0.1) 100%
    );
  }

  .tldr-hero.warning {
    background: linear-gradient(
      135deg,
      rgba(234, 179, 8, 0.15) 0%,
      rgba(245, 158, 11, 0.1) 100%
    );
  }

  .tldr-hero.error {
    background: linear-gradient(
      135deg,
      rgba(239, 68, 68, 0.15) 0%,
      rgba(220, 38, 38, 0.1) 100%
    );
  }

  .verdict-badge {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 80px;
    height: 80px;
    border-radius: 12px;
    background: var(--color-bg);
    border: 2px solid var(--color-border);
    flex-shrink: 0;
  }

  .tldr-hero.success .verdict-badge {
    border-color: var(--color-success);
    color: var(--color-success);
  }

  .tldr-hero.warning .verdict-badge {
    border-color: var(--color-warning);
    color: var(--color-warning);
  }

  .tldr-hero.error .verdict-badge {
    border-color: var(--color-error);
    color: var(--color-error);
  }

  .verdict-icon {
    font-size: 1.8rem;
    line-height: 1;
  }

  .verdict-label {
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.25rem;
  }

  .tldr-title h2 {
    margin: 0 0 0.25rem 0;
    font-size: 1.3rem;
    color: var(--color-text);
  }

  .tldr-subtitle {
    margin: 0;
    color: var(--color-text-muted);
    font-size: 0.95rem;
  }

  /* Tabs */
  .tabs {
    display: flex;
    border-bottom: 1px solid var(--color-border);
    background: var(--color-bg);
    overflow-x: auto;
  }

  .tab {
    background: transparent;
    border: none;
    padding: 0.85rem 1.25rem;
    color: var(--color-text-muted);
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: 500;
    border-bottom: 2px solid transparent;
    white-space: nowrap;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    transition: all 0.2s;
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
    font-size: 0.65rem;
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

  /* Summary Panel */
  .summary-panel {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .executive-summary,
  .action-items,
  .agent-summary {
    background: var(--color-bg);
    border-radius: var(--radius);
    padding: 1.25rem;
  }

  .executive-summary h3,
  .action-items h3,
  .agent-summary h3 {
    margin: 0 0 1rem 0;
    font-size: 1rem;
    color: var(--color-text);
  }

  .action-items ul {
    margin: 0;
    padding-left: 1.5rem;
  }

  .action-items li {
    margin-bottom: 0.5rem;
    color: var(--color-text-muted);
  }

  .agent-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .agent-chip {
    display: flex;
    flex-direction: column;
    background: var(--color-bg-secondary);
    border: 1px solid var(--color-border);
    border-radius: 6px;
    padding: 0.5rem 0.75rem;
  }

  .agent-stage {
    font-size: 0.7rem;
    text-transform: capitalize;
    color: var(--color-text-muted);
  }

  .agent-model {
    font-size: 0.75rem;
    font-family: monospace;
    color: var(--color-primary);
  }

  /* Document Panel */
  .document-panel {
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
    background: var(--color-bg);
    border: 1px solid var(--color-border);
    border-radius: 4px;
    cursor: pointer;
  }

  .copy-btn:hover {
    background: var(--color-bg-secondary);
  }

  .document-content {
    background: var(--color-bg);
    border-radius: var(--radius);
    padding: 1.5rem;
    line-height: 1.6;
  }

  .empty {
    color: var(--color-text-muted);
    font-style: italic;
  }

  /* Audit Panel */
  .audit-panel {
    max-height: 600px;
    overflow-y: auto;
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
    font-size: 0.75rem;
    color: var(--color-text-muted);
    text-transform: uppercase;
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
    margin: 0 0 0.5rem 0;
    font-size: 0.9rem;
  }

  .audit-section.warning {
    border-left: 3px solid var(--color-warning);
  }
  .audit-section.error {
    border-left: 3px solid var(--color-error);
  }

  .audit-details {
    background: var(--color-bg);
    border-radius: var(--radius);
    margin-bottom: 0.5rem;
  }

  .audit-details summary {
    padding: 0.75rem 1rem;
    cursor: pointer;
    font-weight: 500;
  }

  .audit-details pre {
    padding: 0 1rem 1rem;
    margin: 0;
    font-size: 0.75rem;
    overflow-x: auto;
    color: var(--color-text-muted);
  }

  /* Debug Panel */
  .debug-panel {
    max-height: 600px;
    overflow-y: auto;
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
    text-transform: capitalize;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .model-tag {
    font-size: 0.7rem;
    padding: 0.1rem 0.4rem;
    border-radius: 3px;
    background: var(--color-bg-secondary);
    color: var(--color-text-muted);
    border: 1px solid var(--color-border);
    font-family: monospace;
  }

  .debug-section pre {
    padding: 0 1rem 1rem;
    margin: 0;
    font-size: 0.75rem;
    overflow-x: auto;
    color: var(--color-text-muted);
  }
</style>
