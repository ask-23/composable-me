/**
 * HITL (Human-in-the-Loop) API functions for gap analysis approval
 * and interview answer submission.
 */

import type { InterviewAnswer } from '../types';

const BACKEND_URL = import.meta.env.BACKEND_URL || 'http://localhost:8000';

/**
 * Response type for HITL action endpoints that return job_id, status, and message
 */
export type HitlActionResponse = {
  job_id: string;
  status: string;
  message: string;
};

/**
 * Approve or reject gap analysis results and resume workflow.
 *
 * @param jobId - The job ID
 * @param approved - Whether to approve the gap analysis
 * @returns Response with job_id, status, and message
 */
export async function approveGapAnalysis(jobId: string, approved: boolean): Promise<HitlActionResponse> {
  const response = await fetch(`${BACKEND_URL}/api/jobs/${jobId}/approve_gap_analysis`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ approved }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Submit interview answers and resume workflow.
 *
 * @param jobId - The job ID
 * @param answers - Array of interview answers
 * @returns Response with job_id, status, and message
 */
export async function submitInterviewAnswers(
  jobId: string,
  answers: InterviewAnswer[]
): Promise<HitlActionResponse> {
  const response = await fetch(`${BACKEND_URL}/api/jobs/${jobId}/submit_interview_answers`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ answers }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}
