/**
 * full-workflow-diagnostic.spec.ts
 *
 * Diagnostic test to capture the full user experience including:
 * - Timer display
 * - Fit Score display
 * - Debug tab expandability
 * - Error messages
 * - HITL flow
 */

import { test, expect } from '@playwright/test';

test.describe('Full Workflow Diagnostic', () => {
    test('captures complete user experience through workflow', async ({ page }) => {
        // Increase timeout for LLM processing
        test.setTimeout(600000); // 10 minutes

        // 1. Navigate to upload page
        await page.goto('/');
        await page.screenshot({ path: 'test-results/01-upload-page.png', fullPage: true });

        // 2. Upload test files
        await page.locator('input[name="jd"]').setInputFiles({
            name: 'jd.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# Senior Platform Engineer\n\nRequirements:\n- 5+ years Python experience\n- AWS expertise (EC2, S3, Lambda)\n- Terraform/IaC experience\n- CI/CD pipeline management'),
        });

        await page.locator('input[name="resume"]').setInputFiles({
            name: 'resume.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from('# John Doe - Platform Engineer\n\n## Experience\n- 7 years Python development\n- 4 years AWS cloud infrastructure\n- 3 years Terraform automation\n- Jenkins and GitHub Actions CI/CD'),
        });

        await page.screenshot({ path: 'test-results/02-files-uploaded.png', fullPage: true });

        // 3. Submit form
        await page.locator('button[type="submit"]').click();

        // 4. Wait for redirect to job page
        await page.waitForURL(/\/jobs\/[a-f0-9-]+/, { timeout: 15000 });
        const jobUrl = page.url();
        console.log('Job URL:', jobUrl);

        // 5. Capture initial job page state
        await page.waitForTimeout(2000);
        await page.screenshot({ path: 'test-results/03-job-page-initial.png', fullPage: true });

        // 6. Wait for gap analysis review state
        console.log('Waiting for gap analysis review...');
        let foundReview = false;
        for (let i = 0; i < 60; i++) {
            await page.waitForTimeout(5000);

            // Capture current state
            const stateText = await page.locator('.stage-label').textContent().catch(() => 'unknown');
            const timerText = await page.locator('.timer').textContent().catch(() => 'no timer');
            console.log(`[${i * 5}s] State: ${stateText}, Timer: ${timerText}`);

            await page.screenshot({ path: `test-results/04-waiting-${i}.png`, fullPage: true });

            // Check for review card
            const reviewCard = page.locator('.review-card');
            if (await reviewCard.isVisible().catch(() => false)) {
                console.log('Found review card!');
                await page.screenshot({ path: 'test-results/05-gap-analysis-review.png', fullPage: true });
                foundReview = true;
                break;
            }

            // Check for errors
            const errorBanner = page.locator('.error-banner, .error');
            if (await errorBanner.isVisible().catch(() => false)) {
                const errorText = await errorBanner.textContent();
                console.log('ERROR detected:', errorText);
                await page.screenshot({ path: 'test-results/ERROR-detected.png', fullPage: true });
            }

            // Check if completed already
            const completed = page.locator('.results-viewer');
            if (await completed.isVisible().catch(() => false)) {
                console.log('Workflow completed without review pause');
                await page.screenshot({ path: 'test-results/05-completed-no-pause.png', fullPage: true });
                break;
            }
        }

        if (!foundReview) {
            console.log('Did not find review card, checking final state');
            await page.screenshot({ path: 'test-results/05-final-no-review.png', fullPage: true });
        }

        // 7. If found review, click approve
        const approveBtn = page.locator('button', { hasText: /Approve.*Continue/i });
        if (await approveBtn.isVisible().catch(() => false)) {
            console.log('Clicking Approve & Continue...');
            await approveBtn.click();
            await page.waitForTimeout(3000);
            await page.screenshot({ path: 'test-results/06-after-approve.png', fullPage: true });

            // Check for error after approve
            const errorAfter = page.locator('.error-banner, .error');
            if (await errorAfter.isVisible().catch(() => false)) {
                const errorText = await errorAfter.textContent();
                console.log('ERROR after approve:', errorText);
                await page.screenshot({ path: 'test-results/ERROR-after-approve.png', fullPage: true });
            }
        }

        // 8. Wait for completion (with periodic screenshots)
        console.log('Waiting for workflow completion...');
        for (let i = 0; i < 60; i++) {
            await page.waitForTimeout(5000);

            const resultsViewer = page.locator('.results-viewer');
            if (await resultsViewer.isVisible().catch(() => false)) {
                console.log('Workflow completed!');
                await page.screenshot({ path: 'test-results/07-completed.png', fullPage: true });

                // 9. Capture all the key UI elements

                // Check timer
                const timer = page.locator('.timer');
                if (await timer.isVisible().catch(() => false)) {
                    const timerValue = await timer.textContent();
                    console.log('Final timer value:', timerValue);
                }

                // Check fit score
                const fitScore = page.locator('.fit-score, .match-score');
                if (await fitScore.isVisible().catch(() => false)) {
                    const scoreValue = await fitScore.textContent();
                    console.log('Fit score:', scoreValue);
                }

                // Check TLDR hero
                const tldrHero = page.locator('.tldr-hero');
                if (await tldrHero.isVisible().catch(() => false)) {
                    await page.screenshot({ path: 'test-results/08-tldr-hero.png' });
                }

                // 10. Click Debug tab and check expandability
                const debugTab = page.locator('.tab', { hasText: 'Debug' });
                if (await debugTab.isVisible().catch(() => false)) {
                    await debugTab.click();
                    await page.waitForTimeout(500);
                    await page.screenshot({ path: 'test-results/09-debug-tab.png', fullPage: true });

                    // Try to expand a debug section
                    const debugSection = page.locator('.debug-section').first();
                    if (await debugSection.isVisible().catch(() => false)) {
                        const summary = debugSection.locator('summary');
                        if (await summary.isVisible().catch(() => false)) {
                            await summary.click();
                            await page.waitForTimeout(500);
                            await page.screenshot({ path: 'test-results/10-debug-expanded.png', fullPage: true });

                            // Check if content is visible
                            const pre = debugSection.locator('pre');
                            const preVisible = await pre.isVisible().catch(() => false);
                            console.log('Debug section pre content visible:', preVisible);
                        }
                    }
                }

                // 11. Check action items / next steps
                const actionItems = page.locator('.action-items');
                if (await actionItems.isVisible().catch(() => false)) {
                    const items = await actionItems.locator('li').allTextContents();
                    console.log('Action items:', items);
                }

                break;
            }

            // Check for interrogation review
            const interrReview = page.locator('.review-card');
            if (await interrReview.isVisible().catch(() => false)) {
                console.log('Found interrogation review, submitting answers...');
                await page.screenshot({ path: `test-results/interrogation-review-${i}.png`, fullPage: true });

                // Try to submit answers
                const submitBtn = page.locator('button', { hasText: /Submit|Continue/i });
                if (await submitBtn.isVisible().catch(() => false)) {
                    // Fill in any text inputs if present
                    const textInputs = page.locator('.review-card textarea, .review-card input[type="text"]');
                    const inputCount = await textInputs.count();
                    for (let j = 0; j < inputCount; j++) {
                        await textInputs.nth(j).fill('Test answer for interview question');
                    }
                    await submitBtn.click();
                    await page.waitForTimeout(3000);
                }
            }
        }

        // Final screenshot
        await page.screenshot({ path: 'test-results/99-final-state.png', fullPage: true });
        console.log('Test complete - check test-results/ folder for screenshots');
    });
});
