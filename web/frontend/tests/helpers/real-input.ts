/**
 * real-input.ts
 * Helper for opt-in real-input E2E tests.
 *
 * Safely checks env vars and file existence without logging PII content.
 */

import { existsSync } from 'fs';
import { resolve } from 'path';

export interface RealInputPaths {
    jdPath: string;
    resumePath: string;
}

/**
 * Check if real-input test env vars are set and files exist.
 * Returns null if not configured (test should skip).
 * Throws if configured but files are invalid.
 */
export function getRealInputPaths(): RealInputPaths | null {
    const jdPath = process.env.REAL_JD_PATH;
    const resumePath = process.env.REAL_RESUME_PATH;

    // Not configured - skip test
    if (!jdPath || !resumePath) {
        return null;
    }

    // Resolve to absolute paths
    const absJdPath = resolve(jdPath);
    const absResumePath = resolve(resumePath);

    // Validate files exist
    if (!existsSync(absJdPath)) {
        throw new Error(`REAL_JD_PATH file not found: ${absJdPath}`);
    }
    if (!existsSync(absResumePath)) {
        throw new Error(`REAL_RESUME_PATH file not found: ${absResumePath}`);
    }

    return {
        jdPath: absJdPath,
        resumePath: absResumePath,
    };
}
