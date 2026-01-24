/**
 * Error handling E2E tests for Hydra web app.
 * Tests edge cases and error states across the application.
 */

import { test, expect } from '@playwright/test';
import {
    mockBackendUnavailable,
    mockRateLimitError,
    mockJobNotFound,
    mockJobStatus,
    mockSSEError,
    mockSSEStream,
    mockSSEEvents,
    uploadStandardFiles,
} from '../helpers/test-helpers';

test.describe('Error Handling - Backend Unavailable', () => {
    test('shows friendly error when backend is down on upload', async ({ page }) => {
        await mockBackendUnavailable(page);

        await page.goto('/');
        await uploadStandardFiles(page);

        await page.locator('button[type="submit"]').click();

        // Should show error message
        const error = page.locator('.error');
        await expect(error).toBeVisible({ timeout: 5000 });
        await expect(error).toContainText(/backend|server|connect/i);
    });

    test('form can be resubmitted after error', async ({ page }) => {
        await mockBackendUnavailable(page);

        await page.goto('/');
        await uploadStandardFiles(page);

        await page.locator('button[type="submit"]').click();
        await expect(page.locator('.error')).toBeVisible({ timeout: 5000 });

        // Button should be re-enabled
        const submitBtn = page.locator('button[type="submit"]');
        await expect(submitBtn).toBeEnabled();

        // Loading overlay should be hidden
        await expect(page.locator('.loading-overlay')).not.toBeVisible();
    });
});

test.describe('Error Handling - Rate Limiting', () => {
    test('shows rate limit error message', async ({ page }) => {
        await mockRateLimitError(page);

        await page.goto('/');
        await uploadStandardFiles(page);

        await page.locator('button[type="submit"]').click();

        // Should show rate limit error
        const error = page.locator('.error');
        await expect(error).toBeVisible({ timeout: 5000 });
        await expect(error).toContainText(/rate limit/i);
    });
});

test.describe('Error Handling - Job Not Found', () => {
    test('shows job not found error for invalid ID', async ({ page }) => {
        const invalidJobId = 'invalid-job-id-12345';
        await mockJobNotFound(page, invalidJobId);

        await page.goto(`/jobs/${invalidJobId}`);

        // Error card should be visible
        await expect(page.locator('.error')).toBeVisible();
        await expect(page.getByRole('heading', { name: 'Job Not Found' })).toBeVisible();
    });

    test('provides link to create new job', async ({ page }) => {
        const invalidJobId = 'invalid-job-id-nav';
        await mockJobNotFound(page, invalidJobId);

        await page.goto(`/jobs/${invalidJobId}`);

        // Start new job button should exist
        const newJobBtn = page.locator('.btn-primary');
        await expect(newJobBtn).toBeVisible();
        await expect(newJobBtn).toContainText('Start a New Job');

        // Click should navigate to home
        await newJobBtn.click();
        await expect(page).toHaveURL('/');
    });

    test('shows descriptive message about job expiration', async ({ page }) => {
        const expiredJobId = 'expired-job-id';
        await mockJobNotFound(page, expiredJobId);

        await page.goto(`/jobs/${expiredJobId}`);

        // Should mention expiration or server restart
        await expect(page.locator('.error')).toContainText(/expired|restart/i);
    });
});

test.describe('Error Handling - SSE Stream Errors', () => {
    test('shows error banner when SSE sends error event', async ({ page }) => {
        const jobId = 'sse-error-test';

        await mockJobStatus(page, { jobId, state: 'gap_analysis' });
        await mockSSEError(page, 'LLM API rate limit exceeded', jobId);

        await page.goto(`/jobs/${jobId}`);

        // Error banner should appear
        await expect(page.locator('.error-banner')).toBeVisible({ timeout: 5000 });
    });

    test('displays error message content', async ({ page }) => {
        const jobId = 'sse-error-content-test';
        const errorMessage = 'Processing failed: Invalid response from LLM';

        await mockJobStatus(page, { jobId, state: 'tailoring' });
        await mockSSEError(page, errorMessage, jobId);

        await page.goto(`/jobs/${jobId}`);

        // Error message should contain the error text
        await expect(page.locator('.error-banner')).toContainText(/error|failed/i);
    });

    test('handles connection lost gracefully', async ({ page }) => {
        const jobId = 'connection-lost-test';

        await mockJobStatus(page, { jobId, state: 'gap_analysis' });

        // Mock SSE that only sends connection event (simulates disconnect)
        const events = [mockSSEEvents.connected('gap_analysis', 15)];
        await mockSSEStream(page, { events, jobId });

        await page.goto(`/jobs/${jobId}`);

        // Page should still be functional
        await expect(page.locator('.progress-container')).toBeVisible();
    });
});

test.describe('Error Handling - Validation Errors', () => {
    test('shows error for empty job description', async ({ page }) => {
        await page.goto('/');

        // Only upload resume
        await page.locator('input[name="resume"]').setInputFiles({
            name: 'resume.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# John Doe\n\nExperienced engineer'),
        });

        await page.locator('button[type="submit"]').click();

        // Should show validation error
        const error = page.locator('.error');
        await expect(error).toBeVisible();
        await expect(error).toContainText(/job description|required/i);
    });

    test('shows error for empty resume', async ({ page }) => {
        await page.goto('/');

        // Only upload JD
        await page.locator('input[name="jd"]').setInputFiles({
            name: 'jd.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# Software Engineer\n\nPython required'),
        });

        await page.locator('button[type="submit"]').click();

        // Should show validation error
        const error = page.locator('.error');
        await expect(error).toBeVisible();
        await expect(error).toContainText(/resume|required/i);
    });

    test('shows error when both fields are empty', async ({ page }) => {
        await page.goto('/');

        await page.locator('button[type="submit"]').click();

        // Should show validation error
        const error = page.locator('.error');
        await expect(error).toBeVisible();
        await expect(error).toContainText(/required/i);
    });
});

test.describe('Error Handling - Network Issues', () => {
    test('handles slow network gracefully', async ({ page }) => {
        const jobId = 'slow-network-test';

        // Mock with delay
        await mockJobStatus(page, { jobId, state: 'initialized' });

        // Slow route handler
        await page.route(`**/api/jobs/${jobId}/stream`, async (route) => {
            // Delay response
            await new Promise(resolve => setTimeout(resolve, 2000));
            await route.fulfill({
                status: 200,
                headers: { 'Content-Type': 'text/event-stream' },
                body: mockSSEEvents.connected('initialized', 0),
            });
        });

        await page.goto(`/jobs/${jobId}`);

        // Should show connecting state or progress container
        await expect(page.locator('.progress-container')).toBeVisible();
    });
});

test.describe('Error Handling - Failed Jobs', () => {
    test('failed job shows error styling', async ({ page }) => {
        const jobId = 'failed-job-test';

        await mockJobStatus(page, {
            jobId,
            state: 'failed',
            overrides: {
                success: false,
                error_message: 'Job processing failed due to LLM error',
            },
        });

        // Mock SSE with failure
        const events = [
            mockSSEEvents.connected('failed', 0),
            mockSSEEvents.complete({
                success: false,
                state: 'failed',
                error_message: 'Job processing failed',
            }),
        ];
        await mockSSEStream(page, { events, jobId });

        await page.goto(`/jobs/${jobId}`);

        // Agent card should show error state
        await expect(page.locator('.agent-card.error')).toBeVisible();
    });

    test('failed job displays error message', async ({ page }) => {
        const jobId = 'failed-job-msg-test';
        const errorMsg = 'API quota exceeded';

        await mockJobStatus(page, {
            jobId,
            state: 'failed',
            overrides: {
                success: false,
                error_message: errorMsg,
            },
        });
        await mockSSEError(page, errorMsg, jobId);

        await page.goto(`/jobs/${jobId}`);

        // Error banner should be visible
        await expect(page.locator('.error-banner')).toBeVisible({ timeout: 5000 });
    });
});

test.describe('Error Handling - Edge Cases', () => {
    test('handles special characters in job ID', async ({ page }) => {
        const specialJobId = 'job-with-special-chars-!@#';
        await mockJobNotFound(page, specialJobId);

        await page.goto(`/jobs/${encodeURIComponent(specialJobId)}`);

        // Should show error (not crash)
        await expect(page.locator('.error')).toBeVisible();
    });

    test('handles very long job ID', async ({ page }) => {
        const longJobId = 'a'.repeat(100);
        await mockJobNotFound(page, longJobId);

        await page.goto(`/jobs/${longJobId}`);

        // Should show error (not crash)
        await expect(page.locator('.error')).toBeVisible();
    });
});
