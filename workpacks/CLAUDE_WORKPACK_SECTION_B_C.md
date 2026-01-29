# Claude Workpack: Section B + Section C (Parallelizable)

Repo: `/Users/admin/git/composable-crew`

Goal: Fix the “flow freezes at Gap Analysis Review” bug by correcting frontend SSE lifecycle + HITL resilience, and prove it with automated tests (plus an opt-in real-input smoke E2E).

Confirmed root cause (do not re-litigate):
- Backend emits an SSE `event: complete` even when the workflow is *paused* in review states like `gap_analysis_review`.
- Frontend closes the `EventSource` on `complete`, so the UI stops receiving progress updates (“freeze”).
- User then clicks “Approve & Continue” again; backend rejects with 400 because the job already advanced (e.g. to `interrogation`).

Non-negotiables:
- Do NOT print or log JD/resume contents (console/devtools/test output).
- Do NOT commit any real resume/JD files or generated copies.
- Any real-input test MUST be opt-in (skipped unless env vars are set).

---

## Section B (Frontend) — Fix SSE lifecycle + HITL resilience + PII-safe

Files (Section B):
- `web/frontend/src/components/JobProgress.svelte` (SSE lifecycle fix)
- `web/frontend/src/components/JobPage.svelte` (HITL “Approve” callback + remove console logging)
- `web/frontend/src/lib/api/hitl.ts` (type/response-shape fix)

### B1) `JobProgress.svelte`: Only close SSE on terminal states

Problem:
- Current code closes EventSource on `"complete"` regardless of job state.

Required behavior:
- Treat `"complete"` as terminal ONLY when `state === "completed" || state === "failed"`.
- If `"complete"` arrives with a non-terminal state (esp. `gap_analysis_review`, `interrogation_review`):
  - do NOT close the EventSource
  - do NOT force `progress = 100`
  - keep listening (defensive; backend should be fixed, but UI must be resilient)

Implementation sketch (apply to the `"complete"` listener):
```ts
eventSource.addEventListener("complete", (e) => {
  const data: SSECompleteEvent = JSON.parse((e as MessageEvent).data);
  const nextState = data.state as JobState;

  state = nextState;

  const terminal = nextState === "completed" || nextState === "failed";
  if (!terminal) {
    // Defensive: backend shouldn’t send complete for pause states; keep SSE alive.
    return;
  }

  progress = 100;
  if (data.agent_models) agent_models = data.agent_models;

  if (nextState === "failed" && data.error_message) {
    error = data.error_message;
  }

  eventSource.close();
  onComplete?.(data);
});
```

### B2) `JobPage.svelte`: Make “Approve & Continue” resilient even if SSE is flaky

Problem:
- `onApprove` is currently effectively a no-op (“SSE will update state”), which fails if SSE is closed/dropped.

Required behavior:
- After “Approve”, do a one-shot `GET /api/jobs/${jobId}` refresh and update local state immediately.
- No console logging.

Implementation detail:
- Add a `refreshJob()` helper that fetches `/api/jobs/${jobId}` and updates `job` and/or `currentState/intermediateResults`.
- Call it in:
  - `GapAnalysisReview onApprove`
  - `InterviewReview onSubmit` (same resilience principle)

Optional (recommended):
- Use short, bounded polling (condition-based waiting) to refresh a few times until state changes off the review state, rather than sleeping blindly.

### B3) `JobPage.svelte`: Remove console logging of intermediate results (PII risk)

Remove any `$effect` / handlers that print `currentState` or `intermediateResults` to console.

### B4) `hitl.ts`: Fix response typing mismatch

Problem:
- `approveGapAnalysis()` / `submitInterviewAnswers()` are typed as returning `Promise<Job>`, but backend returns `{ job_id, status, message }`.

Fix:
- Add:
```ts
export type HitlActionResponse = { job_id: string; status: string; message: string };
```
- Change both functions to return `Promise<HitlActionResponse>` (or explicitly ignore returned body, but don’t lie in typings).

---

## Section C (Tests + Verification)

Files (Section C):
- Add: `tests/unit/backend/test_sse_pause_semantics.py` (backend regression: pause states do not emit SSE `complete`)
- Add: `web/frontend/tests/e2e/hitl-gap-approve-real.spec.ts` (opt-in Playwright E2E: review → approve → resumes)
- Optional: `web/frontend/tests/helpers/real-input.ts` (env var parsing + safe file existence checks; no content logging)

### C1) Backend regression test: pause must not emit SSE `complete`

Goal:
- When workflow ends in a review/pause state (e.g. `gap_analysis_review`), SSE stream must NOT emit `event: complete`.

Approach (no real LLM):
- Patch the workflow execution to return a paused `WorkflowResult` (e.g. `WorkflowState.GAP_ANALYSIS_REVIEW`) and ensure the stream emits a final `progress` but not `complete`.
- Read a bounded portion of the SSE response and assert `event: complete` is absent.

### C2) Playwright E2E: real-input HITL approve continues (opt-in only)

Add: `web/frontend/tests/e2e/hitl-gap-approve-real.spec.ts`

Rules:
- Skip unless env vars are set:
  - `REAL_RESUME_PATH` (path to a local resume file)
  - `REAL_JD_PATH` (path to a local JD markdown file)
- Do not log file contents in test output.
- Test flow:
  1) open `/`
  2) upload JD + resume using `setInputFiles`
  3) submit
  4) wait for “Review Gap Analysis”
  5) click “Approve & Continue”
  6) assert UI proceeds (review disappears and next stage appears), and no 400 error banner appears

### C3) Verification runs

Frontend:
- From `web/frontend/`: run the full suite and ensure green.

Backend:
- Run unit tests including the new regression.

Evidence to provide back:
- The exact commands run and their outputs (pass/fail summary).
- A brief note confirming no added console logging of intermediate results.

---

## Parallelization Map (3+ agents)

These can be executed in parallel with minimal merge conflict risk:
- Agent 1: B1 (`web/frontend/src/components/JobProgress.svelte`)
- Agent 2: B2+B3 (`web/frontend/src/components/JobPage.svelte`)
- Agent 3: B4 (`web/frontend/src/lib/api/hitl.ts`)
- Agent 4: C2 (Playwright E2E real-input spec)
- Agent 5: C1 (backend SSE regression test)

