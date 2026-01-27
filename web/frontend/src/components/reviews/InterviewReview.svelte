<script lang="ts">
    /**
     * InterviewReview.svelte
     * HITL interface for answering interview questions.
     */
    import { submitInterviewAnswers } from "../../lib/api/hitl";
    import type { InterrogationResult, InterviewAnswer } from "../../lib/types";

    interface Props {
        jobId: string;
        interviewPrep?: InterrogationResult;
        onSubmit: () => void;
    }

    let { jobId, interviewPrep, onSubmit }: Props = $props();

    // Extract question objects
    const questionObjects = interviewPrep?.questions || [];

    // State for answers
    let answers = $state<string[]>(new Array(questionObjects.length).fill(""));
    let isSubmitting = $state(false);
    let error = $state<string | null>(null);

    // Derived check if all questions have answers
    let allAnswered = $derived(answers.every((a) => a.trim().length > 0));

    async function handleSubmit() {
        isSubmitting = true;
        error = null;

        // Format answers for API
        const formattedAnswers: InterviewAnswer[] = questionObjects.map(
            (q, i) => ({
                question: q.question, // Extract string from object
                answer: answers[i],
                question_id: q.id,
            }),
        );

        try {
            await submitInterviewAnswers(jobId, formattedAnswers);
            onSubmit();
        } catch (e) {
            error = e instanceof Error ? e.message : "Failed to submit answers";
        } finally {
            isSubmitting = false;
        }
    }
</script>

<div class="review-card card">
    <div class="header">
        <div class="icon">💬</div>
        <div class="title">
            <h2>Interview Preparation</h2>
            <p>
                The agents have generated STAR-format interview questions based
                on your profile and the job. Please provide your answers or
                talking points for each question.
            </p>
        </div>
    </div>

    {#if questionObjects.length === 0}
        <div class="empty-state">
            <p>No questions generated. Please check the logs.</p>
        </div>
    {:else}
        <div class="questions-list">
            {#each questionObjects as q, i}
                <div class="question-item">
                    <label for={`q-${i}`}>
                        <span class="q-number">Q{i + 1}</span>
                        {q.question}
                    </label>
                    <textarea
                        id={`q-${i}`}
                        bind:value={answers[i]}
                        placeholder="Type your answer, key points, or a STAR story here..."
                        rows="4"
                    ></textarea>
                </div>
            {/each}
        </div>
    {/if}

    {#if error}
        <div class="error-banner">{error}</div>
    {/if}

    <div class="actions">
        <button
            class="btn-primary"
            onclick={handleSubmit}
            disabled={isSubmitting || !allAnswered}
        >
            {#if isSubmitting}
                Submitting...
            {:else}
                Submit Answers & Continue
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

    .questions-list {
        display: flex;
        flex-direction: column;
        gap: 2rem;
        margin-bottom: 2rem;
    }

    .question-item {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }

    label {
        font-weight: 500;
        font-size: 1.05rem;
        color: var(--color-text);
        display: flex;
        gap: 0.75rem;
        line-height: 1.4;
    }

    .q-number {
        color: var(--color-primary);
        font-weight: 700;
        flex-shrink: 0;
    }

    textarea {
        width: 100%;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid var(--color-border);
        background: var(--color-bg);
        color: var(--color-text);
        font-family: inherit;
        font-size: 1rem;
        resize: vertical;
        transition:
            border-color 0.2s,
            box-shadow 0.2s;
    }

    textarea:focus {
        outline: none;
        border-color: var(--color-primary);
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
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
        opacity: 0.5;
        cursor: not-allowed;
        background: var(--color-text-muted);
    }
</style>
