<script lang="ts">
  /**
   * FileUpload.svelte - Drag-and-drop file upload component
   * Uses Svelte 5 runes for reactivity
   */

  interface Props {
    label: string;
    name: string;
    accept?: string;
    required?: boolean;
    multiple?: boolean;
    onFilesChange?: (files: File[]) => void;
  }

  let {
    label,
    name,
    accept = '.md,.txt',
    required = false,
    multiple = false,
    onFilesChange,
  }: Props = $props();

  let files = $state<File[]>([]);
  let isDragging = $state(false);
  let error = $state<string | null>(null);
  let inputRef: HTMLInputElement;

  // Derived state
  let hasFiles = $derived(files.length > 0);
  let fileNames = $derived(files.map((f) => f.name).join(', '));

  function handleDragOver(e: DragEvent) {
    e.preventDefault();
    isDragging = true;
  }

  function handleDragLeave(e: DragEvent) {
    e.preventDefault();
    isDragging = false;
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    isDragging = false;

    const droppedFiles = Array.from(e.dataTransfer?.files || []);
    validateAndSetFiles(droppedFiles);
  }

  function handleInputChange(e: Event) {
    const input = e.target as HTMLInputElement;
    const selectedFiles = Array.from(input.files || []);
    validateAndSetFiles(selectedFiles);
  }

  function syncInputFiles() {
    // Sync the component's files state with the hidden input element
    // This ensures FormData correctly reads the files on form submission
    if (inputRef) {
      const dataTransfer = new DataTransfer();
      files.forEach((file) => dataTransfer.items.add(file));
      inputRef.files = dataTransfer.files;
    }
  }

  function validateAndSetFiles(newFiles: File[]) {
    error = null;

    // Validate file types
    const acceptedTypes = accept.split(',').map((t) => t.trim());
    const validFiles = newFiles.filter((file) => {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      return acceptedTypes.some((t) => t === ext || t === '*');
    });

    if (validFiles.length !== newFiles.length) {
      error = `Some files were rejected. Accepted types: ${accept}`;
    }

    if (validFiles.length === 0) {
      return;
    }

    // Set files (replace or append based on multiple)
    files = multiple ? [...files, ...validFiles] : validFiles.slice(0, 1);

    // Sync with the hidden input
    syncInputFiles();

    // Notify parent
    onFilesChange?.(files);
  }

  function removeFile(index: number) {
    files = files.filter((_, i) => i !== index);
    syncInputFiles();
    onFilesChange?.(files);
  }

  function openFilePicker() {
    inputRef?.click();
  }
</script>

<div class="file-upload" class:dragging={isDragging}>
  <label class="label">{label}{required ? ' *' : ''}</label>

  <div
    class="dropzone"
    class:has-files={hasFiles}
    class:required-empty={required && !hasFiles}
    role="button"
    tabindex="0"
    ondragover={handleDragOver}
    ondragleave={handleDragLeave}
    ondrop={handleDrop}
    onclick={openFilePicker}
    onkeydown={(e) => e.key === 'Enter' && openFilePicker()}
  >
    <input
      bind:this={inputRef}
      type="file"
      {name}
      {accept}
      {multiple}
      onchange={handleInputChange}
      class="hidden-input"
    />

    {#if hasFiles}
      <div class="file-list">
        {#each files as file, i}
          <div class="file-item">
            <span class="file-name">{file.name}</span>
            <span class="file-size">({(file.size / 1024).toFixed(1)} KB)</span>
            <button
              type="button"
              class="remove-btn"
              onclick={(e) => {
                e.stopPropagation();
                removeFile(i);
              }}
            >
              &times;
            </button>
          </div>
        {/each}
      </div>
    {:else}
      <div class="placeholder">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
        <p>Drag & drop or click to select</p>
        <p class="hint">Accepts: {accept}</p>
      </div>
    {/if}
  </div>

  {#if error}
    <p class="error-msg">{error}</p>
  {/if}
</div>

<style>
  .file-upload {
    margin-bottom: 1.5rem;
  }

  .label {
    display: block;
    font-weight: 500;
    margin-bottom: 0.5rem;
    color: var(--color-text);
  }

  .dropzone {
    border: 2px dashed var(--color-border);
    border-radius: var(--radius);
    padding: 2rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    background: var(--color-bg);
  }

  .dropzone:hover,
  .dragging .dropzone {
    border-color: var(--color-primary);
    background: rgba(59, 130, 246, 0.05);
  }

  .dropzone.has-files {
    padding: 1rem;
    text-align: left;
  }

  .hidden-input {
    display: none;
  }

  .placeholder {
    color: var(--color-text-muted);
  }

  .placeholder svg {
    margin-bottom: 0.5rem;
    opacity: 0.5;
  }

  .placeholder p {
    margin: 0.25rem 0;
  }

  .hint {
    font-size: 0.875rem;
    opacity: 0.7;
  }

  .file-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .file-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: var(--color-bg-secondary);
    padding: 0.5rem 0.75rem;
    border-radius: calc(var(--radius) / 2);
  }

  .file-name {
    font-weight: 500;
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .file-size {
    color: var(--color-text-muted);
    font-size: 0.875rem;
  }

  .remove-btn {
    background: transparent;
    border: none;
    color: var(--color-text-muted);
    font-size: 1.25rem;
    padding: 0 0.25rem;
    cursor: pointer;
    line-height: 1;
  }

  .remove-btn:hover {
    color: var(--color-error);
  }

  .error-msg {
    color: var(--color-error);
    font-size: 0.875rem;
    margin-top: 0.5rem;
  }
</style>
