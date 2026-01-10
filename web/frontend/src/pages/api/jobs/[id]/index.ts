/**
 * API route: GET /api/jobs/[id]
 * Proxies job status requests to the Litestar backend.
 */

import type { APIRoute } from 'astro';

const BACKEND_URL = import.meta.env.BACKEND_URL || 'http://localhost:8000';

export const GET: APIRoute = async ({ params }) => {
  const { id } = params;

  if (!id) {
    return new Response(
      JSON.stringify({ message: 'Job ID is required' }),
      { status: 400, headers: { 'Content-Type': 'application/json' } }
    );
  }

  try {
    const response = await fetch(`${BACKEND_URL}/api/jobs/${id}`);
    const data = await response.json();

    return new Response(JSON.stringify(data), {
      status: response.status,
      headers: { 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('Error fetching job:', error);
    return new Response(
      JSON.stringify({ message: 'Failed to fetch job. Is the backend running?' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
};
