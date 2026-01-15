# Web Application Specification & Architecture

## 1. Overview
The goal is to transition `composable-crew` from a CLI-first tool to a robust Web Application. The core requirement is "Human-in-the-Loop" workflow, allowing users to:
1.  Upload Resume/JD.
2.  Review Gap Analysis findings.
3.  Answer Interview Questions interactively.
4.  Download tailored documents.

## 2. User Journey & UI Flow

### Phase 1: Ingestion
-   **Page:** `/` (Home)
-   **Actions:**
    -   Upload Resume (PDF/Markdown).
    -   Paste Job Description (Text/URL).
    -   Optional: Select "Source Documents" folder (or upload zip).
-   **System:** Creates a `Job` in `INITIALIZED` state.

### Phase 2: Analysis & Review
-   **Page:** `/jobs/{id}/analysis`
-   **System:** Runs `GapAnalyzer`.
-   **UI:**
    -   Shows "Analyzing..." progress bar.
    -   Displays `Gap Analysis Report` (Matches, Gaps, Blockers).
-   **Action:**
    -   User clicks **"Approve & Continue"** (Triggers transition to Phase 3).
    -   User clicks **"Abort"**.

### Phase 3: The Interview
-   **Page:** `/jobs/{id}/interview`
-   **System:** Runs `InterrogatorPrepper`.
-   **UI:**
    -   Chat interface.
    -   Agent asks questions based on Gaps.
    -   User types answers.
-   **Action:**
    -   User answers all questions.
    -   User clicks **"Submit Answers"** (Triggers transition to Phase 4).

### Phase 4: Tailoring & Result
-   **Page:** `/jobs/{id}/result`
-   **System:** Runs `Differentiator` -> `Tailoring` -> `ATS` -> `Audit`.
-   **UI:**
    -   Shows "Tailoring..." progress.
    -   Displays Final Resume & Cover Letter (Markdown/Preview).
    -   Displays Audit Report.
-   **Action:**
    -   Download PDF/MD.
    -   "Restart" or "Edit Answers".

---

## 3. Technical Architecture Refactoring

### Core Issue: Monolithic Execution
The current `HydraWorkflow.execute()` is blocking. It runs A -> B -> C -> D in one go. We need to break this into "Steps" or "Phases".

### New Workflow State Machine
The `HydraWorkflow` will support a `step()` method that runs *one* phase and returns the next state.

**States:**
1.  `INITIALIZED`
2.  `GAP_ANALYSIS_RUNNING` -> `GAP_ANALYSIS_REVIEW` (Pause)
3.  `INTERROGATION_RUNNING` -> `INTERROGATION_REVIEW` (Pause for Answers)
4.  `GENERATION_RUNNING` (Diff -> Tailor -> ATS -> Audit)
5.  `COMPLETED`

### Backend Changes (`web/backend/`)

#### 1. `Job` Model Update (`models.py`, `job_queue.py`)
Add fields for user input:
-   `gap_analysis_approved` (bool)
-   `interview_answers` (List[Dict])

#### 2. API Endpoints (`routes/jobs.py`)
-   `POST /jobs`: Create Job.
-   `GET /jobs/{id}`: Get Status.
-   `POST /jobs/{id}/approve_analysis`: Sets `gap_analysis_approved=True`, resumes workflow.
-   `POST /jobs/{id}/submit_answers`: Saves answers, resumes workflow.

#### 3. Workflow Runner (`services/workflow_runner.py`)
-   Must support **Execution Cycles**: Load Job -> Run until Pause -> Save State -> Exit Thread.
-   Resume: Load Job -> Inject Input -> Continue.

---

## 4. Implementation Plan

1.  **Refactor `HydraWorkflow`**:
    -   Split `execute()` into `run_stage_gap_analysis()`, `run_stage_interrogation()`, etc.
    -   Add `resume_context` input to handle injecting user answers.
2.  **Update API**:
    -   Add `JobController` actions for approval and answers.
3.  **Update Frontend**:
    -   Implement the 4 pages using Astro/Svelte.
