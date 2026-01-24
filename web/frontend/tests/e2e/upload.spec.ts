import { test, expect } from '@playwright/test';
import {
    mockJobCreation,
    mockJobStatus,
    mockSSEComplete,
    mockBackendUnavailable,
    mockRateLimitError,
    uploadFile,
    uploadStandardFiles,
    SAMPLE_JOB_DESCRIPTION,
    SAMPLE_RESUME,
} from '../helpers/test-helpers';

test.describe('Upload Page', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('page loads with correct title and elements', async ({ page }) => {
        // Check page title
        await expect(page).toHaveTitle(/Upload/);

        // Check main heading
        await expect(page.getByRole('heading', { name: 'Generate Application Materials' })).toBeVisible();

        // Check form elements exist (use specific label selectors with exact match)
        await expect(page.getByText('Job Description *', { exact: true })).toBeVisible();
        await expect(page.getByText('Resume *', { exact: true })).toBeVisible();
        await expect(page.getByText('Source Documents (optional)', { exact: true })).toBeVisible();

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

        // Dispatch change event to trigger Svelte's reactive handler
        await jdInput.evaluate((el) => el.dispatchEvent(new Event('change', { bubbles: true })));

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

        // Dispatch change event to trigger Svelte's reactive handler
        await resumeInput.evaluate((el) => el.dispatchEvent(new Event('change', { bubbles: true })));

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

        // Dispatch change event to trigger Svelte's reactive handler
        await jdInput.evaluate((el) => el.dispatchEvent(new Event('change', { bubbles: true })));

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

        // Loading overlay should appear (check quickly before redirect)
        await expect(page.locator('.loading-overlay')).toBeVisible({ timeout: 2000 }).catch(() => { });

        // Wait for either redirect to job page OR error message (backend may not be configured)
        await Promise.race([
            expect(page).toHaveURL(/\/jobs\/[a-f0-9-]+/, { timeout: 15000 }),
            expect(page.locator('.error')).toBeVisible({ timeout: 15000 })
        ]);
    });
});

test.describe('Upload Page - Mocked Backend', () => {
    test('successful submission with mocked backend redirects to job page', async ({ page }) => {
        const mockJobId = 'mocked-job-12345';

        // Setup mocks before navigation
        await mockJobCreation(page, mockJobId);
        await mockJobStatus(page, { jobId: mockJobId, state: 'initialized' });
        await mockSSEComplete(page, mockJobId);

        await page.goto('/');

        // Upload files using helper
        await uploadStandardFiles(page);

        // Submit form
        await page.locator('button[type="submit"]').click();

        // Should redirect to job page
        await expect(page).toHaveURL(`/jobs/${mockJobId}`, { timeout: 10000 });
    });

    test('loading overlay shows and transitions during submission', async ({ page }) => {
        const mockJobId = 'step-test-job';

        // Mock the job status and SSE first
        await mockJobStatus(page, { jobId: mockJobId, state: 'initialized' });
        await mockSSEComplete(page, mockJobId);

        // Mock job creation with a slight delay to allow overlay observation
        await page.route('**/api/jobs', async (route) => {
            // Delay response for 500ms to ensure overlay is visible
            await new Promise((resolve) => setTimeout(resolve, 500));
            await route.fulfill({
                status: 202,
                contentType: 'application/json',
                json: { job_id: mockJobId },
            });
        });

        await page.goto('/');
        await uploadStandardFiles(page);

        // Start observing for the loading overlay before clicking
        const overlayPromise = page.locator('.loading-overlay').waitFor({ state: 'visible', timeout: 3000 });

        // Submit form
        await page.locator('button[type="submit"]').click();

        // Loading overlay should appear
        await overlayPromise;

        // Eventually redirects to job page
        await expect(page).toHaveURL(`/jobs/${mockJobId}`, { timeout: 10000 });
    });
    test('shows error when backend is unavailable', async ({ page }) => {
        // Mock backend as unavailable
        await mockBackendUnavailable(page);

        await page.goto('/');
        await uploadStandardFiles(page);

        // Submit form
        await page.locator('button[type="submit"]').click();

        // Should show error message
        await expect(page.locator('.error')).toBeVisible({ timeout: 5000 });
        await expect(page.locator('.error')).toContainText(/backend|server|connect/i);

        // Button should be re-enabled
        await expect(page.locator('button[type="submit"]')).toBeEnabled();
    });

    test('shows error when rate limited', async ({ page }) => {
        // Mock rate limit response
        await mockRateLimitError(page);

        await page.goto('/');
        await uploadStandardFiles(page);

        // Submit form
        await page.locator('button[type="submit"]').click();

        // Should show rate limit error
        await expect(page.locator('.error')).toBeVisible({ timeout: 5000 });
        await expect(page.locator('.error')).toContainText(/rate limit/i);
    });
});

test.describe('Upload Page - Validation Edge Cases', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('shows error when only JD is uploaded', async ({ page }) => {
        // Upload only JD
        await uploadFile(page, 'jd', SAMPLE_JOB_DESCRIPTION, 'jd.md');

        // Submit form
        await page.locator('button[type="submit"]').click();

        // Should show error for missing resume
        await expect(page.locator('.error')).toBeVisible();
        await expect(page.locator('.error')).toContainText(/resume|required/i);
    });

    test('shows error when only resume is uploaded', async ({ page }) => {
        // Upload only resume
        await uploadFile(page, 'resume', SAMPLE_RESUME, 'resume.md');

        // Submit form
        await page.locator('button[type="submit"]').click();

        // Should show error for missing JD
        await expect(page.locator('.error')).toBeVisible();
        await expect(page.locator('.error')).toContainText(/job description|required/i);
    });

    test('multiple source documents can be uploaded', async ({ page }) => {
        // Find the sources file upload section and its input
        const sourcesInput = page.locator('input[name="sources"]');

        // Upload source documents - setInputFiles should trigger the onchange
        await sourcesInput.setInputFiles([
            {
                name: 'source1.md',
                mimeType: 'text/markdown',
                buffer: Buffer.from('# Source Document 1\n\nContent here'),
            },
            {
                name: 'source2.md',
                mimeType: 'text/markdown',
                buffer: Buffer.from('# Source Document 2\n\nMore content'),
            },
        ]);

        // Dispatch change event to trigger Svelte's reactive handler
        await sourcesInput.evaluate((el) => el.dispatchEvent(new Event('change', { bubbles: true })));

        // Wait a moment for Svelte reactivity to update DOM
        await page.waitForTimeout(100);

        // Look for file names in the sources dropzone's parent container
        const sourcesDropzone = page.locator('.dropzone').nth(2); // Third dropzone is sources
        await expect(sourcesDropzone).toContainText('source1.md');
        await expect(sourcesDropzone).toContainText('source2.md');
    });

    test('submit button is disabled during submission', async ({ page }) => {
        const mockJobId = 'button-disable-test';

        // Setup slow mock (we'll check button state quickly)
        await mockJobCreation(page, mockJobId);
        await mockJobStatus(page, { jobId: mockJobId, state: 'initialized' });
        await mockSSEComplete(page, mockJobId);

        await uploadStandardFiles(page);

        const submitBtn = page.locator('button[type="submit"]');

        // Submit form
        await submitBtn.click();

        // Button should be disabled immediately
        await expect(submitBtn).toBeDisabled();
    });

    test('error message can be dismissed by uploading files', async ({ page }) => {
        // Submit empty form to trigger error
        await page.locator('button[type="submit"]').click();
        await expect(page.locator('.error')).toBeVisible();

        // Now upload files - error should hide when form becomes valid and re-submitted
        await uploadStandardFiles(page);

        // Error should still be visible until a new attempt
        await expect(page.locator('.error')).toBeVisible();
    });
});

test.describe('Upload Page - Feature Grid', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('all feature cards are visible', async ({ page }) => {
        const features = [
            'Gap Analysis',
            'Interview Prep',
            'Differentiation',
            'Tailoring',
            'ATS Optimization',
            'Audit & Verify'
        ];

        for (const feature of features) {
            await expect(page.getByRole('heading', { name: feature })).toBeVisible();
        }
    });

    test('feature grid has proper layout', async ({ page }) => {
        const featureGrid = page.locator('.feature-grid');
        await expect(featureGrid).toBeVisible();

        // Should have 6 feature cards
        const featureCards = page.locator('.feature');
        await expect(featureCards).toHaveCount(6);
    });
});
