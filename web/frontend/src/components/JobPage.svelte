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

    // Track completion state reactively
    let isComplete = $state(
        initialJob.state === "completed" || initialJob.state === "failed",
    );
    let finalDocuments = $state<FinalDocuments | undefined>(
        initialJob.final_documents,
    );
    let auditReport = $state<AuditReport | undefined>(initialJob.audit_report);
    let executiveBrief = $state<ExecutiveBrief | undefined>(
        initialJob.executive_brief,
    );
    let intermediateResults = $state<Record<string, unknown>>(
        initialJob.intermediate_results || {},
    );
    let auditFailed = $state(initialJob.audit_failed);
    let auditError = $state<string | undefined>(initialJob.audit_error);
    let agentModels = $state<Record<string, string>>(
        initialJob.agent_models || {},
    );

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
