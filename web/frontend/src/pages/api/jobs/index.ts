/**
 * API route: POST /api/jobs
 * Proxies job creation to the Litestar backend.
 */

import type { APIRoute } from 'astro';

const BACKEND_URL = import.meta.env.BACKEND_URL || 'http://localhost:8000';

export const POST: APIRoute = async ({ request }) => {
  try {
    const body = await request.json();

    // Validate required fields
    if (!body.job_description || body.job_description.length < 10) {
      return new Response(
        JSON.stringify({ message: 'Job description is required (min 10 chars)' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    if (!body.resume || body.resume.length < 10) {
      return new Response(
        JSON.stringify({ message: 'Resume is required (min 10 chars)' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Proxy to backend
    const response = await fetch(`${BACKEND_URL}/api/jobs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        job_description: body.job_description,
        resume: body.resume,
        source_documents: body.source_documents || '',
        model: body.model,
        max_audit_retries: body.max_audit_retries ?? 2,
      }),
    });

    const data = await response.json();

    return new Response(JSON.stringify(data), {
      status: response.status,
      headers: { 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('Error creating job:', error);
    return new Response(
      JSON.stringify({ message: 'Failed to create job. Is the backend running?' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
};
