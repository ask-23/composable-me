# Hydra State Graph
<!-- LLM-optimized memory document for session continuity -->
<!-- Last updated: 2026-01-26T17:50:00-06:00 -->

## SYSTEM_IDENTITY

```yaml
project: composable-crew (Hydra)
type: multi-agent AI pipeline for job application optimization
location: /Users/admin/git/composable-crew
primary_interface: web application (Astro 5 + Svelte 5 frontend, Litestar backend)
secondary_interface: CLI (runtime/crewai/cli.py)
```

---

## SESSION_LOG

### 2026-01-26T17:00-17:50 | Recovery: Back to Green

**OBJECTIVE**: Fix regressions from JSON ingestion feature, restore E2E test suite

**COMPLETED_MILESTONES**:

1. `[2026-01-26T17:05]` **EXECUTIVE_SYNTHESIS_STATE**
   - Added `EXECUTIVE_SYNTHESIS` to `JobState` enum (backend)
   - Added state mapping in `workflow_runner.py`
   - Added progress calculation (95%) in `job_queue.py`

2. `[2026-01-26T17:10]` **UI_STAGES_SEPARATION**
   - Created `UI_STAGES` (7 stages) for progress bar display
   - Kept `STAGES` (11 states) for state machine
   - Updated `JobProgress.svelte` to map internal states to display states

3. `[2026-01-26T17:20]` **SSR_MOCK_ROUTING_FIX**
   - Added `?mock` query param to skip SSR in `[id].astro`
   - Enables Playwright mocks to intercept client-side requests
   - Fixed all job-progress and results E2E tests

4. `[2026-01-26T17:35]` **SVELTE_5_EVENT_HANDLING**
   - Fixed file upload tests using `__change` internal handlers
   - Created helpers for Svelte 5 event invocation pattern
   - Fixed CSV role picker modal tests

5. `[2026-01-26T17:45]` **INITIAL_PROGRESS_FIX**
   - Added `initialProgress` prop to `JobProgress.svelte`
   - Completed jobs now show correct progress on load

**FINAL_RESULT**: 93 passed, 2 skipped, 0 failed

---

### 2026-01-26T14:02-15:15 | JSON Input + pCloud Sync Implementation

**OBJECTIVE**: Enable Hydra to consume JSON job feed files from pCloud public folder

**COMPLETED_MILESTONES**:

1. `[2026-01-26T14:04]` **JSON_INPUT_SUPPORT**
   - Created `web/frontend/src/lib/json-utils.ts`
   - Modified `web/frontend/src/components/UploadForm.svelte`
   - Frontend now accepts `.json` files alongside `.csv` for job descriptions

2. `[2026-01-26T15:10]` **PCLOUD_SYNC_UTILITY**
   - Created `scripts/feed-sync/hydra-feed-sync.py`
   - Standalone utility to sync from pCloud public folder

3. `[2026-01-26T15:40]` **UI_REGRESSION_FIX**
   - Created `GapAnalysisReview.svelte` and `InterviewReview.svelte`
   - Updated `JobPage.svelte` for intermediate review states

---

## CURRENT_STATE

### Workflow Pipeline (7 Agents)

```
1. GAP_ANALYZER → Requirements mapping
   └─ PAUSE: GAP_ANALYSIS_REVIEW (HITL approval)
2. INTERROGATOR_PREPPER → STAR+ interview questions
   └─ PAUSE: INTERROGATION_REVIEW (HITL answers)
3. DIFFERENTIATOR → Unique value propositions
4. TAILORING_AGENT → Resume/cover letter customization
5. ATS_OPTIMIZER → Keyword optimization
6. AUDITOR_SUITE → Truth/Tone/ATS/Compliance audits
7. EXECUTIVE_SYNTHESIZER → Strategic brief generation  ← NEW
```

### State Machine (11 States)

```yaml
states:
  - initialized       # 0%
  - gap_analysis      # 15%
  - gap_analysis_review  # 18% (HITL pause)
  - interrogation     # 30%
  - interrogation_review # 35% (HITL pause)
  - differentiation   # 45%
  - tailoring         # 60%
  - ats_optimization  # 75%
  - auditing          # 90%
  - executive_synthesis  # 95%  ← NEW
  - completed         # 100%
  - failed            # 100%
```

### UI Display States (7 Stages)

```yaml
ui_stages:
  - initialized       # "Starting"
  - gap_analysis      # "Gap Analysis"
  - interrogation     # "Interview Prep"
  - tailoring         # "Tailoring"
  - ats_optimization  # "ATS Optimization"
  - auditing          # "Auditing"
  - completed         # "Complete"
```

---

## KEY_PATTERNS

### Svelte 5 E2E Testing Pattern

```typescript
// For file inputs and form handlers in Svelte 5:
const svelteHandler = (el as any).__change;
if (typeof svelteHandler === 'function') {
    const event = new Event('change', { bubbles: true });
    Object.defineProperty(event, 'target', { value: el, writable: false });
    svelteHandler(event);
}
```

### SSR Mock Routing Pattern

```typescript
// In Astro page - detect ?mock to skip SSR
const skipSSR = Astro.url.searchParams.has('mock');
const job = skipSSR ? null : await fetchJob(id);

// In tests - navigate with ?mock
await page.goto(`/jobs/${jobId}?mock`);
```

---

## FILE_INVENTORY

### Modified Files (2026-01-26 Recovery)

| File | Change |
|------|--------|
| `web/backend/models.py` | Added EXECUTIVE_SYNTHESIS state |
| `web/backend/services/workflow_runner.py` | Added state mapping |
| `web/backend/services/job_queue.py` | Added progress for new states |
| `web/frontend/src/lib/types.ts` | Added UI_STAGES, executive_synthesis |
| `web/frontend/src/components/JobProgress.svelte` | Uses UI_STAGES, initialProgress prop |
| `web/frontend/src/components/JobPage.svelte` | Passes initialProgress |
| `web/frontend/src/components/UploadForm.svelte` | Added .csv-hint element |
| `web/frontend/src/pages/jobs/[id].astro` | Added ?mock SSR bypass |
| `web/frontend/tests/helpers/test-helpers.ts` | Svelte 5 event helpers |
| `web/frontend/tests/fixtures/mock-responses.ts` | Updated state arrays |

---

## MEMORY_ANCHORS

```
HYDRA = multi-agent job application optimizer (7 agents)
HITL = Human-in-the-Loop (2 pause points: gap_analysis_review, interrogation_review)
EXECUTIVE_SYNTHESIS = Final agent, creates strategic brief (95% progress)
UI_STAGES = 7 stages for progress bar (excludes review states)
STAGES = 11 states for state machine (full workflow)
SVELTE_5_EVENTS = Use __change/__submit internal handlers in tests
SSR_MOCK_BYPASS = ?mock query param skips SSR for Playwright tests
E2E_STATUS = 93 passed, 2 skipped, 0 failed
```
