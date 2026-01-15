# User Experience & Usability Report

## 1. User Personas

### Persona A: The Honest Optimizer (Primary)
**Profile:** Mid-to-senior software engineer or tech professional.
**Goals:**
-   Apply to specific, high-value roles.
-   Tailor resume to match JD keywords and "vibe" without fabricating experience.
-   Avoid "AI-sounding" text that recruiters instantly reject.
-   Maintain a single "source of truth" for their career history.
**Frustrations:**
-   Rewriting resumes for every job is time-consuming.
-   Fear of "hallucinations" (AI inventing experience).
-   Dislikes complex CLI setups (Python environments, API keys).
**Needs:**
-   Trust: Needs to know *exactly* what was changed and why.
-   Control: Wants to approve/edit the "spin" before the final document is generated.

### Persona B: The Volume Applier (Secondary)
**Profile:** Junior engineer or recent grad.
**Goals:**
-   Apply to 50+ jobs per week.
-   Minimize time spent per application.
**Frustrations:**
-   Manual copy-pasting of files.
-   Wait times for generation.
**Needs:**
-   Batch processing.
-   Low friction setup.

---

## 2. User Journey Mapping

### Current Journey (The "Black Box")
1.  **Discovery:** User finds `composable-crew` repo.
2.  **Setup (High Friction):**
    -   Clones repo.
    -   Installs Python 3.x.
    -   Creates venv & installs requirements (often hits dependency conflicts).
    -   Obtains API key (Together/OpenRouter) and sets env var.
3.  **Preparation (High Friction):**
    -   Manually creates a `sources/` directory.
    -   Manually saves JD as `jd.md` (copy-paste from browser).
    -   Manually converts Resume to `resume.md` or txt.
4.  **Execution:**
    -   Runs `./run.sh ...` with long arguments.
5.  **Waiting:**
    -   Watches logs scroll by for 2-5 minutes.
    -   "Interrogator" generates questions in logs (User: "Wait, do I answer these?").
    -   Workflow continues automatically without answers.
6.  **Review:**
    -   Checks `output/` folder.
    -   Opens `audit_report.yaml` to see if it passed.
    -   Reads `resume.md`.
    -   *Realization:* The resume didn't address the specific gaps because the "interview" never happened.

### Ideal Journey (Human-in-the-Loop)
1.  **Setup:**
    -   `pip install composable-crew` (or single binary).
    -   `crew init` (interactive setup of API keys).
2.  **Input:**
    -   `crew apply https://linkedin.com/jobs/...` (URL support).
    -   System uses cached resume profile.
3.  **Analysis & Interview (The Missing Link):**
    -   System: "I found 3 gaps. 1. You lack 'GCP' experience. Do you have any unreported experience with Google Cloud?"
    -   User: "Yes, I used BigQuery at my last job for data warehousing."
    -   System: "Great, I'll add that."
4.  **Generation:**
    -   System generates documents using the *new* info.
5.  **Review:**
    -   User sees diff of changes.
    -   User accepts/rejects specific "spins".

---

## 3. Heuristic Evaluation (Usability Audit)

### Visibility of System Status
-   **Current:** Good logging in CLI.
-   **Issue:** The "Interrogator" step implies interaction but provides none. The user sees "Generating questions..." and then "Tailoring..." without a chance to intervene.

### Match Between System and Real World
-   **Issue:** The file structure requirements (`sources/`, `examples/`) are rigid and don't match how users organize files (usually `~/Documents/Resumes`).

### User Control and Freedom
-   **Critical Fail:** Once `run.sh` starts, it's a train on tracks. No way to pause, review the "Gap Analysis", correct a misunderstanding, or answer interview questions.
-   **Issue:** If the Audit fails, the user is stuck. They can't "override" the auditor easily without changing code or prompt files.

### Error Prevention
-   **Issue:** "Document failed audit after maximum retries" is a generic error for a complex problem.
-   **Issue:** If API keys are missing, the script might crash mid-execution rather than checking upfront (though `cli.py` seems to check `get_llm_client` early).

### Recognition Rather Than Recall
-   **Issue:** CLI arguments require remembering paths. A file picker or interactive mode (mentioned in README but relies on `run.sh` implementation) is better.

---

## 4. Key Recommendations

1.  **Implement Interactive Mode:** Stop the workflow after "Interrogator-Prepper" generates questions. Ask the user for input via CLI (using `input()` or a TUI library like `rich` or `textual`).
2.  **Interactive "Greenlight":** The README mentions "Commander asks: Proceed?". This is currently missing in code. Implement a confirmation step after Gap Analysis.
3.  **Unified Input:** Allow passing a URL for the JD instead of a file path (requires a scraper/fetcher).
4.  **Profile Management:** Instead of passing `--resume` and `--sources` every time, allow saving a "Default Profile" so the user only needs to provide the JD.
5.  **Fix the "Interview":** The `InterrogatorPrepper` should output questions, the system should prompt the user, and the *answers* should be fed into `TailoringAgent`.

## 5. Implementation Status (2026-01-13)

### ✅ Interactive Mode Implemented
-   Added `--interactive` flag to CLI.
-   Added `UserInteraction` class in `hydra_workflow.py`.
-   **Gap Analysis Review:** User is prompted to proceed/abort after gaps are identified.
-   **Interactive Interview:** System now pauses, asks the generated questions, and captures user input. These answers are fed into the `TailoringAgent`.

## 6. Metrics Strategy (Measuring Success)

To validate these UX improvements, we should track:
1.  **Completion Rate:** % of workflows that reach "Audit Passed" vs "Aborted".
    -   *Hypothesis:* Interactive mode might *lower* completion rate initially (users aborting bad gap analysis), but *increase* the quality/acceptance of final docs.
2.  **Edit Distance:** Compare the generated resume vs. the final version the user actually sends.
    -   *Goal:* Reduce the amount of manual editing required after generation.
3.  **User Satisfaction (CSAT):** Simple "Did this help?" prompt at the end.

## 7. Accessibility & Inclusion

-   **Screen Reader Support:** The CLI uses standard `stdout`/`stdin`, which is compatible with major screen readers (VoiceOver, JAWS, NVDA).
-   **Cognitive Load:**
    -   *Improvement:* Breaking the process into steps (Gap Analysis -> Approval -> Interview -> Result) reduces the cognitive load of reviewing a massive final output all at once.
    -   *Future:* Add "Save Progress" to allow breaks during the interview.

