/**
 * API route: GET /api/jobs/[id]/stream
 * Proxies SSE stream from the Litestar backend.
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
    // Fetch SSE stream from backend
    const response = await fetch(`${BACKEND_URL}/api/jobs/${id}/stream`, {
      headers: {
        'Accept': 'text/event-stream',
      },
    });

    if (!response.ok) {
      return new Response(
        JSON.stringify({ message: 'Job not found' }),
        { status: response.status, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Proxy the SSE stream
    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no',
      },
    });

  } catch (error) {
    console.error('Error streaming job:', error);
    return new Response(
      JSON.stringify({ message: 'Failed to stream job. Is the backend running?' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
};
