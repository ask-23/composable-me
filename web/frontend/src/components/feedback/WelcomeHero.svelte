<script lang="ts">
  /**
   * WelcomeHero.svelte - First-time user welcome component
   * Shows a welcoming introduction to Hydra with dismissal option
   */

  const STORAGE_KEY = 'hydra-welcome-dismissed';

  let dismissed = $state(false);

  // Check localStorage on mount
  $effect(() => {
    if (typeof window !== 'undefined') {
      dismissed = localStorage.getItem(STORAGE_KEY) === 'true';
    }
  });

  function handleDismiss() {
    dismissed = true;
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, 'true');
    }
  }
</script>

{#if !dismissed}
  <div class="welcome-hero">
    <button
      class="welcome-dismiss"
      onclick={handleDismiss}
      aria-label="Dismiss welcome message"
      type="button"
    >
      <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
        <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z"/>
      </svg>
    </button>

    <div class="welcome-content">
      <div class="welcome-badge">Welcome to Hydra</div>
      <h2 class="welcome-title">Your AI-Powered Application Assistant</h2>
      <p class="welcome-description">
        Hydra uses a team of 6 specialized AI agents to analyze your job description,
        identify your strengths, and create tailored application materials optimized
        for both ATS systems and human reviewers.
      </p>

      <div class="welcome-steps">
        <div class="step">
          <span class="step-number">1</span>
          <span class="step-text">Upload your job description and resume</span>
        </div>
        <div class="step">
          <span class="step-number">2</span>
          <span class="step-text">Watch the agents collaborate in real-time</span>
        </div>
        <div class="step">
          <span class="step-number">3</span>
          <span class="step-text">Download your tailored documents</span>
        </div>
      </div>
    </div>

    <div class="welcome-pointer">
      <span class="pointer-text">Get started below</span>
      <svg class="pointer-arrow" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 5v14M19 12l-7 7-7-7"/>
      </svg>
    </div>
  </div>
{/if}

<style>
  .welcome-hero {
    position: relative;
    background: linear-gradient(
      135deg,
      rgba(59, 130, 246, 0.12) 0%,
      rgba(147, 51, 234, 0.08) 100%
    );
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: var(--radius);
    padding: 2rem;
    margin-bottom: 2rem;
  }

  .welcome-dismiss {
    position: absolute;
    top: 1rem;
    right: 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    padding: 0;
    background: transparent;
    border: none;
    border-radius: 6px;
    color: var(--color-text-muted);
    cursor: pointer;
    transition: color 0.2s, background 0.2s;
  }

  .welcome-dismiss:hover {
    color: var(--color-text);
    background: rgba(255, 255, 255, 0.1);
  }

  .welcome-content {
    max-width: 600px;
  }

  .welcome-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    background: rgba(59, 130, 246, 0.15);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 999px;
    color: var(--color-primary);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 1rem;
  }

  .welcome-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--color-text);
    margin: 0 0 0.75rem 0;
  }

  .welcome-description {
    color: var(--color-text-muted);
    font-size: 0.95rem;
    line-height: 1.6;
    margin: 0 0 1.5rem 0;
  }

  .welcome-steps {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .step {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .step-number {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    background: var(--color-primary);
    color: white;
    font-size: 0.75rem;
    font-weight: 700;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .step-text {
    color: var(--color-text);
    font-size: 0.875rem;
  }

  .welcome-pointer {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    margin-top: 1.5rem;
    padding-top: 1.5rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }

  .pointer-text {
    color: var(--color-primary);
    font-size: 0.875rem;
    font-weight: 500;
  }

  .pointer-arrow {
    color: var(--color-primary);
    animation: bounce 1.5s ease-in-out infinite;
  }

  @keyframes bounce {
    0%, 100% {
      transform: translateY(0);
    }
    50% {
      transform: translateY(6px);
    }
  }

  /* Responsive */
  @media (max-width: 640px) {
    .welcome-hero {
      padding: 1.5rem;
    }

    .welcome-title {
      font-size: 1.25rem;
    }
  }
</style>
