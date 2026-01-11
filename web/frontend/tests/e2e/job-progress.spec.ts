import { test, expect } from '@playwright/test';

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
        // First create a job by submitting the form
        await page.goto('/');

        // Upload files
        await page.locator('input[name="jd"]').setInputFiles({
            name: 'jd.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# Test Job\n\nPython required'),
        });

        await page.locator('input[name="resume"]').setInputFiles({
            name: 'resume.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# Test Resume\n\nPython experience'),
        });

        // Submit and wait for redirect
        await page.locator('button[type="submit"]').click();
        await expect(page).toHaveURL(/\/jobs\/[a-f0-9-]+/, { timeout: 10000 });

        // Check page structure
        await expect(page.getByRole('heading', { name: 'Job Progress' })).toBeVisible();
        await expect(page.locator('.job-id')).toBeVisible();

        // Progress container should exist
        await expect(page.locator('.progress-container')).toBeVisible();
    });

    test('progress stages are visible', async ({ page }) => {
        // Create a job first
        await page.goto('/');

        await page.locator('input[name="jd"]').setInputFiles({
            name: 'jd.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# Test Job'),
        });

        await page.locator('input[name="resume"]').setInputFiles({
            name: 'resume.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# Test Resume'),
        });

        await page.locator('button[type="submit"]').click();
        await expect(page).toHaveURL(/\/jobs\/[a-f0-9-]+/, { timeout: 10000 });

        // Wait for page to stabilize after navigation (use domcontentloaded, not networkidle which blocks on SSE)
        await page.waitForLoadState('domcontentloaded');

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
        // Create a job
        await page.goto('/');

        await page.locator('input[name="jd"]').setInputFiles({
            name: 'jd.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# Test Job'),
        });

        await page.locator('input[name="resume"]').setInputFiles({
            name: 'resume.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# Test Resume'),
        });

        await page.locator('button[type="submit"]').click();
        await expect(page).toHaveURL(/\/jobs\/[a-f0-9-]+/, { timeout: 10000 });

        // Timer should show and increment
        const timer = page.locator('.timer');
        await expect(timer).toBeVisible();

        // Wait a bit and check timer increments
        const initialText = await timer.textContent();
        await page.waitForTimeout(2000);
        const updatedText = await timer.textContent();

        // Timer should have changed (if not complete)
        // Note: This might flake if job completes too fast
        expect(updatedText).not.toBe(initialText);
    });

    test('agent card shows current stage info', async ({ page }) => {
        // Create a job
        await page.goto('/');

        await page.locator('input[name="jd"]').setInputFiles({
            name: 'jd.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# Test Job'),
        });

        await page.locator('input[name="resume"]').setInputFiles({
            name: 'resume.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# Test Resume'),
        });

        await page.locator('button[type="submit"]').click();
        await expect(page).toHaveURL(/\/jobs\/[a-f0-9-]+/, { timeout: 10000 });

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
        // Create a job
        await page.goto('/');

        await page.locator('input[name="jd"]').setInputFiles({
            name: 'jd.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# Test Job'),
        });

        await page.locator('input[name="resume"]').setInputFiles({
            name: 'resume.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# Test Resume'),
        });

        await page.locator('button[type="submit"]').click();
        await expect(page).toHaveURL(/\/jobs\/[a-f0-9-]+/, { timeout: 10000 });

        // Click back link
        await page.locator('.back-link').click();

        // Should be back on upload page
        await expect(page).toHaveURL('/');
    });
});
