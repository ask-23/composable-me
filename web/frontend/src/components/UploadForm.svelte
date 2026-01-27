<script lang="ts">
    /**
     * UploadForm.svelte - Form wrapper with CSV role picker integration
     * Handles file uploads, CSV parsing, role selection, and form submission
     */
    import FileUpload from "./FileUpload.svelte";
    import RolePicker from "./RolePicker.svelte";
    import {
        parseRoleCSV,
        roleToJobDescription,
        type RoleEntry,
    } from "../lib/csv-utils";
    import { parseJobFeedJSON } from "../lib/json-utils";

    // State
    let jdFiles = $state<File[]>([]);
    let resumeFiles = $state<File[]>([]);
    let sourceFiles = $state<File[]>([]);

    let showRolePicker = $state(false);
    let detectedRoles = $state<RoleEntry[]>([]);
    let selectedRole = $state<RoleEntry | null>(null);
    let jdContent = $state<string | null>(null);

    let isSubmitting = $state(false);
    let error = $state<string | null>(null);
    let loadingStep = $state(0);

    const loadingSteps = [
        {
            status: "Reading files...",
            detail: "Parsing your job description and resume",
        },
        { status: "Uploading...", detail: "Sending documents to Hydra" },
        {
            status: "Starting workflow...",
            detail: "Initializing the multi-agent pipeline",
        },
        { status: "Redirecting...", detail: "Taking you to the progress page" },
    ];

    // Handle JD file changes
    async function handleJDFilesChange(files: File[]) {
        jdFiles = files;

        if (files.length > 0) {
            const file = files[0];
            const fileName = file.name.toLowerCase();

            // Check if it's a CSV file
            if (fileName.endsWith(".csv")) {
                const content = await file.text();
                const roles = parseRoleCSV(content);

                if (roles.length > 0) {
                    detectedRoles = roles;
                    showRolePicker = true;
                } else {
                    error =
                        "No roles found in CSV file. Please check the file format.";
                }
            } else if (fileName.endsWith(".json")) {
                // Handle JSON job feed files
                const content = await file.text();
                try {
                    const roles = parseJobFeedJSON(content);

                    if (roles.length > 0) {
                        detectedRoles = roles;
                        showRolePicker = true;
                    } else {
                        error =
                            "No jobs found in JSON file. Please check the file format.";
                    }
                } catch (e) {
                    error =
                        e instanceof Error
                            ? e.message
                            : "Failed to parse JSON file";
                }
            } else {
                // Regular file - read and store content
                jdContent = await file.text();
                selectedRole = null;
            }
        } else {
            jdContent = null;
            selectedRole = null;
        }
    }

    function handleResumeFilesChange(files: File[]) {
        resumeFiles = files;
    }

    function handleSourceFilesChange(files: File[]) {
        sourceFiles = files;
    }

    function handleRoleSelect(role: RoleEntry) {
        selectedRole = role;
        jdContent = roleToJobDescription(role);
        showRolePicker = false;
        // Clear the file input since we've extracted the content
        jdFiles = [];
    }

    function handleRolePickerCancel() {
        showRolePicker = false;
        jdFiles = [];
        detectedRoles = [];
    }

    async function handleSubmit(e: Event) {
        e.preventDefault();
        error = null;

        // Validate inputs
        if (!jdContent && jdFiles.length === 0) {
            error = "Job description is required";
            return;
        }
        if (resumeFiles.length === 0) {
            error = "Resume is required";
            return;
        }

        isSubmitting = true;
        loadingStep = 0;

        try {
            // Get job description content
            let jdText = jdContent;
            if (!jdText && jdFiles.length > 0) {
                jdText = await jdFiles[0].text();
            }

            // Get resume content
            loadingStep = 0;
            const resumeText = await resumeFiles[0].text();

            // Get source documents
            const sourcesText = await Promise.all(
                sourceFiles
                    .filter((f) => f.size > 0)
                    .map(async (f) => `# ${f.name}\n${await f.text()}`),
            );

            // Create job via API
            loadingStep = 1;
            const response = await fetch("/api/jobs", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    job_description: jdText,
                    resume: resumeText,
                    source_documents: sourcesText.join("\n\n"),
                }),
            });

            if (!response.ok) {
                const errorData = await response
                    .json()
                    .catch(() => ({ message: "Unknown error" }));
                throw new Error(
                    errorData.message ||
                        errorData.detail ||
                        `HTTP ${response.status}`,
                );
            }

            loadingStep = 2;
            const { job_id } = await response.json();

            // Redirect to job page
            loadingStep = 3;
            window.location.href = `/jobs/${job_id}`;
        } catch (err) {
            error = err instanceof Error ? err.message : "An error occurred";
            isSubmitting = false;
        }
    }
</script>

{#if showRolePicker}
    <RolePicker
        roles={detectedRoles}
        onSelect={handleRoleSelect}
        onCancel={handleRolePickerCancel}
    />
{/if}

{#if isSubmitting}
    <div class="loading-overlay">
        <div class="loading-content">
            <div class="loading-spinner">
                <div class="spinner-ring"></div>
                <div class="spinner-ring"></div>
                <div class="spinner-ring"></div>
            </div>
            <h2>{loadingSteps[loadingStep].status}</h2>
            <p>{loadingSteps[loadingStep].detail}</p>
            <div class="loading-steps">
                {#each loadingSteps as step, i}
                    <div class="step" class:active={i <= loadingStep}>
                        <span class="step-dot"></span>
                        <span>{["Read", "Upload", "Start", "Go"][i]}</span>
                    </div>
                    {#if i < loadingSteps.length - 1}
                        <div class="step-line"></div>
                    {/if}
                {/each}
            </div>
        </div>
    </div>
{/if}

<form class="card upload-form" onsubmit={handleSubmit}>
    {#if selectedRole}
        <div class="selected-role-banner">
            <div class="banner-content">
                <span class="banner-label">Selected Role:</span>
                <strong>{selectedRole.company}</strong> - {selectedRole.role}
                <button
                    type="button"
                    class="change-btn"
                    onclick={() => {
                        selectedRole = null;
                        jdContent = null;
                    }}>Change</button
                >
            </div>
        </div>
    {:else}
        <p class="csv-hint">Tip: Upload a CSV or JSON file to select from multiple roles</p>
        <FileUpload
            label="Job Description"
            name="jd"
            accept=".md,.txt,.csv,.json"
            required={!jdContent}
            onFilesChange={handleJDFilesChange}
        />
    {/if}

    <FileUpload
        label="Resume"
        name="resume"
        accept=".md,.txt"
        required={true}
        onFilesChange={handleResumeFilesChange}
    />

    <FileUpload
        label="Source Documents (optional)"
        name="sources"
        accept=".md,.txt"
        multiple={true}
        onFilesChange={handleSourceFilesChange}
    />

    <div class="form-actions">
        <button type="submit" id="submit-btn" disabled={isSubmitting}>
            Generate Application
        </button>
    </div>

    {#if error}
        <div class="error">{error}</div>
    {/if}
</form>

<style>
    .selected-role-banner {
        background: linear-gradient(
            135deg,
            rgba(59, 130, 246, 0.15),
            rgba(59, 130, 246, 0.05)
        );
        border: 1px solid var(--color-primary, #3b82f6);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1.5rem;
    }

    .banner-content {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex-wrap: wrap;
    }

    .banner-label {
        color: var(--color-text-muted, #888);
        font-size: 0.9rem;
    }

    .change-btn {
        margin-left: auto;
        padding: 0.25rem 0.75rem;
        font-size: 0.8rem;
        background: transparent;
        border: 1px solid var(--color-border, #333);
        border-radius: 4px;
        color: var(--color-text, #fff);
        cursor: pointer;
    }

    .change-btn:hover {
        background: rgba(255, 255, 255, 0.1);
    }

    .csv-hint {
        font-size: 0.85rem;
        color: var(--color-text-muted, #888);
        margin-bottom: 0.75rem;
        padding: 0.5rem 0.75rem;
        background: rgba(59, 130, 246, 0.1);
        border-radius: 6px;
        border-left: 3px solid var(--color-primary, #3b82f6);
    }

    .error {
        margin-top: 1rem;
        padding: 0.75rem 1rem;
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 8px;
        color: #ef4444;
    }

    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.9);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    }

    .loading-content {
        text-align: center;
        color: var(--color-text, #fff);
    }

    .loading-content h2 {
        margin: 1.5rem 0 0.5rem;
        font-size: 1.5rem;
    }

    .loading-content p {
        color: var(--color-text-muted, #888);
        margin: 0;
    }

    .loading-spinner {
        position: relative;
        width: 80px;
        height: 80px;
        margin: 0 auto;
    }

    .spinner-ring {
        position: absolute;
        width: 100%;
        height: 100%;
        border: 3px solid transparent;
        border-top-color: var(--color-primary, #3b82f6);
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    .spinner-ring:nth-child(2) {
        width: 70%;
        height: 70%;
        top: 15%;
        left: 15%;
        border-top-color: #60a5fa;
        animation-duration: 0.8s;
    }

    .spinner-ring:nth-child(3) {
        width: 40%;
        height: 40%;
        top: 30%;
        left: 30%;
        border-top-color: #93c5fd;
        animation-duration: 0.6s;
    }

    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
    }

    .loading-steps {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        margin-top: 2rem;
    }

    .step {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.5rem;
        opacity: 0.3;
        transition: opacity 0.3s;
    }

    .step.active {
        opacity: 1;
    }

    .step-dot {
        width: 12px;
        height: 12px;
        background: var(--color-primary, #3b82f6);
        border-radius: 50%;
    }

    .step-line {
        width: 30px;
        height: 2px;
        background: var(--color-border, #333);
    }

    .upload-form {
        max-width: 600px;
        margin: 0 auto;
    }

    .form-actions {
        margin-top: 1.5rem;
    }

    #submit-btn {
        width: 100%;
        padding: 1rem 2rem;
        font-size: 1.1rem;
        background: var(--color-primary, #3b82f6);
        color: white;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        transition: background 0.2s;
    }

    #submit-btn:hover:not(:disabled) {
        background: #2563eb;
    }

    #submit-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
</style>
