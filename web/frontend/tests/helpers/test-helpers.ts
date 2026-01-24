/**
 * Shared test utilities for Hydra E2E tests.
 * Provides API mocking, SSE simulation, and common interactions.
 */

import { Page, Route, Request } from '@playwright/test';
import {
    createMockJob,
    mockFinalDocuments,
    mockAuditReportApproved,
    mockExecutiveBrief,
    mockIntermediateResults,
    mockSSEEvents,
    generateHappyPathSSEStream,
    mockAPIErrors,
    SAMPLE_JOB_DESCRIPTION,
    SAMPLE_RESUME,
} from '../fixtures/mock-responses';
import type { Job, JobState } from '../../src/lib/types';

// ----- API Route Mocking -----

export interface MockJobOptions {
    state?: JobState;
    jobId?: string;
    overrides?: Partial<Job>;
}

/**
 * Mock the job creation endpoint to return a specific job ID
 */
export async function mockJobCreation(page: Page, jobId: string = 'mock-job-123'): Promise<void> {
    await page.route('**/api/jobs', async (route: Route) => {
        if (route.request().method() === 'POST') {
            await route.fulfill({
                status: 202,
                contentType: 'application/json',
                body: JSON.stringify({
                    job_id: jobId,
                    status: 'queued',
                    created_at: new Date().toISOString(),
                }),
            });
        } else {
            await route.continue();
        }
    });
}

/**
 * Mock the job status endpoint to return a job in specific state
 */
export async function mockJobStatus(
    page: Page,
    options: MockJobOptions = {}
): Promise<void> {
    const { state = 'completed', jobId = 'mock-job-123', overrides } = options;
    const mockJob = createMockJob(state, { job_id: jobId, ...overrides });

    await page.route(`**/api/jobs/${jobId}`, async (route: Route) => {
        if (route.request().method() === 'GET') {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify(mockJob),
            });
        } else {
            await route.continue();
        }
    });
}

/**
 * Mock job status to return 404 Not Found
 */
export async function mockJobNotFound(page: Page, jobId: string = 'non-existent'): Promise<void> {
    await page.route(`**/api/jobs/${jobId}`, async (route: Route) => {
        await route.fulfill({
            status: 404,
            contentType: 'application/json',
            body: JSON.stringify({ detail: 'Job not found' }),
        });
    });
}

/**
 * Mock backend unavailable error (503)
 */
export async function mockBackendUnavailable(page: Page): Promise<void> {
    await page.route('**/api/jobs**', async (route: Route) => {
        await route.fulfill({
            status: 503,
            contentType: 'application/json',
            body: JSON.stringify(mockAPIErrors.backendUnavailable),
        });
    });
}

/**
 * Mock rate limit error (429)
 */
export async function mockRateLimitError(page: Page): Promise<void> {
    await page.route('**/api/jobs**', async (route: Route) => {
        await route.fulfill({
            status: 429,
            contentType: 'application/json',
            body: JSON.stringify(mockAPIErrors.rateLimitError),
        });
    });
}

// ----- SSE Stream Mocking -----

export interface SSEMockOptions {
    events?: string[];
    delayMs?: number;
    jobId?: string;
}

/**
 * Mock the SSE stream endpoint with specified events
 */
export async function mockSSEStream(
    page: Page,
    options: SSEMockOptions = {}
): Promise<void> {
    const {
        events = generateHappyPathSSEStream(),
        delayMs = 100,
        jobId = 'mock-job-123'
    } = options;

    await page.route(`**/api/jobs/${jobId}/stream`, async (route: Route) => {
        // Build SSE response body with events
        const body = events.join('');

        await route.fulfill({
            status: 200,
            headers: {
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
            },
            body: body,
        });
    });
}

/**
 * Mock SSE stream that immediately completes with success
 */
export async function mockSSEComplete(page: Page, jobId: string = 'mock-job-123'): Promise<void> {
    const events = [
        mockSSEEvents.connected('initialized', 0),
        mockSSEEvents.progress('completed', 100),
        mockSSEEvents.complete(),
    ];
    await mockSSEStream(page, { events, jobId });
}

/**
 * Mock SSE stream that fails with an error
 */
export async function mockSSEError(
    page: Page,
    errorMessage: string = 'Processing failed',
    jobId: string = 'mock-job-123'
): Promise<void> {
    const events = [
        mockSSEEvents.connected('initialized', 0),
        mockSSEEvents.progress('gap_analysis', 15),
        mockSSEEvents.error(errorMessage),
    ];
    await mockSSEStream(page, { events, jobId });
}

// ----- File Upload Helpers -----

/**
 * Upload a file to a specified input by name
 */
export async function uploadFile(
    page: Page,
    inputName: string,
    content: string,
    filename: string = 'test.md'
): Promise<void> {
    const input = page.locator(`input[name="${inputName}"]`);
    await input.setInputFiles({
        name: filename,
        mimeType: 'text/markdown',
        buffer: Buffer.from(content),
    });
    // Dispatch change event to trigger Svelte 5's reactive handler
    await input.evaluate((el) => el.dispatchEvent(new Event('change', { bubbles: true })));
}

/**
 * Upload standard JD and Resume files
 */
export async function uploadStandardFiles(page: Page): Promise<void> {
    await uploadFile(page, 'jd', SAMPLE_JOB_DESCRIPTION, 'job-description.md');
    await uploadFile(page, 'resume', SAMPLE_RESUME, 'resume.md');
}

/**
 * Submit the upload form
 */
export async function submitUploadForm(page: Page): Promise<void> {
    await page.locator('button[type="submit"]').click();
}

/**
 * Full flow: upload files and submit
 */
export async function uploadAndSubmit(page: Page): Promise<void> {
    await uploadStandardFiles(page);
    await submitUploadForm(page);
}

// ----- Navigation Helpers -----

/**
 * Navigate to job page with mocked responses
 */
export async function goToMockedJobPage(
    page: Page,
    options: MockJobOptions & { mockStream?: boolean } = {}
): Promise<void> {
    const { jobId = 'mock-job-123', mockStream = true } = options;

    // Setup mocks before navigation
    await mockJobStatus(page, { ...options, jobId });
    if (mockStream) {
        await mockSSEComplete(page, jobId);
    }

    await page.goto(`/jobs/${jobId}`);
}

/**
 * Navigate to a completed job page with full results
 */
export async function goToCompletedJobPage(page: Page, jobId: string = 'mock-job-123'): Promise<void> {
    await goToMockedJobPage(page, {
        jobId,
        state: 'completed',
        overrides: {
            final_documents: mockFinalDocuments,
            audit_report: mockAuditReportApproved,
            executive_brief: mockExecutiveBrief,
            intermediate_results: mockIntermediateResults,
        },
    });
}

// ----- Assertion Helpers -----

/**
 * Wait for loading overlay to disappear
 */
export async function waitForLoadingComplete(page: Page, timeout: number = 10000): Promise<void> {
    await page.locator('.loading-overlay').waitFor({ state: 'hidden', timeout });
}

/**
 * Wait for error message to appear
 */
export async function waitForError(page: Page, timeout: number = 5000): Promise<string> {
    const error = page.locator('.error');
    await error.waitFor({ state: 'visible', timeout });
    return await error.textContent() || '';
}

// ----- Re-exports for convenience -----

export {
    createMockJob,
    mockFinalDocuments,
    mockAuditReportApproved,
    mockAuditReportRejected,
    mockExecutiveBrief,
    mockIntermediateResults,
    mockSSEEvents,
    generateHappyPathSSEStream,
    mockAPIErrors,
    SAMPLE_JOB_DESCRIPTION,
    SAMPLE_RESUME,
} from '../fixtures/mock-responses';
