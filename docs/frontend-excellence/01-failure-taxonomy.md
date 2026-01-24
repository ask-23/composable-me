# Hydra Frontend Failure Taxonomy

## Overview

This document enumerates all failure scenarios and defines the UX recovery patterns for each.

## Failure Categories

### 1. Network Failures

| Failure | Detection | User Message | Recovery Action |
|---------|-----------|--------------|-----------------|
| No internet connection | `navigator.onLine === false` | "You're offline. Check your connection." | Auto-retry when online |
| DNS resolution failed | Fetch error with no response | "Unable to reach server. Check your network." | Manual retry button |
| Connection timeout | Fetch timeout (30s) | "Request timed out. The server may be busy." | Manual retry with exponential backoff |
| Connection reset | Fetch error mid-request | "Connection interrupted. Retrying..." | Auto-retry (max 3 attempts) |
| SSL/TLS error | Fetch error with security message | "Secure connection failed." | Manual retry, clear instructions |

### 2. API Errors

| HTTP Status | Meaning | User Message | Recovery Action |
|-------------|---------|--------------|-----------------|
| 400 Bad Request | Invalid input | Show validation errors | Fix input and resubmit |
| 401 Unauthorized | Auth required | "Session expired. Please refresh." | Refresh page / re-auth |
| 403 Forbidden | Access denied | "You don't have access to this resource." | Contact support |
| 404 Not Found | Job doesn't exist | "Job not found. It may have expired." | Go back home |
| 409 Conflict | State conflict | "This action is no longer valid." | Refresh and retry |
| 422 Unprocessable | Business logic error | Show specific error from API | Fix and resubmit |
| 429 Too Many Requests | Rate limited | "Too many requests. Please wait." | Auto-retry after delay |
| 500 Internal Server Error | Server bug | "Something went wrong on our end." | Manual retry |
| 502 Bad Gateway | Upstream failure | "Service temporarily unavailable." | Auto-retry with backoff |
| 503 Service Unavailable | Overloaded | "Server is busy. Please try again later." | Auto-retry with backoff |
| 504 Gateway Timeout | Upstream timeout | "Request timed out." | Manual retry |

### 3. SSE/Streaming Failures

| Failure | Detection | User Message | Recovery Action |
|---------|-----------|--------------|-----------------|
| Connection lost | `EventSource.onerror` | "Connection lost. Reconnecting..." | Auto-reconnect (exponential backoff) |
| Stream timeout | No events for 60s | "Connection stale. Refreshing..." | Auto-reconnect |
| Invalid event data | JSON parse error | (Silent) Log error | Continue listening |
| Max reconnects exceeded | Counter > 5 | "Unable to connect. Please refresh." | Manual page refresh |
| Server closed stream | Event: close | (Expected) No message | Check if job complete |

### 4. Job Processing Failures

| Failure | State | User Message | Recovery Action |
|---------|-------|--------------|-----------------|
| LLM API error | `failed` | "AI service error: {details}" | Retry job |
| LLM rate limited | `failed` | "AI service busy. Try again in a moment." | Retry job |
| Invalid input documents | `failed` | "Unable to process your documents: {reason}" | Fix input, new job |
| Audit failed permanently | `completed` (audit_failed=true) | "Documents ready but didn't pass final audit." | Review audit, manual fix |
| Partial completion | `failed` | "Processing stopped at {stage}." | Check intermediate results |

### 5. Client-Side Failures

| Failure | Detection | User Message | Recovery Action |
|---------|-----------|--------------|-----------------|
| File read error | FileReader.onerror | "Unable to read file: {name}" | Try different file |
| File too large | file.size > limit | "File too large. Maximum size is {limit}MB." | Use smaller file |
| Invalid file type | Extension check | "Invalid file type. Accepted: .md, .txt" | Use correct format |
| Clipboard write failed | navigator.clipboard error | "Unable to copy. Try selecting text manually." | Manual selection |
| LocalStorage full | QuotaExceededError | (Silent) Degrade gracefully | Continue without storage |
| Browser not supported | Feature detection | "Your browser may not support all features." | Suggest modern browser |

### 6. Validation Failures

| Field | Validation | Error Message |
|-------|------------|---------------|
| Job Description | Required, min 50 chars | "Job description is required and must be at least 50 characters." |
| Resume | Required, min 100 chars | "Resume is required and must be at least 100 characters." |
| Interview Answer | Required when shown | "Please answer all questions before continuing." |
| Gap Analysis Feedback | Optional, max 500 chars | "Feedback must be less than 500 characters." |

## Recovery Patterns

### Pattern 1: Auto-Retry with Backoff

```
Attempt 1: Immediate
Attempt 2: Wait 1 second
Attempt 3: Wait 2 seconds
Attempt 4: Wait 4 seconds
Attempt 5: Wait 8 seconds
Give up: Show manual retry option
```

### Pattern 2: Optimistic Update with Rollback

```
1. Update UI immediately (optimistic)
2. Send request to server
3. On success: Confirm UI state
4. On failure: Rollback UI, show error
```

### Pattern 3: Progressive Degradation

```
1. Try primary action
2. On failure: Try fallback action
3. On failure: Show manual alternative
4. Always preserve user's work
```

### Pattern 4: Error Boundary Recovery

```
1. Catch render error
2. Log error with context
3. Show friendly fallback UI
4. Offer "Try Again" to re-render
5. Offer "Go Home" as escape hatch
```

## Error Message Guidelines

### Do

- Be specific about what went wrong
- Explain what the user can do about it
- Use plain language, not technical jargon
- Preserve the user's work when possible
- Provide a clear action (button, link)

### Don't

- Show raw error codes or stack traces
- Blame the user
- Use vague messages like "An error occurred"
- Leave the user stuck with no options
- Auto-dismiss errors before user reads them

## Implementation Checklist

- [ ] All fetch calls wrapped with error handling
- [ ] All SSE connections have reconnection logic
- [ ] All forms have validation with clear errors
- [ ] Error boundary at page level
- [ ] Offline detection and notification
- [ ] Toast notifications for transient errors
- [ ] Persistent error displays for blocking errors
- [ ] Retry buttons on all recoverable errors
- [ ] Error logging with context for debugging
