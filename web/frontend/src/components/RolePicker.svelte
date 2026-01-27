<script lang="ts">
    /**
     * RolePicker.svelte - Modal for selecting a role from CSV data
     */
    import type { RoleEntry } from "../lib/csv-utils";

    interface Props {
        roles: RoleEntry[];
        onSelect: (role: RoleEntry) => void;
        onCancel: () => void;
    }

    let { roles, onSelect, onCancel }: Props = $props();

    let searchQuery = $state("");
    let selectedIndex = $state(-1);

    // Filter roles based on search
    let filteredRoles = $derived(
        roles.filter((role) => {
            const query = searchQuery.toLowerCase();
            return (
                role.company.toLowerCase().includes(query) ||
                role.role.toLowerCase().includes(query) ||
                role.location.toLowerCase().includes(query)
            );
        }),
    );

    function handleSelect(role: RoleEntry) {
        onSelect(role);
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === "Escape") {
            onCancel();
        } else if (e.key === "ArrowDown") {
            e.preventDefault();
            selectedIndex = Math.min(
                selectedIndex + 1,
                filteredRoles.length - 1,
            );
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            selectedIndex = Math.max(selectedIndex - 1, 0);
        } else if (e.key === "Enter" && selectedIndex >= 0) {
            handleSelect(filteredRoles[selectedIndex]);
        }
    }
</script>

<svelte:window onkeydown={handleKeydown} />

<div class="modal-backdrop" onclick={onCancel} role="presentation">
    <div
        class="modal"
        onclick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
    >
        <div class="modal-header">
            <h2 id="modal-title">Select a Role</h2>
            <p class="subtitle">Found {roles.length} roles in your CSV file</p>
        </div>

        <div class="search-container">
            <input
                type="text"
                placeholder="Search by company, role, or location..."
                bind:value={searchQuery}
                class="search-input"
                autofocus
            />
        </div>

        <div class="roles-list">
            {#each filteredRoles as role, i}
                <button
                    class="role-card"
                    class:selected={i === selectedIndex}
                    onclick={() => handleSelect(role)}
                    onmouseenter={() => (selectedIndex = i)}
                >
                    <div class="role-header">
                        <span class="company">{role.company}</span>
                        <span class="location">{role.location}</span>
                    </div>
                    <div class="role-title">{role.role}</div>
                    <div class="role-meta">
                        <span class="employment-type"
                            >{role.employmentType}</span
                        >
                        {#if role.salary && role.salary !== "Not specified"}
                            <span class="salary">{role.salary}</span>
                        {/if}
                    </div>
                </button>
            {:else}
                <div class="no-results">No roles match your search</div>
            {/each}
        </div>

        <div class="modal-footer">
            <button class="cancel-btn" onclick={onCancel}>Cancel</button>
            <span class="hint"
                >↑↓ to navigate, Enter to select, Esc to cancel</span
            >
        </div>
    </div>
</div>

<style>
    .modal-backdrop {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        backdrop-filter: blur(4px);
    }

    .modal {
        background: var(--color-bg-secondary, #1a1a2e);
        border: 1px solid var(--color-border, #333);
        border-radius: 12px;
        width: 90%;
        max-width: 700px;
        max-height: 80vh;
        display: flex;
        flex-direction: column;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
    }

    .modal-header {
        padding: 1.5rem;
        border-bottom: 1px solid var(--color-border, #333);
    }

    .modal-header h2 {
        margin: 0;
        font-size: 1.5rem;
        color: var(--color-text, #fff);
    }

    .subtitle {
        margin: 0.5rem 0 0;
        color: var(--color-text-muted, #888);
        font-size: 0.9rem;
    }

    .search-container {
        padding: 1rem 1.5rem;
        border-bottom: 1px solid var(--color-border, #333);
    }

    .search-input {
        width: 100%;
        padding: 0.75rem 1rem;
        background: var(--color-bg, #0f0f1a);
        border: 1px solid var(--color-border, #333);
        border-radius: 8px;
        color: var(--color-text, #fff);
        font-size: 1rem;
    }

    .search-input:focus {
        outline: none;
        border-color: var(--color-primary, #3b82f6);
    }

    .roles-list {
        flex: 1;
        overflow-y: auto;
        padding: 1rem;
    }

    .role-card {
        width: 100%;
        text-align: left;
        padding: 1rem;
        margin-bottom: 0.75rem;
        background: var(--color-bg, #0f0f1a);
        border: 1px solid var(--color-border, #333);
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
    }

    .role-card:hover,
    .role-card.selected {
        border-color: var(--color-primary, #3b82f6);
        background: rgba(59, 130, 246, 0.1);
    }

    .role-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }

    .company {
        font-weight: 600;
        color: var(--color-primary, #3b82f6);
        font-size: 0.9rem;
    }

    .location {
        font-size: 0.8rem;
        color: var(--color-text-muted, #888);
    }

    .role-title {
        font-size: 1.1rem;
        font-weight: 500;
        color: var(--color-text, #fff);
        margin-bottom: 0.5rem;
    }

    .role-meta {
        display: flex;
        gap: 1rem;
        font-size: 0.8rem;
        color: var(--color-text-muted, #888);
    }

    .salary {
        color: var(--color-success, #10b981);
    }

    .no-results {
        text-align: center;
        padding: 2rem;
        color: var(--color-text-muted, #888);
    }

    .modal-footer {
        padding: 1rem 1.5rem;
        border-top: 1px solid var(--color-border, #333);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .cancel-btn {
        padding: 0.5rem 1rem;
        background: transparent;
        border: 1px solid var(--color-border, #333);
        border-radius: 6px;
        color: var(--color-text, #fff);
        cursor: pointer;
    }

    .cancel-btn:hover {
        background: rgba(255, 255, 255, 0.1);
    }

    .hint {
        font-size: 0.8rem;
        color: var(--color-text-muted, #888);
    }
</style>
