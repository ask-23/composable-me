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
 * Mock SSE stream that stays at a specific state (does not complete)
 */
export async function mockSSEAtState(page: Page, state: string, progress: number, jobId: string = 'mock-job-123'): Promise<void> {
    const events = [
        mockSSEEvents.connected(state, progress),
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
 * Upload a file to a specified input by name.
 * For Svelte 5 components with client:load hydration, we need to ensure
 * the component is fully interactive before setting files.
 */
export async function uploadFile(
    page: Page,
    inputName: string,
    content: string,
    filename: string = 'test.md'
): Promise<void> {
    const input = page.locator(`input[name="${inputName}"]`);
    const dropzone = input.locator('xpath=ancestor::div[contains(@class, "dropzone")]');

    // Retry logic for flaky Svelte 5 hydration
    let attempts = 0;
    const maxAttempts = 3;

    while (attempts < maxAttempts) {
        attempts++;

        // Click the dropzone first to ensure Svelte's event handlers are connected
        await dropzone.click();
        await page.waitForTimeout(50);

        // Set the files
        await input.setInputFiles({
            name: filename,
            mimeType: 'text/markdown',
            buffer: Buffer.from(content),
        });

        // Svelte 5 stores event handlers in __change property
        await input.evaluate((el: HTMLInputElement) => {
            const svelteHandler = (el as any).__change;
            if (typeof svelteHandler === 'function') {
                const event = new Event('change', { bubbles: true });
                Object.defineProperty(event, 'target', { value: el, writable: false });
                svelteHandler(event);
            } else {
                el.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });

        // Wait for Svelte's reactivity
        await page.waitForTimeout(100);

        // Check if the file was uploaded by looking for has-files class
        const hasFiles = await dropzone.evaluate((el) => el.classList.contains('has-files'));
        if (hasFiles) {
            return; // Success!
        }

        // If this isn't the last attempt, wait a bit before retrying
        if (attempts < maxAttempts) {
            await page.waitForTimeout(200);
        }
    }

    // If we get here, the upload didn't work after all attempts
    // Log a warning but don't fail - the test assertions will catch it
    console.warn(`File upload for ${inputName} may not have succeeded after ${maxAttempts} attempts`);
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
 * Uses ?mock query param to skip SSR and enable client-side fetching
 * which can be intercepted by Playwright routes
 */
export async function goToMockedJobPage(
    page: Page,
    options: MockJobOptions & { mockStream?: boolean } = {}
): Promise<void> {
    const { jobId = 'mock-job-123', mockStream = true, state = 'completed' } = options;

    // Setup mocks before navigation
    await mockJobStatus(page, { ...options, jobId });
    if (mockStream) {
        // For completed/failed states, use full completion stream
        // For in-progress states, mock SSE to stay at current state
        if (state === 'completed' || state === 'failed') {
            await mockSSEComplete(page, jobId);
        } else {
            // Map state to progress percentage
            const progressMap: Record<string, number> = {
                initialized: 0,
                gap_analysis: 15,
                interrogation: 30,
                differentiation: 45,
                tailoring: 60,
                ats_optimization: 75,
                auditing: 90,
            };
            const progress = progressMap[state] ?? 0;
            await mockSSEAtState(page, state, progress, jobId);
        }
    }

    // Use ?mock to skip SSR fetch and enable client-side mocking
    await page.goto(`/jobs/${jobId}?mock`);

    // Wait for the page to load the mocked data
    // For completed jobs, wait for both the success state AND results-viewer
    // This ensures SSE events have been processed
    if (state === 'completed') {
        // Wait for SSE complete event to be processed (sets .agent-card.success)
        await page.locator('.agent-card.success').waitFor({ state: 'visible', timeout: 10000 });
        await page.locator('.results-viewer').waitFor({ state: 'visible', timeout: 10000 });
    } else {
        await page.locator('.progress-card').waitFor({ state: 'visible', timeout: 10000 });
    }
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
