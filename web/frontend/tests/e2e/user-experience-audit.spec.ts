/**
 * user-experience-audit.spec.ts
 *
 * Comprehensive test to capture the ACTUAL user experience through the entire
 * Hydra workflow. This test documents every issue visible to the user.
 *
 * Issues to capture:
 * 1. "No questions generated for interview" - happens every time
 * 2. No results shown at end - just "Results will appear here..."
 * 3. "Audit failed" followed by "Applying audit fixes" - confusing
 * 4. "Returning documents with REJECTED status" - but nothing rejected visible
 * 5. "Executing Executive Synthesis" - no output shown
 */

import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

// Test against actual Docker app
test.use({ baseURL: 'http://localhost:4321' });

// Ensure test-results directory exists
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const resultsDir = path.join(__dirname, '../../test-results/user-audit');

test.describe('User Experience Audit', () => {
    test.beforeAll(() => {
        if (!fs.existsSync(resultsDir)) {
            fs.mkdirSync(resultsDir, { recursive: true });
        }
    });

    test('complete workflow capturing all user-visible issues', async ({ page }) => {
        // 10 minute timeout for full LLM workflow
        test.setTimeout(600000);

        const issues: string[] = [];
        const log = (msg: string) => {
            const timestamp = new Date().toISOString();
            console.log(`[${timestamp}] ${msg}`);
        };

        // Capture console messages from the page
        const consoleLogs: string[] = [];
        page.on('console', msg => {
            consoleLogs.push(`[${msg.type()}] ${msg.text()}`);
        });

        // Track API responses
        const apiResponses: { url: string; status: number; body?: string }[] = [];
        page.on('response', async response => {
            if (response.url().includes('/api/')) {
                const entry: { url: string; status: number; body?: string } = {
                    url: response.url(),
                    status: response.status()
                };
                try {
                    if (response.headers()['content-type']?.includes('application/json')) {
                        entry.body = await response.text();
                    }
                } catch (e) {
                    // SSE or streaming response
                }
                apiResponses.push(entry);
            }
        });

        // ========== STEP 1: Upload Page ==========
        log('STEP 1: Navigate to upload page');
        await page.goto('/');
        await page.screenshot({ path: `${resultsDir}/01-upload-page.png`, fullPage: true });

        // ========== STEP 2: Upload JD and Resume ==========
        log('STEP 2: Upload JD and Resume');

        // Use realistic test data
        const jdContent = `# Senior Platform Engineer

## About the Role
We're looking for an experienced Platform Engineer to join our infrastructure team.

## Requirements
- 5+ years of Python development experience
- Strong AWS expertise (EC2, S3, Lambda, ECS)
- Terraform/Infrastructure as Code experience
- CI/CD pipeline design and management (GitHub Actions, Jenkins)
- Container orchestration (Docker, Kubernetes)
- Experience with observability tools (Prometheus, Grafana, DataDog)

## Nice to Have
- Go programming experience
- Service mesh experience (Istio, Linkerd)
- Security certifications (AWS SAA, CKA)
`;

        const resumeContent = `# John Doe - Platform Engineer

## Summary
Platform engineer with 7 years of experience building scalable cloud infrastructure.

## Experience

### Senior Platform Engineer | TechCorp Inc | 2020-Present
- Led migration of 50+ microservices to Kubernetes
- Implemented GitOps workflows using ArgoCD
- Reduced infrastructure costs by 40% through optimization
- Built self-service developer platform

### Platform Engineer | StartupXYZ | 2017-2020
- Managed AWS infrastructure for 100k+ daily users
- Implemented Terraform modules for infrastructure provisioning
- Set up CI/CD pipelines with GitHub Actions

## Skills
- Languages: Python (7 years), Go (3 years), Bash
- Cloud: AWS (5 years), GCP (2 years)
- IaC: Terraform (4 years), CloudFormation
- Containers: Docker, Kubernetes, ECS
- CI/CD: GitHub Actions, Jenkins, CircleCI
- Observability: Prometheus, Grafana, ELK Stack
`;

        await page.locator('input[name="jd"]').setInputFiles({
            name: 'senior-platform-engineer.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from(jdContent),
        });

        await page.locator('input[name="resume"]').setInputFiles({
            name: 'john-doe-resume.md',
            mimeType: 'text/markdown',
            buffer: Buffer.from(resumeContent),
        });

        await page.screenshot({ path: `${resultsDir}/02-files-uploaded.png`, fullPage: true });

        // ========== STEP 3: Submit ==========
        log('STEP 3: Submit form');
        await page.locator('button[type="submit"]').click();

        // Wait for redirect to job page
        await page.waitForURL(/\/jobs\/[a-f0-9-]+/, { timeout: 15000 });
        const jobUrl = page.url();
        const jobId = jobUrl.split('/').pop();
        log(`Job created: ${jobId}`);

        await page.waitForTimeout(2000);
        await page.screenshot({ path: `${resultsDir}/03-job-started.png`, fullPage: true });

        // ========== STEP 4: Monitor workflow stages ==========
        log('STEP 4: Monitoring workflow stages');

        const stageTimestamps: { stage: string; time: string; screenshot: string }[] = [];
        let screenshotCounter = 4;
        let lastStage = '';
        let reviewApproved = false;
        let workflowComplete = false;

        for (let i = 0; i < 120; i++) { // Up to 10 minutes
            await page.waitForTimeout(5000);

            // Get current stage
            const stageLabel = await page.locator('.stage-label').textContent().catch(() => 'unknown');
            const timer = await page.locator('.timer').textContent().catch(() => 'no timer');

            // Check if stage changed
            if (stageLabel !== lastStage) {
                screenshotCounter++;
                const screenshotPath = `${resultsDir}/${String(screenshotCounter).padStart(2, '0')}-stage-${stageLabel?.replace(/\s+/g, '-').toLowerCase() || 'unknown'}.png`;
                await page.screenshot({ path: screenshotPath, fullPage: true });

                stageTimestamps.push({
                    stage: stageLabel || 'unknown',
                    time: timer || 'unknown',
                    screenshot: screenshotPath
                });

                log(`Stage changed: ${stageLabel} (Timer: ${timer})`);
                lastStage = stageLabel || '';
            }

            // Check for review card (HITL pause)
            const reviewCard = page.locator('.review-card');
            if (await reviewCard.isVisible().catch(() => false)) {
                if (!reviewApproved) {
                    screenshotCounter++;
                    await page.screenshot({
                        path: `${resultsDir}/${String(screenshotCounter).padStart(2, '0')}-hitl-review.png`,
                        fullPage: true
                    });

                    log('HITL Review card visible - clicking Approve');

                    // Get the fit score
                    const fitScore = await page.locator('.score-value').textContent().catch(() => 'N/A');
                    log(`Fit Score displayed: ${fitScore}`);

                    // Get matches/gaps/adjacent
                    const matches = await page.locator('.column:has(h3:has-text("Matches")) li').allTextContents().catch(() => []);
                    const gaps = await page.locator('.column:has(h3:has-text("Gaps")) li').allTextContents().catch(() => []);
                    const adjacent = await page.locator('.column:has(h3:has-text("Adjacent")) li').allTextContents().catch(() => []);

                    log(`Matches: ${matches.length}, Gaps: ${gaps.length}, Adjacent: ${adjacent.length}`);

                    if (matches.length === 0 && gaps.length === 0 && adjacent.length === 0) {
                        issues.push('ISSUE: Gap analysis review shows no matches, gaps, or adjacent skills');
                    }

                    // Click approve
                    const approveBtn = page.locator('button', { hasText: /Approve/i });
                    if (await approveBtn.isVisible()) {
                        await approveBtn.click();
                        reviewApproved = true;
                        await page.waitForTimeout(2000);

                        screenshotCounter++;
                        await page.screenshot({
                            path: `${resultsDir}/${String(screenshotCounter).padStart(2, '0')}-after-approve.png`,
                            fullPage: true
                        });
                    }
                }
            }

            // Check for results viewer (workflow complete)
            const resultsViewer = page.locator('.results-viewer');
            if (await resultsViewer.isVisible().catch(() => false)) {
                log('Results viewer is visible');
                workflowComplete = true;

                screenshotCounter++;
                await page.screenshot({
                    path: `${resultsDir}/${String(screenshotCounter).padStart(2, '0')}-results-visible.png`,
                    fullPage: true
                });

                // Check what's actually in the results
                const resultsContent = await resultsViewer.textContent().catch(() => '');
                log(`Results content length: ${resultsContent?.length || 0} chars`);

                if (resultsContent?.includes('Results will appear here')) {
                    issues.push('ISSUE: Results viewer shows placeholder text instead of actual results');
                }

                // Check for TLDR hero
                const tldrHero = page.locator('.tldr-hero');
                if (await tldrHero.isVisible().catch(() => false)) {
                    const tldrText = await tldrHero.textContent().catch(() => '');
                    log(`TLDR Hero content: ${tldrText?.substring(0, 200)}...`);
                } else {
                    issues.push('ISSUE: TLDR Hero section not visible in results');
                }

                // Check tabs
                const tabs = await page.locator('.tab').allTextContents().catch(() => []);
                log(`Available tabs: ${tabs.join(', ')}`);

                // Try to view each tab
                for (const tabName of ['Executive', 'Documents', 'Debug']) {
                    const tab = page.locator('.tab', { hasText: tabName });
                    if (await tab.isVisible().catch(() => false)) {
                        await tab.click();
                        await page.waitForTimeout(500);

                        screenshotCounter++;
                        await page.screenshot({
                            path: `${resultsDir}/${String(screenshotCounter).padStart(2, '0')}-tab-${tabName.toLowerCase()}.png`,
                            fullPage: true
                        });

                        // Check for empty content
                        const tabContent = await page.locator('.tab-content, .results-content').textContent().catch(() => '');
                        if (!tabContent || tabContent.trim().length < 50) {
                            issues.push(`ISSUE: ${tabName} tab appears empty or has minimal content`);
                        }
                    }
                }

                break;
            }

            // Check for error messages
            const errorBanner = page.locator('.error-banner, .error');
            if (await errorBanner.isVisible().catch(() => false)) {
                const errorText = await errorBanner.textContent();
                log(`ERROR: ${errorText}`);
                issues.push(`ISSUE: Error displayed: ${errorText}`);

                screenshotCounter++;
                await page.screenshot({
                    path: `${resultsDir}/${String(screenshotCounter).padStart(2, '0')}-error.png`,
                    fullPage: true
                });
            }

            // Log progress every 30 seconds
            if (i % 6 === 0) {
                log(`Still waiting... Stage: ${stageLabel}, Timer: ${timer}`);
            }
        }

        // ========== STEP 5: Final state capture ==========
        log('STEP 5: Capturing final state');

        screenshotCounter++;
        await page.screenshot({
            path: `${resultsDir}/${String(screenshotCounter).padStart(2, '0')}-final-state.png`,
            fullPage: true
        });

        // Get final job state from API
        try {
            const jobResponse = await page.request.get(`http://localhost:8000/api/jobs/${jobId}`);
            const jobData = await jobResponse.json();
            log(`Final job state: ${jobData.state}`);
            log(`Job has results: ${!!jobData.results}`);

            if (jobData.results) {
                const resultsKeys = Object.keys(jobData.results);
                log(`Results keys: ${resultsKeys.join(', ')}`);

                // Check for executive synthesis
                if (!jobData.results.executive_synthesis && !jobData.results.executive_summary) {
                    issues.push('ISSUE: No executive synthesis in job results');
                }

                // Check for tailored documents
                if (!jobData.results.tailored_resume && !jobData.results.documents) {
                    issues.push('ISSUE: No tailored documents in job results');
                }
            } else {
                issues.push('ISSUE: Job completed but results object is empty/missing');
            }
        } catch (e) {
            log(`Failed to fetch job state: ${e}`);
        }

        // ========== STEP 6: Write audit report ==========
        log('STEP 6: Writing audit report');

        const reportContent = `# User Experience Audit Report
Generated: ${new Date().toISOString()}
Job ID: ${jobId}

## Workflow Timeline
${stageTimestamps.map(s => `- ${s.stage}: ${s.time}`).join('\n')}

## Issues Identified
${issues.length > 0 ? issues.map((issue, i) => `${i + 1}. ${issue}`).join('\n') : 'No issues captured (review screenshots manually)'}

## Console Logs (last 50)
\`\`\`
${consoleLogs.slice(-50).join('\n')}
\`\`\`

## API Responses
${apiResponses.filter(r => r.url.includes('jobs')).map(r => `- ${r.url}: ${r.status}`).join('\n')}

## Screenshots Captured
${fs.readdirSync(resultsDir).filter(f => f.endsWith('.png')).sort().map(f => `- ${f}`).join('\n')}
`;

        fs.writeFileSync(`${resultsDir}/audit-report.md`, reportContent);
        log('Audit report written to test-results/user-audit/audit-report.md');

        // Log all issues at the end
        console.log('\n========== ISSUES SUMMARY ==========');
        if (issues.length > 0) {
            issues.forEach((issue, i) => console.log(`${i + 1}. ${issue}`));
        } else {
            console.log('No programmatic issues captured - review screenshots manually');
        }
        console.log('=====================================\n');

        // Test assertions
        expect(workflowComplete || reviewApproved).toBeTruthy();
    });
});
