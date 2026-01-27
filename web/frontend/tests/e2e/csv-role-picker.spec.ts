import { test, expect, Page } from '@playwright/test';
import { mockJobCreation } from '../helpers/test-helpers';

/**
 * Upload a file with Svelte 5 event handling.
 * Clicks the dropzone first to ensure Svelte's event handlers are connected,
 * then triggers the change event via Svelte 5's internal handler.
 */
async function uploadFileWithSvelte5(
    page: Page,
    inputName: string,
    content: string,
    filename: string,
    mimeType: string
): Promise<void> {
    const input = page.locator(`input[name="${inputName}"]`);
    const dropzone = input.locator('xpath=ancestor::div[contains(@class, "dropzone")]');

    // Click the dropzone first to ensure Svelte's event handlers are connected
    await dropzone.click();
    await page.waitForTimeout(50);

    // Set the files
    await input.setInputFiles({
        name: filename,
        mimeType: mimeType,
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
}

/**
 * Upload a CSV file to the JD input.
 */
async function uploadCSVFile(page: Page, csvContent: string, filename: string = 'roles.csv'): Promise<void> {
    await uploadFileWithSvelte5(page, 'jd', csvContent, filename, 'text/csv');
}

/**
 * Upload a markdown file to a specified input.
 */
async function uploadMDFile(page: Page, inputName: string, content: string, filename: string): Promise<void> {
    await uploadFileWithSvelte5(page, inputName, content, filename, 'text/markdown');
}

test.describe('CSV Role Picker', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('shows CSV hint on upload page', async ({ page }) => {
        const hint = page.locator('.csv-hint');
        await expect(hint).toBeVisible();
        await expect(hint).toContainText('CSV');
    });

    test('JD dropzone accepts .csv files', async ({ page }) => {
        const jdDropzone = page.locator('.dropzone').first();
        await expect(jdDropzone).toContainText('Drag & drop');

        // Check accept attribute includes .csv
        const fileInput = page.locator('input[name="jd"]');
        const accept = await fileInput.getAttribute('accept');
        expect(accept).toContain('.csv');
    });

    test('uploading CSV opens role picker modal', async ({ page }) => {
        // Create a mock CSV file
        const csvContent = `Company,Role,Location,Employment Type,Summary,Salary,Link
Acme Corp,Senior Engineer,Remote,Full-time,Lead engineering efforts for platform team,150k-200k,https://acme.com/jobs/1
Widget Inc,Staff Developer,Hybrid,Full-time,Architect scalable systems,180k-220k,https://widget.com/jobs/2
TechCo,Principal Engineer,Onsite,Contract,Drive technical excellence,200k-250k,https://techco.com/jobs/3`;

        // Upload CSV via file input
        await uploadCSVFile(page, csvContent);

        // Wait for role picker modal
        const modal = page.locator('.modal');
        await expect(modal).toBeVisible({ timeout: 5000 });
        await expect(modal).toContainText('Select a Role');
        await expect(modal).toContainText('3 roles');
    });

    test('role picker shows all roles from CSV', async ({ page }) => {
        const csvContent = `Company,Role,Location,Employment Type,Summary,Salary,Link
Acme Corp,Senior Engineer,Remote,Full-time,Lead engineering efforts,150k-200k,https://acme.com/jobs/1
Widget Inc,Staff Developer,Hybrid,Full-time,Architect systems,180k-220k,https://widget.com/jobs/2`;

        await uploadCSVFile(page, csvContent);

        const modal = page.locator('.modal');
        await expect(modal).toBeVisible();

        // Check both roles are visible
        await expect(modal.locator('.role-card')).toHaveCount(2);
        await expect(modal).toContainText('Acme Corp');
        await expect(modal).toContainText('Widget Inc');
        await expect(modal).toContainText('Senior Engineer');
        await expect(modal).toContainText('Staff Developer');
    });

    test('selecting role closes modal and shows banner', async ({ page }) => {
        const csvContent = `Company,Role,Location,Employment Type,Summary,Salary,Link
Acme Corp,Senior Engineer,Remote,Full-time,Lead engineering efforts for platform team,150k-200k,https://acme.com/jobs/1`;

        // Upload CSV via file input
        await uploadCSVFile(page, csvContent);

        const modal = page.locator('.modal');
        await expect(modal).toBeVisible();

        // Click on the role
        await modal.locator('.role-card').first().click();

        // Modal should close
        await expect(modal).not.toBeVisible();

        // Banner should appear
        const banner = page.locator('.selected-role-banner');
        await expect(banner).toBeVisible();
        await expect(banner).toContainText('Acme Corp');
        await expect(banner).toContainText('Senior Engineer');
    });

    test('can change selected role', async ({ page }) => {
        const csvContent = `Company,Role,Location,Employment Type,Summary,Salary,Link
Acme Corp,Senior Engineer,Remote,Full-time,Lead engineering efforts,150k-200k,https://acme.com/jobs/1`;

        await uploadCSVFile(page, csvContent);

        const modal = page.locator('.modal');
        await expect(modal).toBeVisible();
        await modal.locator('.role-card').first().click();

        // Banner should appear
        const banner = page.locator('.selected-role-banner');
        await expect(banner).toBeVisible();

        // Click change button
        await banner.locator('.change-btn').click();

        // Banner should disappear
        await expect(banner).not.toBeVisible();

        // JD dropzone should be visible again
        const jdDropzone = page.locator('.dropzone').first();
        await expect(jdDropzone).toBeVisible();
    });

    test('cancel button closes role picker', async ({ page }) => {
        const csvContent = `Company,Role,Location,Employment Type,Summary,Salary,Link
Acme Corp,Senior Engineer,Remote,Full-time,Lead engineering efforts,150k-200k,https://acme.com/jobs/1`;

        await uploadCSVFile(page, csvContent);

        const modal = page.locator('.modal');
        await expect(modal).toBeVisible();

        // Click cancel
        await modal.locator('.cancel-btn').click();

        // Modal should close
        await expect(modal).not.toBeVisible();

        // Should not have selected role banner
        await expect(page.locator('.selected-role-banner')).not.toBeVisible();
    });

    test('escape key closes role picker', async ({ page }) => {
        const csvContent = `Company,Role,Location,Employment Type,Summary,Salary,Link
Acme Corp,Senior Engineer,Remote,Full-time,Lead engineering efforts,150k-200k,https://acme.com/jobs/1`;

        await uploadCSVFile(page, csvContent);

        const modal = page.locator('.modal');
        await expect(modal).toBeVisible();

        // Press Escape
        await page.keyboard.press('Escape');

        // Modal should close
        await expect(modal).not.toBeVisible();
    });

    test('search filters roles in picker', async ({ page }) => {
        const csvContent = `Company,Role,Location,Employment Type,Summary,Salary,Link
Acme Corp,Senior Engineer,Remote,Full-time,Lead engineering efforts,150k-200k,https://acme.com/jobs/1
Widget Inc,Staff Developer,Hybrid,Full-time,Architect systems,180k-220k,https://widget.com/jobs/2
TechCo,Principal Engineer,Onsite,Contract,Drive excellence,200k-250k,https://techco.com/jobs/3`;

        await uploadCSVFile(page, csvContent);

        const modal = page.locator('.modal');
        await expect(modal).toBeVisible();
        await expect(modal.locator('.role-card')).toHaveCount(3);

        // Search for Widget
        await modal.locator('.search-input').fill('Widget');

        // Should only show one role
        await expect(modal.locator('.role-card')).toHaveCount(1);
        await expect(modal).toContainText('Widget Inc');
    });

    test('form submits with selected role', async ({ page }) => {
        // Mock the API
        await mockJobCreation(page, 'test-csv-job-123');

        const csvContent = `Company,Role,Location,Employment Type,Summary,Salary,Link
Acme Corp,Senior Engineer,Remote,Full-time,Lead engineering efforts for platform team with focus on scalability,150k-200k,https://acme.com/jobs/1`;

        // Upload CSV and select role
        await uploadCSVFile(page, csvContent);

        const modal = page.locator('.modal');
        await expect(modal).toBeVisible({ timeout: 5000 });
        await modal.locator('.role-card').first().click();

        // Upload resume
        await uploadMDFile(page, 'resume', '# My Resume\n\nExperienced engineer...', 'resume.md');

        // Submit form
        await page.click('#submit-btn');

        // Should redirect to job page
        await expect(page).toHaveURL(/\/jobs\/test-csv-job-123/);
    });

    test('regular .md file does not trigger role picker', async ({ page }) => {
        await uploadMDFile(page, 'jd', '# Senior Engineer\n\nWe are looking for...', 'job-description.md');

        // Modal should NOT appear for .md files
        const modal = page.locator('.modal');
        await expect(modal).not.toBeVisible();

        // No role banner should appear
        await expect(page.locator('.selected-role-banner')).not.toBeVisible();

        // The dropzone should still be visible (UploadForm manages jdContent internally)
        await expect(page.locator('.dropzone').first()).toBeVisible();
    });
});
