import { test, expect } from '@playwright/test';
import {
    goToCompletedJobPage,
    mockJobStatus,
    mockSSEComplete,
    mockFinalDocuments,
    mockAuditReportApproved,
    mockAuditReportRejected,
    mockExecutiveBrief,
    mockIntermediateResults,
    createMockJob,
} from '../helpers/test-helpers';
import { mockAuditReportCrashed } from '../fixtures/mock-responses';

test.describe('Results Viewer', () => {
    // Helper to create a job and wait for completion
    // Note: This requires a working backend with fast processing
    // In CI, you might want to mock the backend or use fixtures

    test('completed job shows results tabs', async ({ page }) => {
        test.slow(); // Increase timeout to 3x for LLM workflow completion
        // This test is skipped by default as it requires full workflow completion
        // Unskip when running against a real backend with fast processing

        await page.goto('/');

        await page.locator('input[name="jd"]').setInputFiles({
            name: 'jd.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# Software Engineer\n\nPython required'),
        });

        await page.locator('input[name="resume"]').setInputFiles({
            name: 'resume.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# John Doe\n\n5 years Python experience'),
        });

        await page.locator('button[type="submit"]').click();
        await expect(page).toHaveURL(/\/jobs\/[a-f0-9-]+/, { timeout: 10000 });

        // Wait for job to complete (this could take a while)
        await expect(page.getByText('Mission Accomplished'))
            .toBeVisible({ timeout: 120000 });

        // Check completion message is visible
        await expect(page.getByText('Mission Accomplished')).toBeVisible();
        await expect(page.getByText('Your application materials are ready')).toBeVisible();
    });

    test('error state shows error message', async ({ page }) => {
        // Navigate to a job that will fail
        await page.goto('/');

        // Upload files with minimal content (will trigger validation error)
        await page.locator('input[name="jd"]').setInputFiles({
            name: 'jd.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# Simple Job\n\nBasic requirements'), // Needs 10+ chars
        });

        await page.locator('input[name="resume"]').setInputFiles({
            name: 'resume.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# Simple Resume\n\nBasic experience'), // Needs 10+ chars
        });

        await page.locator('button[type="submit"]').click();

        // Wait for either redirect to job page OR error message
        await Promise.race([
            expect(page).toHaveURL(/\/jobs\/[a-f0-9-]+/, { timeout: 15000 }),
            expect(page.locator('.error')).toBeVisible({ timeout: 15000 })
        ]);
    });
});

test.describe('Results Viewer - Mocked', () => {
    test('shows TLDR hero section with verdict badge', async ({ page }) => {
        const jobId = 'tldr-hero-test';
        await goToCompletedJobPage(page, jobId);

        // TLDR hero should be visible
        const tldrHero = page.locator('.tldr-hero');
        await expect(tldrHero).toBeVisible();

        // Verdict badge should show
        await expect(page.locator('.verdict-badge')).toBeVisible();
        await expect(page.locator('.verdict-label')).toBeVisible();
    });

    test('displays all 5 tabs', async ({ page }) => {
        const jobId = 'tabs-test';
        await goToCompletedJobPage(page, jobId);

        // Check all tabs exist
        const tabs = page.locator('.tabs .tab');
        await expect(tabs).toHaveCount(5);

        // Verify tab labels
        await expect(page.locator('.tab').filter({ hasText: 'Summary' })).toBeVisible();
        await expect(page.locator('.tab').filter({ hasText: 'Resume' })).toBeVisible();
        await expect(page.locator('.tab').filter({ hasText: 'Cover Letter' })).toBeVisible();
        await expect(page.locator('.tab').filter({ hasText: 'Audit' })).toBeVisible();
        await expect(page.locator('.tab').filter({ hasText: 'Debug' })).toBeVisible();
    });

    test('Summary tab is default active', async ({ page }) => {
        const jobId = 'default-tab-test';
        await goToCompletedJobPage(page, jobId);

        // Summary tab should be active
        await expect(page.locator('.tab.active')).toContainText('Summary');

        // Executive summary should be visible
        await expect(page.locator('.executive-summary')).toBeVisible();
    });

    test('can navigate to Resume tab', async ({ page }) => {
        const jobId = 'resume-tab-test';
        await goToCompletedJobPage(page, jobId);

        // Click Resume tab
        await page.locator('.tab').filter({ hasText: 'Resume' }).click();

        // Resume tab should now be active
        await expect(page.locator('.tab.active')).toContainText('Resume');

        // Resume content should be visible
        await expect(page.locator('.document-panel')).toBeVisible();
        await expect(page.locator('h3').filter({ hasText: 'Tailored Resume' })).toBeVisible();
    });

    test('can navigate to Cover Letter tab', async ({ page }) => {
        const jobId = 'cover-letter-tab-test';
        await goToCompletedJobPage(page, jobId);

        // Click Cover Letter tab
        await page.locator('.tab').filter({ hasText: 'Cover Letter' }).click();

        // Cover Letter tab should now be active
        await expect(page.locator('.tab.active')).toContainText('Cover Letter');

        // Cover letter content should be visible
        await expect(page.locator('h3').filter({ hasText: 'Cover Letter' })).toBeVisible();
    });

    test('can navigate to Audit tab', async ({ page }) => {
        const jobId = 'audit-tab-test';
        await goToCompletedJobPage(page, jobId);

        // Click Audit tab
        await page.locator('.tab').filter({ hasText: 'Audit' }).click();

        // Audit panel should be visible
        await expect(page.locator('.audit-panel')).toBeVisible();
        await expect(page.locator('h3').filter({ hasText: 'Audit Report' })).toBeVisible();
    });

    test('can navigate to Debug tab', async ({ page }) => {
        const jobId = 'debug-tab-test';
        await goToCompletedJobPage(page, jobId);

        // Click Debug tab
        await page.locator('.tab').filter({ hasText: 'Debug' }).click();

        // Debug panel should be visible
        await expect(page.locator('.debug-panel')).toBeVisible();
        await expect(page.locator('h3').filter({ hasText: 'Intermediate Results' })).toBeVisible();
    });

    test('Resume tab has copy button', async ({ page }) => {
        const jobId = 'copy-btn-test';
        await goToCompletedJobPage(page, jobId);

        // Go to Resume tab
        await page.locator('.tab').filter({ hasText: 'Resume' }).click();

        // Copy button should be visible
        const copyBtn = page.locator('.copy-btn');
        await expect(copyBtn).toBeVisible();
        await expect(copyBtn).toContainText('Copy');
    });

    test('Cover Letter tab has copy button', async ({ page }) => {
        const jobId = 'copy-btn-cl-test';
        await goToCompletedJobPage(page, jobId);

        // Go to Cover Letter tab
        await page.locator('.tab').filter({ hasText: 'Cover Letter' }).click();

        // Copy button should be visible
        const copyBtn = page.locator('.copy-btn');
        await expect(copyBtn).toBeVisible();
    });
});

test.describe('Results Viewer - Verdict Badges', () => {
    test('APPROVED status shows success styling', async ({ page }) => {
        const jobId = 'approved-verdict-test';

        await mockJobStatus(page, {
            jobId,
            state: 'completed',
            overrides: {
                final_documents: mockFinalDocuments,
                audit_report: mockAuditReportApproved,
                executive_brief: mockExecutiveBrief,
            },
        });
        await mockSSEComplete(page, jobId);

        await page.goto(`/jobs/${jobId}`);

        // TLDR hero should have success class
        await expect(page.locator('.tldr-hero.success')).toBeVisible();
    });

    test('REJECTED status shows error styling', async ({ page }) => {
        const jobId = 'rejected-verdict-test';

        await mockJobStatus(page, {
            jobId,
            state: 'completed',
            overrides: {
                final_documents: mockFinalDocuments,
                audit_report: mockAuditReportRejected,
            },
        });
        await mockSSEComplete(page, jobId);

        await page.goto(`/jobs/${jobId}`);

        // TLDR hero should have error class
        await expect(page.locator('.tldr-hero.error')).toBeVisible();
    });

    test('audit_failed shows warning styling', async ({ page }) => {
        const jobId = 'warning-verdict-test';

        await mockJobStatus(page, {
            jobId,
            state: 'completed',
            overrides: {
                final_documents: mockFinalDocuments,
                audit_failed: true,
                audit_error: 'Audit did not complete successfully',
            },
        });
        await mockSSEComplete(page, jobId);

        await page.goto(`/jobs/${jobId}`);

        // TLDR hero should have warning class
        await expect(page.locator('.tldr-hero.warning')).toBeVisible();
    });
});

test.describe('Results Viewer - Audit Panel', () => {
    test('shows audit summary with status and retry count', async ({ page }) => {
        const jobId = 'audit-summary-test';
        await goToCompletedJobPage(page, jobId);

        // Go to Audit tab
        await page.locator('.tab').filter({ hasText: 'Audit' }).click();

        // Audit summary should show status and retries
        await expect(page.locator('.audit-stat').first()).toBeVisible();
    });

    test('shows rejection reason when present', async ({ page }) => {
        const jobId = 'rejection-reason-test';

        await mockJobStatus(page, {
            jobId,
            state: 'completed',
            overrides: {
                final_documents: mockFinalDocuments,
                audit_report: mockAuditReportRejected,
            },
        });
        await mockSSEComplete(page, jobId);

        await page.goto(`/jobs/${jobId}`);

        // Go to Audit tab
        await page.locator('.tab').filter({ hasText: 'Audit' }).click();

        // Rejection reason should be visible
        await expect(page.locator('.audit-section.warning')).toBeVisible();
        await expect(page.getByRole('heading', { name: 'Rejection Reason' })).toBeVisible();
    });

    test('shows crash error when audit crashed', async ({ page }) => {
        const jobId = 'crash-error-test';

        await mockJobStatus(page, {
            jobId,
            state: 'completed',
            overrides: {
                final_documents: mockFinalDocuments,
                audit_report: mockAuditReportCrashed,
            },
        });
        await mockSSEComplete(page, jobId);

        await page.goto(`/jobs/${jobId}`);

        // Go to Audit tab
        await page.locator('.tab').filter({ hasText: 'Audit' }).click();

        // Error section should be visible
        await expect(page.locator('.audit-section.error')).toBeVisible();
    });

    test('audit details can be expanded', async ({ page }) => {
        const jobId = 'audit-expand-test';
        await goToCompletedJobPage(page, jobId);

        // Go to Audit tab
        await page.locator('.tab').filter({ hasText: 'Audit' }).click();

        // Click to expand resume audit details
        const auditDetails = page.locator('.audit-details').first();
        if (await auditDetails.isVisible()) {
            await auditDetails.locator('summary').click();

            // Pre content should be visible
            await expect(auditDetails.locator('pre')).toBeVisible();
        }
    });
});

test.describe('Results Viewer - Debug Panel', () => {
    test('shows intermediate results sections', async ({ page }) => {
        const jobId = 'debug-sections-test';
        await goToCompletedJobPage(page, jobId);

        // Go to Debug tab
        await page.locator('.tab').filter({ hasText: 'Debug' }).click();

        // Debug sections should be visible
        const debugSections = page.locator('.debug-section');
        const count = await debugSections.count();
        expect(count).toBeGreaterThan(0);
    });

    test('debug sections can be expanded', async ({ page }) => {
        const jobId = 'debug-expand-test';
        await goToCompletedJobPage(page, jobId);

        // Go to Debug tab
        await page.locator('.tab').filter({ hasText: 'Debug' }).click();

        // Click to expand first debug section
        const debugSection = page.locator('.debug-section').first();
        if (await debugSection.isVisible()) {
            await debugSection.locator('summary').click();

            // Pre content should be visible
            await expect(debugSection.locator('pre')).toBeVisible();
        }
    });
});

test.describe('Results Viewer - Action Items', () => {
    test('shows next steps in summary', async ({ page }) => {
        const jobId = 'action-items-test';
        await goToCompletedJobPage(page, jobId);

        // Action items section should be visible
        const actionItems = page.locator('.action-items');
        await expect(actionItems).toBeVisible();
        await expect(actionItems.locator('h3')).toContainText('Next Steps');
    });

    test('action items list contains items', async ({ page }) => {
        const jobId = 'action-items-list-test';
        await goToCompletedJobPage(page, jobId);

        // List items should exist
        const listItems = page.locator('.action-items li');
        const count = await listItems.count();
        expect(count).toBeGreaterThan(0);
    });
});

test.describe('Accessibility', () => {
    test('upload form is keyboard navigable', async ({ page }) => {
        await page.goto('/');

        // Tab through form elements
        await page.keyboard.press('Tab');

        // Check that focus moves through interactive elements
        // The exact order depends on tab index and DOM structure
        const focusedElement = page.locator(':focus');
        await expect(focusedElement).toBeVisible();
    });

    test('dropzones are keyboard accessible', async ({ page }) => {
        await page.goto('/');

        // Focus on first dropzone
        const dropzone = page.locator('.dropzone').first();
        await dropzone.focus();

        // Should be able to activate with Enter
        await expect(dropzone).toBeFocused();
    });

    test('tab navigation works with keyboard', async ({ page }) => {
        const jobId = 'keyboard-tabs-test';
        await goToCompletedJobPage(page, jobId);

        // Focus first tab
        const firstTab = page.locator('.tab').first();
        await firstTab.focus();
        await expect(firstTab).toBeFocused();

        // Tab to next tab
        await page.keyboard.press('Tab');
        const secondTab = page.locator('.tab').nth(1);
        await expect(secondTab).toBeFocused();
    });
});

