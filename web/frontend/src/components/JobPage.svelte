<script lang="ts">
    /**
     * JobPage.svelte - Main job page component with reactive results display
     * Shows progress tracker and dynamically reveals results when job completes
     */

    import { onMount } from "svelte";
    import JobProgress from "./JobProgress.svelte";
    import ResultsViewer from "./ResultsViewer.svelte";
    import GapAnalysisReview from "./reviews/GapAnalysisReview.svelte";
    import InterviewReview from "./reviews/InterviewReview.svelte";
    import type {
        Job,
        SSECompleteEvent,
        FinalDocuments,
        AuditReport,
        ExecutiveBrief,
        JobState,
        GapAnalysisResult,
        InterrogationResult,
    } from "../lib/types";

    interface Props {
        jobId: string;
        initialJob?: Job;
    }

    let { jobId, initialJob }: Props = $props();

    // Loading state for client-side fetch mode
    let isLoading = $state(!initialJob);
    let loadError = $state<string | null>(null);
    let job = $state<Job | undefined>(initialJob);

    // Client-side fetch when no initial job provided (e.g., for E2E tests with mocks)
    onMount(async () => {
        if (!initialJob) {
            try {
                // Use relative URL - this goes through browser and can be mocked by Playwright
                const response = await fetch(`/api/jobs/${jobId}`);
                if (response.ok) {
                    job = await response.json();
                } else if (response.status === 404) {
                    loadError = "Job not found";
                } else {
                    loadError = `Failed to load job: HTTP ${response.status}`;
                }
            } catch (e) {
                loadError = "Failed to connect to backend";
            } finally {
                isLoading = false;
            }
        }
    });

    // Track state - initialized from job when available
    let currentState = $state<JobState>(job?.state || "initialized");
    let isComplete = $state(job?.state === "completed" || job?.state === "failed");
    let finalDocuments = $state<FinalDocuments | undefined>(job?.final_documents);
    let auditReport = $state<AuditReport | undefined>(job?.audit_report);
    let executiveBrief = $state<ExecutiveBrief | undefined>(job?.executive_brief);
    let intermediateResults = $state<Record<string, unknown>>(job?.intermediate_results || {});
    let auditFailed = $state(job?.audit_failed);
    let auditError = $state<string | undefined>(job?.audit_error);
    let agentModels = $state<Record<string, string>>(job?.agent_models || {});

    // Sync state when job is loaded client-side
    $effect(() => {
        if (job && !initialJob) {
            currentState = job.state;
            isComplete = job.state === "completed" || job.state === "failed";
            finalDocuments = job.final_documents;
            auditReport = job.audit_report;
            executiveBrief = job.executive_brief;
            intermediateResults = job.intermediate_results || {};
            auditFailed = job.audit_failed;
            auditError = job.audit_error;
            agentModels = job.agent_models || {};
        }
    });

    // Defensive: refresh job data when entering review states without intermediate results
    $effect(() => {
        if (currentState === "gap_analysis_review" && !intermediateResults.gap_analysis) {
            refreshJob();
        }
        if (currentState === "interrogation_review" && !intermediateResults.interrogation) {
            refreshJob();
        }
    });

    /**
     * refreshJob - Fetch latest job state from API and update local state
     * Used after HITL actions to ensure state is current even if SSE drops
     */
    async function refreshJob(): Promise<void> {
        try {
            const response = await fetch(`/api/jobs/${jobId}`);
            if (response.ok) {
                const latestJob: Job = await response.json();
                // Update all state from fresh API response
                currentState = latestJob.state;
                isComplete = latestJob.state === "completed" || latestJob.state === "failed";
                finalDocuments = latestJob.final_documents;
                auditReport = latestJob.audit_report;
                executiveBrief = latestJob.executive_brief;
                intermediateResults = latestJob.intermediate_results || {};
                auditFailed = latestJob.audit_failed;
                auditError = latestJob.audit_error;
                agentModels = latestJob.agent_models || {};
                job = latestJob;
            }
        } catch (e) {
            console.error("Failed to refresh job state:", e);
        }
    }

    /**
     * pollForStateChange - Poll API until state changes from current review state
     * Implements bounded condition-based waiting with max attempts
     */
    async function pollForStateChange(fromState: JobState, maxAttempts = 10, intervalMs = 500): Promise<void> {
        for (let attempt = 0; attempt < maxAttempts; attempt++) {
            await refreshJob();
            if (currentState !== fromState) {
                // State changed - polling successful
                return;
            }
            // Wait before next poll
            await new Promise(r => setTimeout(r, intervalMs));
        }
        // Max attempts reached - state may not have changed yet, but we stop polling
        console.warn(`Polling stopped after ${maxAttempts} attempts - state still: ${currentState}`);
    }

    function handleStateChange(newState: JobState) {
        currentState = newState;
    }

    function handleStageComplete(
        stage: string,
        result: Record<string, unknown>,
    ) {
        intermediateResults = { ...intermediateResults, [stage]: result };
    }

    function handleComplete(event: SSECompleteEvent) {
        currentState = event.state;
        isComplete = event.state === "completed" || event.state === "failed";
        finalDocuments = event.final_documents;
        auditReport = event.audit_report;
        executiveBrief = event.executive_brief;
        auditFailed = event.audit_failed;
        auditError = event.audit_error;
        agentModels = event.agent_models || {};

        // Defensive: If complete but critical data is missing, refresh from API
        // This handles edge cases where SSE event was incomplete
        if (isComplete && !executiveBrief && !finalDocuments) {
            console.warn("Complete event missing critical data, refreshing from API");
            refreshJob();
        }

        // Only scroll if we are actually complete
        if (isComplete) {
            setTimeout(() => {
                const resultsSection =
                    document.querySelector(".results-section");
                if (resultsSection) {
                    resultsSection.scrollIntoView({
                        behavior: "smooth",
                        block: "start",
                    });
                }
            }, 300);
        }
    }
</script>

{#if isLoading}
    <div class="card loading-card">
        <p>Loading job status...</p>
    </div>
{:else if loadError}
    <div class="card error-card">
        <h2>Error</h2>
        <p>{loadError}</p>
    </div>
{:else}
    <!-- Progress tracker -->
    <div class="card progress-card">
        <JobProgress
            {jobId}
            initialState={job?.state || "initialized"}
            initialProgress={job?.progress_percent || 0}
            startedAt={job?.started_at}
            onComplete={handleComplete}
            onStateChange={handleStateChange}
            onStageComplete={handleStageComplete}
        />
    </div>
{/if}

<!-- HITL Reviews -->
{#if currentState === "gap_analysis_review"}
    <GapAnalysisReview
        {jobId}
        gapAnalysis={intermediateResults.gap_analysis as GapAnalysisResult}
        onApprove={async () => {
            // Poll for state change after approval (HITL resilience)
            await pollForStateChange("gap_analysis_review");
        }}
    />
{:else if currentState === "interrogation_review"}
    <InterviewReview
        {jobId}
        interviewPrep={intermediateResults.interrogation as InterrogationResult}
        onSubmit={async () => {
            // Poll for state change after submit (HITL resilience)
            await pollForStateChange("interrogation_review");
        }}
    />
{/if}

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

    .waiting-card,
    .loading-card {
        text-align: center;
        padding: 3rem;
        color: var(--color-text-muted);
    }

    .error-card {
        text-align: center;
        padding: 2rem;
        background: rgba(239, 68, 68, 0.1);
        border-color: var(--color-error);
    }

    .error-card h2 {
        color: var(--color-error);
        margin-bottom: 0.5rem;
    }

    .card {
        background: var(--color-bg-secondary);
        border: 1px solid var(--color-border);
        border-radius: var(--radius);
        padding: 1.5rem;
    }
</style>
