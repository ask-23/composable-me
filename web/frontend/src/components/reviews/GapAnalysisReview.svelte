<script lang="ts">
    /**
     * GapAnalysisReview.svelte
     * HITL interface for reviewing and approving gap analysis findings.
     */
    import { approveGapAnalysis } from "../../lib/api/hitl";
    import type { Job, GapAnalysisResult } from "../../lib/types";

    interface Props {
        jobId: string;
        gapAnalysis?: GapAnalysisResult;
        onApprove: () => void;
    }

    let { jobId, gapAnalysis, onApprove }: Props = $props();

    let isSubmitting = $state(false);
    let error = $state<string | null>(null);

    // Get the actual analysis data - handle both flat and nested structures
    // Backend returns: { agent, gap_analysis: { summary: { fit_score }, requirements: [...] } }
    let analysisData = $derived(gapAnalysis?.gap_analysis ?? gapAnalysis);

    // Derived analysis data - handle both flat and nested structures
    let matchScore = $derived(
        typeof analysisData?.fit_score === "number"
            ? analysisData.fit_score
            : typeof analysisData?.summary?.fit_score === "number"
              ? analysisData.summary.fit_score
              : typeof gapAnalysis?.fit_score === "number"
                ? gapAnalysis.fit_score
                : 0,
    );

    // Helper to extract items from analysis
    function getItems(type: "matches" | "gaps" | "adjacent"): string[] {
        if (!analysisData && !gapAnalysis) return [];

        const data = analysisData ?? gapAnalysis;

        // 1. Try direct arrays
        if (type === "matches" && data?.matches?.length)
            return data.matches;
        if (type === "gaps" && data?.gaps?.length)
            return data.gaps;
        if (type === "adjacent" && data?.adjacent_skills?.length)
            return data.adjacent_skills;

        // 2. Try parsing requirements list (check multiple locations)
        const requirements =
            data?.requirements ||
            data?.requirements_analysis?.explicit_required ||
            gapAnalysis?.requirements ||
            [];

        if (!requirements.length) return [];

        return requirements
            .filter((r: any) => {
                const cls = r.classification;
                if (type === "matches") return cls === "direct_match";
                if (type === "gaps") return cls === "gap" || cls === "blocker";
                if (type === "adjacent")
                    return cls === "adjacent" || cls === "adjacent_experience";
                return false;
            })
            .map((r: any) => r.requirement || r.text || JSON.stringify(r)); // Handle potential 'text' field from logs
    }

    let matches = $derived(getItems("matches"));
    let gaps = $derived(getItems("gaps"));
    let adjacent = $derived(getItems("adjacent"));

    async function handleApprove() {
        isSubmitting = true;
        error = null;
        try {
            await approveGapAnalysis(jobId, true);
            onApprove();
        } catch (e) {
            error =
                e instanceof Error ? e.message : "Failed to approve analysis";
        } finally {
            isSubmitting = false;
        }
    }
</script>

<div class="review-card card">
    <div class="header">
        <div class="icon">🔍</div>
        <div class="title">
            <h2>Review Gap Analysis</h2>
            <p>
                The agents have analyzed your profile against the job
                description. Please review the findings to continue.
            </p>
        </div>
        <div class="score">
            <div class="score-value">{matchScore}</div>
            <div class="score-label">Fit Score</div>
        </div>
    </div>

    <div class="content">
        <div class="column">
            <h3>✅ Direct Matches</h3>
            {#if matches.length > 0}
                <ul>
                    {#each matches as match}
                        <li>{match}</li>
                    {/each}
                </ul>
            {:else}
                <p class="empty">No direct matches found</p>
            {/if}
        </div>

        <div class="column">
            <h3>⚠️ Gaps Identified</h3>
            {#if gaps.length > 0}
                <ul>
                    {#each gaps as gap}
                        <li>{gap}</li>
                    {/each}
                </ul>
            {:else}
                <p class="empty">No gaps identified</p>
            {/if}
        </div>

        <div class="column">
            <h3>🔄 Adjacent Skills</h3>
            {#if adjacent.length > 0}
                <ul>
                    {#each adjacent as skill}
                        <li>{skill}</li>
                    {/each}
                </ul>
            {:else}
                <p class="empty">No adjacent skills found</p>
            {/if}
        </div>
    </div>

    {#if error}
        <div class="error-banner">{error}</div>
    {/if}

    <div class="actions">
        <button
            class="btn-primary"
            onclick={handleApprove}
            disabled={isSubmitting}
        >
            {#if isSubmitting}
                Processing...
            {:else}
                Approve & Continue
            {/if}
        </button>
    </div>
</div>

<style>
    .card {
        background: var(--color-bg-secondary);
        border: 1px solid var(--color-border);
        border-radius: var(--radius);
        padding: 2rem;
        margin: 2rem 0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }

    .header {
        display: flex;
        gap: 1.5rem;
        align-items: flex-start;
        margin-bottom: 2rem;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid var(--color-border);
    }

    .icon {
        font-size: 2.5rem;
        background: var(--color-bg-tertiary);
        width: 64px;
        height: 64px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 12px;
    }

    .title {
        flex: 1;
    }

    .title h2 {
        margin: 0 0 0.5rem 0;
        font-size: 1.5rem;
        color: var(--color-text);
    }

    .title p {
        margin: 0;
        color: var(--color-text-muted);
        font-size: 1rem;
        line-height: 1.5;
    }

    .score {
        text-align: center;
        background: rgba(59, 130, 246, 0.1);
        padding: 1rem;
        border-radius: 12px;
        min-width: 100px;
    }

    .score-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--color-primary);
    }

    .score-label {
        font-size: 0.8rem;
        color: var(--color-text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .content {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 2rem;
        margin-bottom: 2rem;
    }

    .column h3 {
        font-size: 1.1rem;
        margin-bottom: 1rem;
        color: var(--color-text);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    ul {
        list-style: none;
        padding: 0;
        margin: 0;
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }

    li {
        background: var(--color-bg);
        padding: 0.75rem;
        border-radius: 6px;
        font-size: 0.95rem;
        color: var(--color-text-secondary);
        border: 1px solid var(--color-border);
    }

    .empty {
        color: var(--color-text-muted);
        font-style: italic;
    }

    .error-banner {
        margin-bottom: 1.5rem;
        padding: 1rem;
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid var(--color-error);
        border-radius: 6px;
        color: var(--color-error);
    }

    .actions {
        display: flex;
        justify-content: flex-end;
    }

    .btn-primary {
        background: var(--color-primary);
        color: white;
        border: none;
        padding: 1rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
    }

    .btn-primary:hover:not(:disabled) {
        filter: brightness(1.1);
        transform: translateY(-1px);
    }

    .btn-primary:disabled {
        opacity: 0.7;
        cursor: not-allowed;
    }
</style>
