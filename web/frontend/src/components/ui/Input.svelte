<script lang="ts">
  /**
   * Input.svelte - Accessible text input component
   * Supports labels, error messages, and various states
   */

  interface Props {
    label?: string;
    name: string;
    type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search';
    placeholder?: string;
    value?: string;
    error?: string;
    disabled?: boolean;
    required?: boolean;
    autocomplete?: string;
    oninput?: (event: Event) => void;
    onchange?: (event: Event) => void;
  }

  let {
    label,
    name,
    type = 'text',
    placeholder = '',
    value = $bindable(''),
    error,
    disabled = false,
    required = false,
    autocomplete,
    oninput,
    onchange,
  }: Props = $props();

  let inputId = $derived(`input-${name}`);
  let errorId = $derived(`error-${name}`);
  let hasError = $derived(!!error);
</script>

<div class="input-wrapper">
  {#if label}
    <label for={inputId} class="input-label">
      {label}
      {#if required}
        <span class="required-indicator" aria-hidden="true">*</span>
      {/if}
    </label>
  {/if}

  <input
    id={inputId}
    {name}
    {type}
    {placeholder}
    bind:value
    {disabled}
    {required}
    {autocomplete}
    class="input"
    class:has-error={hasError}
    aria-invalid={hasError}
    aria-describedby={hasError ? errorId : undefined}
    {oninput}
    {onchange}
  />

  {#if error}
    <p id={errorId} class="error-message" role="alert">
      {error}
    </p>
  {/if}
</div>

<style>
  .input-wrapper {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-1);
  }

  .input-label {
    display: block;
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
  }

  .required-indicator {
    color: var(--color-error);
    margin-left: var(--spacing-1);
  }

  .input {
    width: 100%;
    padding: var(--spacing-2) var(--spacing-3);
    font-family: var(--font-family-sans);
    font-size: var(--font-size-base);
    line-height: var(--line-height-normal);
    color: var(--color-text);
    background-color: var(--color-bg);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-base);
    transition:
      border-color var(--transition-fast),
      box-shadow var(--transition-fast);
  }

  .input::placeholder {
    color: var(--color-text-muted);
  }

  .input:hover:not(:disabled) {
    border-color: var(--color-secondary-400);
  }

  .input:focus {
    outline: none;
    border-color: var(--focus-ring-color);
    box-shadow: 0 0 0 var(--focus-ring-width) rgb(59 130 246 / 0.2);
  }

  .input:disabled {
    background-color: var(--color-bg-secondary);
    color: var(--color-text-muted);
    cursor: not-allowed;
  }

  .input.has-error {
    border-color: var(--color-error);
  }

  .input.has-error:focus {
    border-color: var(--color-error);
    box-shadow: 0 0 0 var(--focus-ring-width) rgb(239 68 68 / 0.2);
  }

  .error-message {
    margin: 0;
    font-size: var(--font-size-sm);
    color: var(--color-error);
  }
</style>
