# Hydra Frontend Product Understanding

## 1. User Journey Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          HYDRA USER JOURNEY                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  NEW USER                                                                    │
│  ────────                                                                    │
│  1. Land on upload page (/)                                                  │
│  2. Read "What Hydra Does" features                                          │
│  3. Upload job description (JD) file                                         │
│  4. Upload resume file                                                       │
│  5. Optionally add source documents                                          │
│  6. Click "Generate Application"                                             │
│                                                                              │
│  PROCESSING                                                                  │
│  ──────────                                                                  │
│  7. See loading overlay (Read → Upload → Start → Go)                         │
│  8. Redirect to /jobs/{id}                                                   │
│  9. Watch real-time progress via SSE                                         │
│     - Stage indicators (7 stages + complete)                                 │
│     - Agent card with role & fun facts                                       │
│     - Timer showing elapsed time                                             │
│     - Execution log (collapsible)                                            │
│                                                                              │
│  [MISSING] HUMAN-IN-THE-LOOP                                                 │
│  10. Review gap analysis → Approve/Request changes                           │
│  11. Answer interview questions for skill gaps                               │
│                                                                              │
│  SUCCESS PATH                                                                │
│  ────────────                                                                │
│  12. Job completes → Results appear                                          │
│  13. View TLDR hero with verdict (APPROVED/REJECTED/MIXED)                   │
│  14. Navigate tabs: Summary | Resume | Cover Letter | Audit | Debug          │
│  15. Copy resume/cover letter to clipboard                                   │
│  16. Review action items                                                     │
│                                                                              │
│  FAILURE PATH                                                                │
│  ────────────                                                                │
│  A. Connection lost → "Connection lost. Refresh to reconnect."               │
│  B. Backend error → Error banner shown                                       │
│  C. Job failed → Failed state with error message                             │
│                                                                              │
│  POWER USER                                                                  │
│  ──────────                                                                  │
│  - View intermediate results in Debug tab                                    │
│  - See which LLM models powered each agent                                   │
│  - Check audit details for verification                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2. Screen Inventory

| Screen | Path | Components | States |
|--------|------|------------|--------|
| Upload | `/` | FileUpload ×3, Submit button, Features grid | Default, Dragging, Files selected, Loading overlay, Error |
| Job Progress | `/jobs/[id]` | JobProgress, ResultsViewer | Loading, Connected, Each stage (7), Complete, Failed, Error |
| Results | (embedded) | ResultsViewer, MarkdownViewer | 5 tabs: Summary, Resume, Cover Letter, Audit, Debug |

## 3. Data Flow Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DATA FLOW ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  UPLOAD FLOW                                                                 │
│  ───────────                                                                 │
│  Browser                          Astro API                    Backend       │
│  ┌─────────┐                     ┌──────────┐                ┌──────────┐    │
│  │ FormData│ ──file.text()──────>│ POST     │ ────JSON────>  │ Litestar │    │
│  │ (files) │                     │ /api/jobs│                │ :8000    │    │
│  └─────────┘                     └──────────┘                └──────────┘    │
│                                       │                           │          │
│                                       │ job_id                    │ SQLite   │
│                                       ▼                           │ persist  │
│                               window.location                     ▼          │
│                               /jobs/{job_id}              job_queue.create() │
│                                                                              │
│  SSE STREAMING                                                               │
│  ─────────────                                                               │
│  Browser                          Backend                                    │
│  ┌─────────────┐                ┌──────────────────────────────┐             │
│  │ EventSource │ <─────SSE───── │ GET /api/jobs/{id}/stream    │             │
│  │             │                │                              │             │
│  │ Events:     │                │ Events emitted:              │             │
│  │ - connected │                │ - connected (initial state)  │             │
│  │ - progress  │                │ - progress (state changes)   │             │
│  │ - log       │                │ - log (execution logs)       │             │
│  │ - complete  │                │ - stage_complete             │             │
│  │ - error     │                │ - complete / error           │             │
│  └─────────────┘                └──────────────────────────────┘             │
│                                                                              │
│  STATE MANAGEMENT (Svelte 5 Runes)                                           │
│  ─────────────────────────────────                                           │
│  ┌──────────────────────────────────────────────────────────────────────┐    │
│  │ JobPage.svelte                                                       │    │
│  │ ┌────────────────────────────────────────────────────────────────┐   │    │
│  │ │ $state: isComplete, finalDocuments, auditReport, executiveBrief│   │    │
│  │ │ $state: intermediateResults, auditFailed, auditError, agentModels │ │    │
│  │ └────────────────────────────────────────────────────────────────┘   │    │
│  │                              │                                       │    │
│  │                              ▼                                       │    │
│  │ ┌──────────────────────────────────────────────────────────────┐    │    │
│  │ │ JobProgress.svelte                                           │    │    │
│  │ │ $state: state, progress, logs, error, isConnected, elapsed   │    │    │
│  │ │ $effect: SSE connection, timer                               │    │    │
│  │ └──────────────────────────────────────────────────────────────┘    │    │
│  │                              │                                       │    │
│  │                              ▼                                       │    │
│  │ ┌──────────────────────────────────────────────────────────────┐    │    │
│  │ │ ResultsViewer.svelte                                         │    │    │
│  │ │ $state: activeTab                                            │    │    │
│  │ │ $derived: hasDocuments, auditStatus, verdict, actionItems    │    │    │
│  │ └──────────────────────────────────────────────────────────────┘    │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 4. Missing Human-in-the-Loop Endpoints

Backend has these endpoints but NO frontend UI:

| Endpoint | Purpose | Required UI |
|----------|---------|-------------|
| `POST /api/jobs/{id}/approve_gap_analysis` | Approve/reject gap analysis | Review component with approve/request changes buttons |
| `POST /api/jobs/{id}/submit_interview_answers` | Submit STAR+ answers | Interview form component with questions |

Backend states that need UI:
- `GAP_ANALYSIS_REVIEW` - Requires gap analysis approval UI
- `INTERROGATION_REVIEW` - Requires interview answers UI

## 5. Current UX Pain Points (Ranked)

### Critical (Blocking Features)
1. **No HITL UI** - Cannot review gap analysis or answer interview questions
2. **No reconnection handling** - SSE drops silently, user must manually refresh

### High (Friction)
3. **No retry mechanism** - Failed jobs cannot be retried
4. **Generic error messages** - No actionable guidance on failures
5. **No cancel functionality** - Cannot cancel a running job

### Medium (Polish)
6. **No skeleton loaders** - Content appears suddenly
7. **No empty states** - Missing "no jobs" or "no documents" states
8. **Timer doesn't persist** - Refresh loses elapsed time
9. **No job history** - Cannot view past jobs

### Low (Nice to Have)
10. **No keyboard shortcuts** - Tab/arrow navigation could be improved
11. **No dark mode toggle** - Uses system preference only
12. **No download option** - Must copy/paste documents

## 6. Test Coverage Gaps

| Flow | Happy Path | Failure Path | Recovery |
|------|------------|--------------|----------|
| Upload files | ✅ | ⚠️ Partial | ❌ |
| Create job | ✅ | ⚠️ Partial | ❌ |
| SSE streaming | ✅ | ❌ | ❌ |
| Job completion | ⚠️ (flaky) | ❌ | ❌ |
| Gap analysis review | ❌ N/A | ❌ | ❌ |
| Interview answers | ❌ N/A | ❌ | ❌ |
| Tab navigation | ❌ | ❌ | ❌ |
| Copy to clipboard | ❌ | ❌ | ❌ |
| Connection loss | ❌ | ❌ | ❌ |

## 7. Performance Observations

- **Bundle**: Single Astro build with Svelte components hydrated client-side
- **Code splitting**: Only by route (Astro default)
- **Caching**: No explicit caching strategy
- **Large lists**: No virtualization (execution log could grow)
- **Memory**: EventSource not always cleaned up on navigation

## 8. Proposed Architecture

```
web/frontend/src/
├── components/          # Shared UI primitives
│   ├── ui/             # Design system (Button, Input, Card, etc.)
│   ├── feedback/       # Toast, Modal, ErrorBoundary
│   └── layout/         # Header, Footer, Container
├── features/           # Feature slices
│   ├── upload/         # FileUpload, UploadForm
│   ├── job/            # JobProgress, JobHeader, JobControls
│   ├── results/        # ResultsViewer, ResultsTabs
│   └── hitl/           # GapAnalysisReview, InterviewForm
├── lib/
│   ├── api/            # API clients, typed fetchers
│   ├── stores/         # Shared Svelte stores
│   ├── hooks/          # Reusable $effect patterns
│   ├── utils/          # Pure helpers
│   └── types.ts        # Type definitions
├── pages/              # Astro pages (routes)
└── tests/
    ├── e2e/            # Playwright E2E tests
    ├── integration/    # API integration tests
    └── component/      # Svelte component tests
```
