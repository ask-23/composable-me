/**
 * hitl-gap-approve-real.spec.ts
 *
 * Opt-in E2E test for HITL Gap Analysis Review with real inputs.
 *
 * Requirements:
 * - REAL_RESUME_PATH: path to local resume file
 * - REAL_JD_PATH: path to local JD markdown file
 *
 * Test skips automatically if env vars are not set.
 *
 * Test flow:
 * 1. Upload JD + resume
 * 2. Submit and wait for "Review Gap Analysis" state
 * 3. Click "Approve & Continue"
 * 4. Assert UI proceeds (no 400 error, review disappears)
 */

import { test, expect } from '@playwright/test';
import { getRealInputPaths } from '../helpers/real-input';

// Check if test should run
const realInputPaths = getRealInputPaths();
const shouldRun = !!realInputPaths;

// Skip entire suite if not configured
test.describe('HITL Gap Analysis Review - Real Input (Opt-in)', () => {
    test.skip(!shouldRun, 'Skipped: REAL_RESUME_PATH and REAL_JD_PATH env vars not set');

    test('can approve gap analysis and workflow proceeds', async ({ page }) => {
        // Safety check (TypeScript narrowing)
        if (!realInputPaths) {
            throw new Error('Test should have been skipped - env vars not set');
        }

        // 1. Navigate to upload page
        await page.goto('/');

        // 2. Upload JD file
        await page.locator('input[name="jd"]').setInputFiles(realInputPaths.jdPath);

        // Wait for file upload to be processed
        await expect(page.locator('.file-item').first()).toBeVisible({ timeout: 5000 });

        // 3. Upload resume file
        await page.locator('input[name="resume"]').setInputFiles(realInputPaths.resumePath);

        // Wait for resume upload to be processed
        await expect(page.locator('.file-item').nth(1)).toBeVisible({ timeout: 5000 });

        // 4. Submit form
        await page.locator('button[type="submit"]').click();

        // 5. Wait for redirect to job page
        await page.waitForURL(/\/jobs\/[a-f0-9-]+/, { timeout: 15000 });

        // 6. Wait for "Review Gap Analysis" state (HITL pause)
        // This could take a while with real LLM calls
        const reviewCard = page.locator('.review-card').first();
        await expect(reviewCard).toBeVisible({ timeout: 300000 }); // 5 minutes max

        // Verify we're in gap analysis review state
        await expect(page.getByRole('heading', { name: /Gap Analysis/i })).toBeVisible();

        // 7. Click "Approve & Continue" button
        const approveButton = page.locator('button', { hasText: /Approve.*Continue/i });
        await expect(approveButton).toBeVisible();
        await approveButton.click();

        // 8. Assert UI proceeds:
        // - Review card should disappear
        await expect(reviewCard).not.toBeVisible({ timeout: 30000 });

        // 9. Assert no 400 error banner appears
        const errorBanner = page.locator('.error-banner');
        // Give it a moment to potentially show an error
        await page.waitForTimeout(2000);
        await expect(errorBanner).not.toBeVisible();

        // 10. Verify workflow continues (either next review state or progress resumes)
        // We should either see:
        // - Another review card (interrogation_review), OR
        // - Progress card showing active state beyond gap_analysis_review
        const hasNextReview = await page.locator('.review-card').isVisible().catch(() => false);
        const hasProgressCard = await page.locator('.progress-card').isVisible().catch(() => false);

        // At least one should be visible (workflow is proceeding)
        expect(hasNextReview || hasProgressCard).toBe(true);
    });

    test('review card shows gap analysis details before approval', async ({ page }) => {
        // Safety check
        if (!realInputPaths) {
            throw new Error('Test should have been skipped - env vars not set');
        }

        // Navigate to upload page
        await page.goto('/');

        // Upload files
        await page.locator('input[name="jd"]').setInputFiles(realInputPaths.jdPath);
        await page.locator('input[name="resume"]').setInputFiles(realInputPaths.resumePath);

        // Submit
        await page.locator('button[type="submit"]').click();

        // Wait for job page
        await page.waitForURL(/\/jobs\/[a-f0-9-]+/, { timeout: 15000 });

        // Wait for review card
        const reviewCard = page.locator('.review-card').first();
        await expect(reviewCard).toBeVisible({ timeout: 300000 });

        // Verify review card contains expected sections
        await expect(reviewCard.getByText(/Match Score/i).or(reviewCard.getByText(/Fit Score/i))).toBeVisible();

        // Check for matches/gaps sections (structure may vary)
        const hasMatchesOrGaps = await reviewCard.getByText(/Match/i).isVisible().catch(() => false) ||
                                  await reviewCard.getByText(/Gap/i).isVisible().catch(() => false);
        expect(hasMatchesOrGaps).toBe(true);

        // Verify approve button is present and enabled
        const approveButton = reviewCard.locator('button', { hasText: /Approve/i });
        await expect(approveButton).toBeVisible();
        await expect(approveButton).toBeEnabled();
    });
});
