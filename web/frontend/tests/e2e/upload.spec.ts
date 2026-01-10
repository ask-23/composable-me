import { test, expect } from '@playwright/test';

test.describe('Upload Page', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('page loads with correct title and elements', async ({ page }) => {
        // Check page title
        await expect(page).toHaveTitle(/Upload/);

        // Check main heading
        await expect(page.locator('h1')).toContainText('Generate Application Materials');

        // Check form elements exist
        await expect(page.locator('text=Job Description')).toBeVisible();
        await expect(page.locator('text=Resume')).toBeVisible();
        await expect(page.locator('text=Source Documents')).toBeVisible();

        // Check submit button
        await expect(page.locator('button[type="submit"]')).toContainText('Generate Application');
    });

    test('shows validation error when submitting without files', async ({ page }) => {
        // Click submit without adding files
        await page.locator('button[type="submit"]').click();

        // Should show error message
        await expect(page.locator('.error')).toBeVisible();
        await expect(page.locator('.error')).toContainText('required');
    });

    test('file upload via click works for job description', async ({ page }) => {
        // Create a test file
        const testContent = '# Test Job Description\n\nThis is a test job.';

        // Find the JD file input and upload
        const jdInput = page.locator('input[name="jd"]');
        await jdInput.setInputFiles({
            name: 'test-jd.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from(testContent),
        });

        // Check that file name is displayed
        await expect(page.locator('.file-item')).toContainText('test-jd.md');
    });

    test('file upload via click works for resume', async ({ page }) => {
        // Create a test file
        const testContent = '# Test Resume\n\nExperience: Testing';

        // Find the resume file input and upload
        const resumeInput = page.locator('input[name="resume"]');
        await resumeInput.setInputFiles({
            name: 'test-resume.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from(testContent),
        });

        // Check that file name is displayed
        await expect(page.locator('.file-item')).toContainText('test-resume.md');
    });

    test('can remove uploaded file', async ({ page }) => {
        // Upload a file
        const jdInput = page.locator('input[name="jd"]');
        await jdInput.setInputFiles({
            name: 'test-jd.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# Test'),
        });

        // Verify file is shown
        await expect(page.locator('.file-item')).toContainText('test-jd.md');

        // Click remove button
        await page.locator('.remove-btn').first().click();

        // File should be removed
        await expect(page.locator('.file-item')).not.toBeVisible();
    });

    test('features section is visible', async ({ page }) => {
        // Check features section
        await expect(page.locator('text=What Hydra Does')).toBeVisible();
        await expect(page.locator('text=Gap Analysis')).toBeVisible();
        await expect(page.locator('text=Interview Prep')).toBeVisible();
        await expect(page.locator('text=ATS Optimization')).toBeVisible();
    });

    test('successful form submission shows loading overlay and redirects', async ({ page }) => {
        // Upload JD
        await page.locator('input[name="jd"]').setInputFiles({
            name: 'jd.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# Software Engineer\n\nPython, TypeScript required'),
        });

        // Upload Resume
        await page.locator('input[name="resume"]').setInputFiles({
            name: 'resume.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# John Doe\n\n5 years Python experience'),
        });

        // Submit form
        await page.locator('button[type="submit"]').click();

        // Loading overlay should appear
        await expect(page.locator('.loading-overlay')).toBeVisible();
        await expect(page.locator('#loading-status')).toContainText(/Reading|Uploading/);

        // Wait for redirect to job page (with timeout for API call)
        await expect(page).toHaveURL(/\/jobs\/[a-f0-9-]+/, { timeout: 10000 });
    });
});
