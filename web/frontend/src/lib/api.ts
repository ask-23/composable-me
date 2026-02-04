/**
 * API client for communicating with the Hydra backend.
 */

import type { CreateJobRequest, CreateJobResponse, Job } from './types';

const BACKEND_URL = import.meta.env.BACKEND_URL || 'http://localhost:8000';

/**
 * Create a new job.
 */
export async function createJob(request: CreateJobRequest): Promise<CreateJobResponse> {
  const response = await fetch(`${BACKEND_URL}/api/jobs`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Get job status and results.
 */
export async function getJob(jobId: string): Promise<Job> {
  const response = await fetch(`${BACKEND_URL}/api/jobs/${jobId}`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Job not found');
    }
    throw new Error(`HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Create an EventSource for streaming job progress.
 */
export function createJobStream(jobId: string): EventSource {
  return new EventSource(`${BACKEND_URL}/api/jobs/${jobId}/stream`);
}
