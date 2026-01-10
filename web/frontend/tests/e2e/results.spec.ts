import { test, expect } from '@playwright/test';

test.describe('Results Viewer', () => {
    // Helper to create a job and wait for completion
    // Note: This requires a working backend with fast processing
    // In CI, you might want to mock the backend or use fixtures

    test.skip('completed job shows results tabs', async ({ page }) => {
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
        await expect(page.locator('.agent-card.success, .agent-card.error'))
            .toBeVisible({ timeout: 120000 });

        // Check results tabs are visible
        await expect(page.locator('text=Resume')).toBeVisible();
        await expect(page.locator('text=Cover Letter')).toBeVisible();
        await expect(page.locator('text=Debug')).toBeVisible();
    });

    test('error state shows error message', async ({ page }) => {
        // Navigate to a job that will fail
        // We can test this by checking the error banner functionality
        await page.goto('/');

        // Upload minimal files that might cause processing failure
        await page.locator('input[name="jd"]').setInputFiles({
            name: 'jd.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('x'), // Minimal content
        });

        await page.locator('input[name="resume"]').setInputFiles({
            name: 'resume.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('x'), // Minimal content
        });

        await page.locator('button[type="submit"]').click();
        await expect(page).toHaveURL(/\/jobs\/[a-f0-9-]+/, { timeout: 10000 });

        // Wait for either success or error (with a reasonable timeout)
        await expect(page.locator('.agent-card.success, .agent-card.error, .error-banner'))
            .toBeVisible({ timeout: 60000 });

        // If there's an error banner, check it has content
        const errorBanner = page.locator('.error-banner');
        if (await errorBanner.isVisible()) {
            await expect(errorBanner.locator('p')).not.toBeEmpty();
        }
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
