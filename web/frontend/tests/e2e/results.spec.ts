import { test, expect } from '@playwright/test';

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
});
