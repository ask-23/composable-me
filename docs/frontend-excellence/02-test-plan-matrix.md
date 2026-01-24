# Hydra Frontend Test Plan Matrix

## Test Coverage Overview

| Category | Happy Path | Failure Paths | Recovery | Edge Cases | Total |
|----------|------------|---------------|----------|------------|-------|
| Upload | 5 | 6 | 3 | 4 | 18 |
| Job Progress | 8 | 5 | 4 | 3 | 20 |
| SSE Connection | 3 | 6 | 5 | 3 | 17 |
| Results Viewer | 6 | 3 | 2 | 4 | 15 |
| HITL Flows | 4 | 4 | 2 | 2 | 12 |
| Accessibility | 8 | 0 | 0 | 2 | 10 |
| Error Recovery | 0 | 8 | 8 | 2 | 18 |
| **Total** | **34** | **32** | **24** | **20** | **110** |

## Detailed Test Cases

### 1. Upload Flow Tests

#### Happy Path
| ID | Test Case | Steps | Expected |
|----|-----------|-------|----------|
| UP-01 | Page loads correctly | Navigate to / | Title, form, features visible |
| UP-02 | Upload JD via click | Click dropzone, select file | File name shown, size displayed |
| UP-03 | Upload JD via drag-drop | Drag file to dropzone | File accepted, name shown |
| UP-04 | Upload resume | Upload .md file | File shown in form |
| UP-05 | Submit valid form | Upload JD + resume, submit | Loading overlay, redirect to /jobs/{id} |

#### Failure Paths
| ID | Test Case | Steps | Expected |
|----|-----------|-------|----------|
| UP-F01 | Submit without files | Click submit with empty form | Validation error shown |
| UP-F02 | Upload invalid file type | Upload .exe file | Rejection message |
| UP-F03 | Network failure on submit | Disable network, submit | Error: "Check your connection" |
| UP-F04 | Server error on submit | Mock 500 response | Error: "Something went wrong" |
| UP-F05 | Validation error from API | Mock 400 response | Error message from API |
| UP-F06 | Large file handling | Upload 10MB file | Size warning or acceptance |

#### Recovery
| ID | Test Case | Steps | Expected |
|----|-----------|-------|----------|
| UP-R01 | Retry after network failure | Submit, fail, retry | Retry succeeds |
| UP-R02 | Clear error and edit | See error, edit files | Error clears |
| UP-R03 | Remove and re-add file | Remove file, add new | New file shown |

### 2. Job Progress Tests

#### Happy Path
| ID | Test Case | Steps | Expected |
|----|-----------|-------|----------|
| JP-01 | Page loads with job | Navigate to /jobs/{id} | Job header, progress shown |
| JP-02 | Progress bar updates | Watch SSE events | Bar animates to new % |
| JP-03 | Stage indicators update | Progress through stages | Stages light up sequentially |
| JP-04 | Agent card updates | Stage changes | New agent info shown |
| JP-05 | Timer increments | Wait on page | Timer shows elapsed time |
| JP-06 | Execution log populates | Log events arrive | Entries appear in log |
| JP-07 | Job completes successfully | Wait for completion | Success state, results shown |
| JP-08 | Model badges shown | Agents use models | Model names displayed |

#### Failure Paths
| ID | Test Case | Steps | Expected |
|----|-----------|-------|----------|
| JP-F01 | Invalid job ID | Navigate to /jobs/invalid | "Job not found" error |
| JP-F02 | Job fails at stage | Job encounters error | Failed state, error message |
| JP-F03 | SSE connection drops | Simulate disconnect | "Connection lost" message |
| JP-F04 | SSE parse error | Send invalid JSON | Silent recovery, continue |
| JP-F05 | Job timeout | Job takes too long | Appropriate timeout handling |

### 3. SSE Connection Tests

#### Happy Path
| ID | Test Case | Steps | Expected |
|----|-----------|-------|----------|
| SSE-01 | Initial connection | Load job page | "Connected" state |
| SSE-02 | Receive progress events | Job progresses | State updates |
| SSE-03 | Clean close on complete | Job completes | Connection closed gracefully |

#### Failure Paths
| ID | Test Case | Steps | Expected |
|----|-----------|-------|----------|
| SSE-F01 | Connection refused | Backend down | Error state shown |
| SSE-F02 | Connection reset | Kill backend mid-job | Reconnection attempt |
| SSE-F03 | Stale connection | No events for 60s | Keepalive or reconnect |
| SSE-F04 | Multiple reconnects | Repeated failures | Shows reconnection count |
| SSE-F05 | Max reconnects exceeded | 5+ failures | "Please refresh" message |
| SSE-F06 | Reconnect during event | Drop during progress | Resume from last state |

#### Recovery
| ID | Test Case | Steps | Expected |
|----|-----------|-------|----------|
| SSE-R01 | Auto-reconnect | Connection drops | Reconnects automatically |
| SSE-R02 | Manual reconnect | Click reconnect button | Reconnects |
| SSE-R03 | State preserved on reconnect | Reconnect after drop | State matches server |
| SSE-R04 | Page refresh recovery | Refresh page | Resumes from current state |
| SSE-R05 | Navigate away and back | Leave and return | Reconnects correctly |

### 4. Results Viewer Tests

#### Happy Path
| ID | Test Case | Steps | Expected |
|----|-----------|-------|----------|
| RV-01 | TLDR hero shows verdict | Job completes | Verdict badge visible |
| RV-02 | Summary tab content | View summary | Executive summary, action items |
| RV-03 | Resume tab content | Switch to Resume tab | Resume markdown rendered |
| RV-04 | Cover letter tab | Switch to Cover Letter | Content rendered |
| RV-05 | Audit tab content | Switch to Audit | Status, details shown |
| RV-06 | Debug tab content | Switch to Debug | Intermediate results |

#### Failure Paths
| ID | Test Case | Steps | Expected |
|----|-----------|-------|----------|
| RV-F01 | No documents generated | Job failed early | Empty state message |
| RV-F02 | Partial results | Some stages completed | Show what's available |
| RV-F03 | Copy fails | Clipboard blocked | Fallback message |

### 5. HITL Flow Tests

#### Gap Analysis Review
| ID | Test Case | Steps | Expected |
|----|-----------|-------|----------|
| HITL-01 | Review state shown | Job reaches GAP_ANALYSIS_REVIEW | Review component appears |
| HITL-02 | Approve and continue | Click Approve | Job resumes |
| HITL-03 | Request revision | Click Revise, add feedback | Feedback submitted |
| HITL-04 | Validation on empty | Submit without selection | Validation error |

#### Interview Questions
| ID | Test Case | Steps | Expected |
|----|-----------|-------|----------|
| HITL-05 | Questions displayed | Job reaches INTERROGATION_REVIEW | Questions shown |
| HITL-06 | Answer all questions | Fill all answers | Submit enabled |
| HITL-07 | Submit answers | Complete and submit | Job resumes |
| HITL-08 | Partial answers | Leave some empty | Validation error |

### 6. Accessibility Tests

| ID | Test Case | Expected |
|----|-----------|----------|
| A11Y-01 | Keyboard navigation - upload | Tab through all interactive elements |
| A11Y-02 | Keyboard navigation - progress | Tab through stages, buttons |
| A11Y-03 | Keyboard navigation - results | Tab through tabs, copy buttons |
| A11Y-04 | Screen reader - upload form | Labels announced correctly |
| A11Y-05 | Screen reader - progress | State changes announced |
| A11Y-06 | Screen reader - errors | Errors announced via aria-live |
| A11Y-07 | Focus management - modal | Focus trapped in modal |
| A11Y-08 | Focus management - error | Focus moves to error message |

### 7. Error Recovery Tests

| ID | Test Case | Steps | Expected |
|----|-----------|-------|----------|
| ER-01 | Retry failed upload | Upload fails, click Retry | Retry succeeds |
| ER-02 | Reconnect SSE | Connection lost, click Reconnect | Reconnects |
| ER-03 | Navigate after error | See error, click Back | Returns home |
| ER-04 | Refresh preserves state | On job page, refresh | Same job, current state |
| ER-05 | Clear error manually | See error, click Dismiss | Error clears |
| ER-06 | Error boundary recovery | Component crashes, click Try Again | Component re-renders |
| ER-07 | Offline handling | Go offline | Offline notification |
| ER-08 | Online recovery | Come back online | Operations resume |

## Test Environment Requirements

### Prerequisites
- Node.js 18+
- Playwright installed
- Backend running (or mocked)
- Test fixtures available

### Mock Requirements
- Mock SSE server for connection tests
- Mock API responses for failure tests
- Network interception for offline tests

### CI Configuration
```yaml
e2e-tests:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
    - run: npm ci
    - run: npx playwright install --with-deps
    - run: npm run test:e2e
  timeout-minutes: 30
```

## Test Data Fixtures

```typescript
// tests/fixtures/mock-data.ts
export const mockJob = {
  job_id: 'test-job-123',
  state: 'completed',
  success: true,
  progress_percent: 100,
  // ... full job data
}

export const mockGapAnalysis = {
  matches: [{ skill: 'Python', evidence: '...' }],
  gaps: [{ skill: 'Kubernetes', importance: 'high' }],
  adjacent_skills: [{ skill: 'Docker', relevance: '...' }],
}

export const mockSSEEvents = [
  { event: 'connected', data: { state: 'initialized', progress: 0 } },
  { event: 'progress', data: { state: 'gap_analysis', progress: 15 } },
  // ... full event sequence
]
```
