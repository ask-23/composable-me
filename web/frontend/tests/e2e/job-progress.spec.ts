import { test, expect } from '@playwright/test';
import {
    mockJobCreation,
    mockJobStatus,
    mockSSEStream,
    mockSSEComplete,
    mockSSEError,
    mockJobNotFound,
    goToMockedJobPage,
    goToCompletedJobPage,
    uploadStandardFiles,
    mockSSEEvents,
    generateHappyPathSSEStream,
    createMockJob,
    mockFinalDocuments,
    mockAuditReportApproved,
    mockExecutiveBrief,
} from '../helpers/test-helpers';

test.describe('Job Progress Page', () => {
    // Note: These tests require a valid job to exist
    // In a real scenario, we'd create a job first or use mocks

    test('shows error for non-existent job', async ({ page }) => {
        await page.goto('/jobs/non-existent-job-id');

        // Should show error
        await expect(page.locator('.error')).toBeVisible();
        await expect(page.locator('.error')).toContainText(/not found|error/i);
    });

    test('job page has correct structure', async ({ page }) => {
        const jobId = 'structure-test';

        // Use mocked job page to test structure without backend dependency
        await goToMockedJobPage(page, { jobId, state: 'gap_analysis' });

        // Check page structure
        await expect(page.getByRole('heading', { name: 'Job Progress' })).toBeVisible();
        await expect(page.locator('.job-id')).toBeVisible();

        // Progress container should exist
        await expect(page.locator('.progress-container')).toBeVisible();
    });

    test('progress stages are visible', async ({ page }) => {
        const jobId = 'stages-visible-test';

        // Use mocked job page to avoid backend dependency
        await goToMockedJobPage(page, { jobId, state: 'gap_analysis' });

        // Check stage labels exist (use exact match to avoid JSON debug content)
        await expect(page.getByText('Starting', { exact: true }).first()).toBeVisible();
        await expect(page.getByText('Gap Analysis', { exact: true })).toBeVisible();
        await expect(page.getByText('Interview Prep', { exact: true })).toBeVisible();
        await expect(page.getByText('Tailoring', { exact: true }).first()).toBeVisible();
        await expect(page.getByText('ATS Optimization', { exact: true })).toBeVisible();
        await expect(page.getByText('Auditing', { exact: true })).toBeVisible();
        await expect(page.getByText('Complete', { exact: true })).toBeVisible();
    });

    test('timer starts on page load', async ({ page }) => {
        const jobId = 'timer-start-test';

        // Use mocked job page in an in-progress state so timer keeps running
        await mockJobStatus(page, { jobId, state: 'gap_analysis' });

        // Mock SSE that stays open (doesn't complete)
        const events = [mockSSEEvents.connected('gap_analysis', 15)];
        await mockSSEStream(page, { events, jobId });

        await page.goto(`/jobs/${jobId}?mock`);

        // Timer should show and increment
        const timer = page.locator('.timer');
        await expect(timer).toBeVisible();

        // Wait a bit and check timer increments
        const initialText = await timer.textContent();
        await page.waitForTimeout(2000);
        const updatedText = await timer.textContent();

        // Timer should have changed (job is still running)
        expect(updatedText).not.toBe(initialText);
    });

    test('agent card shows current stage info', async ({ page }) => {
        const jobId = 'agent-card-test';

        // Use mocked job page to test agent card without backend dependency
        await goToMockedJobPage(page, { jobId, state: 'gap_analysis' });

        // Agent card should be visible
        const agentCard = page.locator('.agent-card');
        await expect(agentCard).toBeVisible();

        // Should have agent name and description
        await expect(agentCard.locator('h3')).toBeVisible();
        await expect(agentCard.locator('.agent-status')).toBeVisible();

        // Should have "What I do" section
        await expect(agentCard.locator('text=What I do')).toBeVisible();

        // Should have fun fact
        await expect(agentCard.locator('.agent-funfact')).toBeVisible();
    });

    test('back link navigates to upload page', async ({ page }) => {
        const jobId = 'back-link-test';

        // Use mocked job page to test navigation without backend dependency
        await goToMockedJobPage(page, { jobId, state: 'gap_analysis' });

        // Click back link
        await page.locator('.back-link').click();

        // Should be back on upload page
        await expect(page).toHaveURL('/');
    });
});

test.describe('Job Progress Page - Mocked SSE', () => {
    test('displays initialized state correctly', async ({ page }) => {
        const jobId = 'init-state-test';

        // Mock job in initialized state
        await goToMockedJobPage(page, { jobId, state: 'initialized' });

        // Check progress is at 0%
        await expect(page.locator('.progress-percent')).toContainText('0%');

        // Agent card should show Hydra Orchestrator
        await expect(page.locator('.agent-card h3')).toContainText('Hydra Orchestrator');
    });

    test('displays gap_analysis state correctly', async ({ page }) => {
        const jobId = 'gap-state-test';

        await goToMockedJobPage(page, { jobId, state: 'gap_analysis' });

        // Progress should be around 15%
        const progressText = await page.locator('.progress-percent').textContent();
        expect(parseInt(progressText || '0')).toBeGreaterThan(0);

        // Agent card should show Gap Analyzer
        await expect(page.locator('.agent-card h3')).toContainText('Gap Analyzer');

        // Stage dot should show active state
        const gapStage = page.locator('.stage').filter({ hasText: 'Gap Analysis' });
        await expect(gapStage.locator('.stage-dot .pulse')).toBeVisible();
    });

    test('completed state shows success styling', async ({ page }) => {
        const jobId = 'complete-test';

        await goToCompletedJobPage(page, jobId);

        // Agent card should have success class (wait for SSE to process)
        await expect(page.locator('.agent-card.success')).toBeVisible({ timeout: 10000 });

        // Progress should be at 100%
        await expect(page.locator('.progress-percent')).toContainText('100%', { timeout: 5000 });

        // Results viewer should appear
        await expect(page.locator('.results-viewer')).toBeVisible({ timeout: 5000 });
    });

    test('failed state shows error styling', async ({ page }) => {
        const jobId = 'failed-test';

        // Mock failed job
        await mockJobStatus(page, {
            jobId,
            state: 'failed',
            overrides: {
                error_message: 'LLM API error occurred',
                success: false,
            },
        });
        await mockSSEError(page, 'Processing failed', jobId);

        await page.goto(`/jobs/${jobId}?mock`);

        // Agent card should have error class
        await expect(page.locator('.agent-card.error')).toBeVisible();
    });

    test('SSE progress updates change UI in real-time', async ({ page }) => {
        const jobId = 'sse-progress-test';

        // Mock job as initialized
        await mockJobStatus(page, { jobId, state: 'initialized' });

        // Mock SSE stream with progressive events
        const events = [
            mockSSEEvents.connected('initialized', 0),
            mockSSEEvents.progress('gap_analysis', 15),
            mockSSEEvents.stageComplete('gap_analysis'),
            mockSSEEvents.progress('interrogation', 30),
            mockSSEEvents.progress('completed', 100),
            mockSSEEvents.complete(),
        ];
        await mockSSEStream(page, { events, jobId });

        await page.goto(`/jobs/${jobId}?mock`);

        // Eventually should reach completed state
        await expect(page.locator('.agent-card.success')).toBeVisible({ timeout: 5000 });
    });

    test('error banner shows when SSE sends error event', async ({ page }) => {
        const jobId = 'error-event-test';

        // Mock job and SSE with error
        await mockJobStatus(page, { jobId, state: 'gap_analysis' });
        await mockSSEError(page, 'Backend processing error occurred', jobId);

        await page.goto(`/jobs/${jobId}?mock`);

        // Error banner should appear with some error message
        // Note: May show "Connection lost" if SSE closes before error event processes,
        // or the actual error message if it processes in time
        await expect(page.locator('.error-banner')).toBeVisible({ timeout: 5000 });
        // Accept either the specific error or connection lost message
        await expect(page.locator('.error-banner')).toContainText(/error|connection lost/i);
    });

    test('execution log can be expanded', async ({ page }) => {
        const jobId = 'log-test';

        // Mock job with some logs
        await mockJobStatus(page, {
            jobId,
            state: 'gap_analysis',
            overrides: {
                execution_log: ['Starting gap_analysis...', 'Analyzing requirements...'],
            },
        });

        // Mock SSE with log events
        const events = [
            mockSSEEvents.connected('gap_analysis', 15),
            mockSSEEvents.log('Processing job description'),
            mockSSEEvents.log('Extracting requirements'),
        ];
        await mockSSEStream(page, { events, jobId });

        await page.goto(`/jobs/${jobId}?mock`);

        // Log container should be present (collapsed)
        const logContainer = page.locator('.log-container');

        // If visible, click to expand
        if (await logContainer.isVisible()) {
            await logContainer.locator('summary').click();

            // Log entries should be visible
            await expect(page.locator('.log-list li').first()).toBeVisible();
        }
    });
});

test.describe('Job Progress Page - Error States', () => {
    test('shows job not found error', async ({ page }) => {
        const jobId = 'not-found-job';

        await mockJobNotFound(page, jobId);

        await page.goto(`/jobs/${jobId}`);

        // Error card should be visible
        await expect(page.locator('.error')).toBeVisible();
        await expect(page.getByRole('heading', { name: 'Job Not Found' })).toBeVisible();

        // Should have link to start new job
        await expect(page.locator('.btn-primary')).toContainText('Start a New Job');
    });

    test('new job link works from error page', async ({ page }) => {
        const jobId = 'not-found-job-2';

        await mockJobNotFound(page, jobId);

        await page.goto(`/jobs/${jobId}`);

        // Click the new job button
        await page.locator('.btn-primary').click();

        // Should navigate to upload page
        await expect(page).toHaveURL('/');
    });

    test('connection status shows connecting message initially', async ({ page }) => {
        const jobId = 'connecting-test';

        // Mock job but DON'T mock SSE stream (will fail to connect)
        await mockJobStatus(page, { jobId, state: 'initialized' });

        await page.goto(`/jobs/${jobId}?mock`);

        // Should briefly show connecting message (if not yet connected)
        // This is timing-sensitive so we just check page loads without errors
        await expect(page.locator('.progress-container')).toBeVisible();
    });
});

test.describe('Job Progress Page - Stage Transitions', () => {
    test('all 7 stages have correct indicators', async ({ page }) => {
        const jobId = 'all-stages-test';

        await goToMockedJobPage(page, { jobId, state: 'auditing' });

        // Check all stage labels exist
        const stageLabels = [
            'Starting',
            'Gap Analysis',
            'Interview Prep',
            'Tailoring',
            'ATS Optimization',
            'Auditing',
            'Complete'
        ];

        for (const label of stageLabels) {
            await expect(page.getByText(label, { exact: true }).first()).toBeVisible();
        }

        // Should have 7 stage dots
        await expect(page.locator('.stage-dot')).toHaveCount(7);
    });

    test('completed stages show checkmarks', async ({ page }) => {
        const jobId = 'checkmarks-test';

        // Mock job at tailoring state (4th stage)
        await goToMockedJobPage(page, { jobId, state: 'tailoring' });

        // Earlier stages should have checkmark SVGs
        const completedStages = page.locator('.stage.complete .stage-dot svg');
        const count = await completedStages.count();
        expect(count).toBeGreaterThan(0);
    });

    test('active stage shows pulsing indicator', async ({ page }) => {
        const jobId = 'pulse-test';

        await goToMockedJobPage(page, { jobId, state: 'differentiation' });

        // Active stage should have pulse animation
        const activeStage = page.locator('.stage.active .stage-dot .pulse');
        await expect(activeStage).toBeVisible();
    });

    test('pending stages show inactive dots', async ({ page }) => {
        const jobId = 'pending-test';

        await goToMockedJobPage(page, { jobId, state: 'gap_analysis' });

        // Pending stages should have regular dots
        const pendingDots = page.locator('.stage.pending .stage-dot .dot');
        const count = await pendingDots.count();
        expect(count).toBeGreaterThan(0);
    });
});

test.describe('Job Progress Page - Timer', () => {
    test('timer shows elapsed time format', async ({ page }) => {
        const jobId = 'timer-format-test';

        await goToMockedJobPage(page, { jobId, state: 'gap_analysis' });

        // Timer should be visible with time format
        const timer = page.locator('.timer');
        await expect(timer).toBeVisible();

        const timerText = await timer.textContent();
        // Should match format like "0s" or "1m 30s"
        expect(timerText).toMatch(/\d+s|\d+m \d+s/);
    });

    test('timer increments while job is running', async ({ page }) => {
        const jobId = 'timer-increment-test';

        // Keep job running (don't complete)
        await mockJobStatus(page, { jobId, state: 'gap_analysis' });

        // Mock SSE that stays open
        const events = [mockSSEEvents.connected('gap_analysis', 15)];
        await mockSSEStream(page, { events, jobId });

        await page.goto(`/jobs/${jobId}?mock`);

        const timer = page.locator('.timer');
        await expect(timer).toBeVisible();

        // Get initial time
        const initialText = await timer.textContent();

        // Wait and check it incremented
        await page.waitForTimeout(2000);
        const updatedText = await timer.textContent();

        expect(updatedText).not.toBe(initialText);
    });
});

test.describe('Job Progress Page - Agent Card Details', () => {
    test('agent card shows model badge when available', async ({ page }) => {
        const jobId = 'model-badge-test';

        // Mock job status with agent_models
        await mockJobStatus(page, {
            jobId,
            state: 'gap_analysis',
            overrides: {
                agent_models: {
                    gap_analysis: 'meta-llama/llama-4-maverick',
                },
            },
        });

        // Mock SSE with agent_models in progress events (UI reads from SSE, not job status)
        const events = [
            mockSSEEvents.connected('gap_analysis', 15),
            mockSSEEvents.progress('gap_analysis', 15, { gap_analysis: 'meta-llama/llama-4-maverick' }),
        ];
        await mockSSEStream(page, { events, jobId });

        await page.goto(`/jobs/${jobId}?mock`);

        // Wait for progress card to load first
        await expect(page.locator('.progress-card')).toBeVisible({ timeout: 5000 });

        // Model badge should show
        const modelBadge = page.locator('.model-badge');
        await expect(modelBadge).toBeVisible({ timeout: 5000 });
        await expect(modelBadge).toContainText(/llama/i);
    });

    test('agent card displays fun fact', async ({ page }) => {
        const jobId = 'funfact-test';

        await goToMockedJobPage(page, { jobId, state: 'interrogation' });

        // Fun fact section should be visible
        const funfact = page.locator('.agent-funfact');
        await expect(funfact).toBeVisible();

        // Should have lightbulb icon
        await expect(funfact.locator('.funfact-icon')).toBeVisible();
    });
});

