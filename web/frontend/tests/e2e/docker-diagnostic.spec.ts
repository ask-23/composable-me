/**
 * docker-diagnostic.spec.ts
 *
 * Test against the actual Docker-hosted app at localhost:4321
 * This simulates the real user experience.
 */

import { test, expect } from '@playwright/test';

// Override baseURL to use Docker frontend
test.use({ baseURL: 'http://localhost:4321' });

test.describe('Docker App Diagnostic', () => {
    test('simulates real user flow through Docker app', async ({ page }) => {
        test.setTimeout(600000); // 10 minutes

        // 1. Navigate to upload page
        await page.goto('/');
        await page.screenshot({ path: 'test-results/docker-01-upload.png', fullPage: true });

        // 2. Upload test files
        await page.locator('input[name="jd"]').setInputFiles({
            name: 'jd.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# Senior Platform Engineer\n\nRequirements:\n- 5+ years Python\n- AWS expertise\n- Terraform'),
        });

        await page.locator('input[name="resume"]').setInputFiles({
            name: 'resume.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# John Doe\n\n7 years Python, 4 years AWS, 3 years Terraform'),
        });

        // 3. Submit
        await page.locator('button[type="submit"]').click();

        // 4. Wait for job page
        await page.waitForURL(/\/jobs\/[a-f0-9-]+/, { timeout: 15000 });
        const jobUrl = page.url();
        console.log('Docker Job URL:', jobUrl);

        await page.screenshot({ path: 'test-results/docker-02-job-started.png', fullPage: true });

        // 5. Wait for review state and capture screenshots
        console.log('Waiting for review state...');
        for (let i = 0; i < 60; i++) {
            await page.waitForTimeout(5000);

            // Get current state
            const timer = await page.locator('.timer').textContent().catch(() => 'no timer');
            console.log(`[${i * 5}s] Timer: ${timer}`);

            // Check for review card
            const reviewCard = page.locator('.review-card');
            if (await reviewCard.isVisible().catch(() => false)) {
                console.log('Found review card');
                await page.screenshot({ path: 'test-results/docker-03-review.png', fullPage: true });

                // Click approve
                const approveBtn = page.locator('button', { hasText: /Approve/i });
                if (await approveBtn.isVisible().catch(() => false)) {
                    console.log('Clicking Approve...');

                    // Listen for network errors
                    const requestPromise = page.waitForResponse(
                        response => response.url().includes('approve_gap_analysis'),
                        { timeout: 30000 }
                    ).catch(e => {
                        console.log('Network request failed:', e.message);
                        return null;
                    });

                    await approveBtn.click();

                    const response = await requestPromise;
                    if (response) {
                        console.log('Approve response status:', response.status());
                        if (!response.ok()) {
                            const body = await response.text();
                            console.log('Approve error body:', body);
                        }
                    }

                    await page.waitForTimeout(2000);
                    await page.screenshot({ path: 'test-results/docker-04-after-approve.png', fullPage: true });

                    // Check for error
                    const error = page.locator('.error, .error-banner');
                    if (await error.isVisible().catch(() => false)) {
                        const errorText = await error.textContent();
                        console.log('ERROR displayed:', errorText);
                        await page.screenshot({ path: 'test-results/docker-ERROR.png', fullPage: true });
                    }
                }
                break;
            }

            // Check for completion
            const results = page.locator('.results-viewer');
            if (await results.isVisible().catch(() => false)) {
                console.log('Completed');
                await page.screenshot({ path: 'test-results/docker-completed.png', fullPage: true });
                break;
            }

            await page.screenshot({ path: `test-results/docker-wait-${i}.png`, fullPage: true });
        }

        // Final state
        await page.screenshot({ path: 'test-results/docker-99-final.png', fullPage: true });
    });
});
