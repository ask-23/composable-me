<script lang="ts">
    /**
     * JobPage.svelte - Main job page component with reactive results display
     * Shows progress tracker and dynamically reveals results when job completes
     */

    import JobProgress from "./JobProgress.svelte";
    import ResultsViewer from "./ResultsViewer.svelte";
    import type {
        Job,
        SSECompleteEvent,
        FinalDocuments,
        AuditReport,
        ExecutiveBrief,
    } from "../lib/types";

    interface Props {
        jobId: string;
        initialJob: Job;
    }

    let { jobId, initialJob }: Props = $props();

    // Extract initial values from props (avoids state_referenced_locally warnings)
    // These are intentionally one-time captures - SSE events update the state later
    const initialState = initialJob.state;
    const initialComplete =
        initialState === "completed" || initialState === "failed";
    const initialDocs = initialJob.final_documents;
    const initialAudit = initialJob.audit_report;
    const initialBrief = initialJob.executive_brief;
    const initialIntermediate = initialJob.intermediate_results || {};
    const initialAuditFailed = initialJob.audit_failed;
    const initialAuditError = initialJob.audit_error;
    const initialModels = initialJob.agent_models || {};

    // Track completion state reactively - we capture initial values and update via SSE
    let isComplete = $state(initialComplete);
    let finalDocuments = $state<FinalDocuments | undefined>(initialDocs);
    let auditReport = $state<AuditReport | undefined>(initialAudit);
    let executiveBrief = $state<ExecutiveBrief | undefined>(initialBrief);
    let intermediateResults =
        $state<Record<string, unknown>>(initialIntermediate);
    let auditFailed = $state(initialAuditFailed);
    let auditError = $state<string | undefined>(initialAuditError);
    let agentModels = $state<Record<string, string>>(initialModels);

    function handleComplete(event: SSECompleteEvent) {
        isComplete = true;
        finalDocuments = event.final_documents;
        auditReport = event.audit_report;
        executiveBrief = event.executive_brief;
        auditFailed = event.audit_failed;
        auditError = event.audit_error;
        agentModels = event.agent_models || {};

        // Scroll to results after a short delay
        setTimeout(() => {
            const resultsSection = document.querySelector(".results-section");
            if (resultsSection) {
                resultsSection.scrollIntoView({
                    behavior: "smooth",
                    block: "start",
                });
            }
        }, 300);
    }
</script>

<!-- Progress tracker -->
<div class="card progress-card">
    <JobProgress
        {jobId}
        initialState={initialJob.state}
        onComplete={handleComplete}
    />
</div>

<!-- Results viewer (appears when complete) -->
{#if isComplete}
    <div class="results-section">
        <ResultsViewer
            documents={finalDocuments}
            {auditReport}
            {executiveBrief}
            {intermediateResults}
            {auditFailed}
            {auditError}
            {agentModels}
        />
    </div>
{:else}
    <div class="waiting-card card">
        <p>Results will appear here when processing completes...</p>
    </div>
{/if}

<style>
    .progress-card {
        margin-bottom: 2rem;
    }

    .results-section {
        margin-top: 2rem;
    }

    .waiting-card {
        text-align: center;
        padding: 3rem;
        color: var(--color-text-muted);
    }

    .card {
        background: var(--color-bg-secondary);
        border: 1px solid var(--color-border);
        border-radius: var(--radius);
        padding: 1.5rem;
    }
</style>
