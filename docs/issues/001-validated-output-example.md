# Issue 1 — Add `examples/validated-output/` sanitized sample run

**Type:** Feature (docs + example artifacts)
**Priority:** High — portfolio-visible, blocks Issue 2
**Estimate:** ~2–3 hours
**Labels:** `docs`, `examples`, `portfolio`

---

## Why

The README promises "résumé + cover letter + claim-by-claim audit output", but a visitor cannot see what those artifacts actually look like without cloning the repo, configuring an LLM provider, and running the workflow. A hiring manager browsing the repo for two minutes will bounce.

A canned, sanitized example commits the full output path to the tree so the artifact story is visible at a glance. This is portfolio surface area, not an internal tool — the example IS the product demonstration.

## Goal

Create a new directory `examples/validated-output/` that contains a complete, sanitized end-to-end run of the Hydra workflow, including all six artifact types the workflow normally produces, plus a `README.md` that frames the example.

## Deliverables

### Directory layout (exact)

```
examples/validated-output/
├── job_description.md      # The input JD used to drive the run
├── source_resume.md        # The source material (raw experience)
├── resume.md               # Generated tailored résumé
├── cover_letter.md         # Generated cover letter
├── audit_report.yaml       # Claim-by-claim audit, matching the schema of a real run
├── execution_log.txt       # Agent-by-agent trace of the run
└── README.md               # Frames the example, explains each file
```

All filenames are exact. No additional files. No nested folders.

### File-level requirements

#### `job_description.md`
- Reuse and extend `examples/sample_jd.md` (the existing Senior Platform Engineer JD).
- Must be plausible but clearly synthetic (e.g., "Company A (Example)"). No real company names.

#### `source_resume.md`
- A synthetic source résumé for a fictional candidate. Use a clearly-fake name (e.g., "Sam Rivera") and email (e.g., `sam.rivera@example.com`). No real PII.
- Should contain enough real-feeling detail (specific projects, technologies, year ranges, modest metrics like "reduced p95 latency by 35%") that the downstream tailored output and audit report look credible.
- 1–2 pages of markdown.

#### `resume.md`
- A tailored résumé that could plausibly be generated FROM `source_resume.md` FOR `job_description.md`.
- **Critical:** every concrete claim (tech stack, metric, role) in `resume.md` must appear in (or be a defensible restatement of) something in `source_resume.md`. The audit report below will be checked against this rule.
- Output format should match what `runtime/crewai/cli.py::_write_output_files` produces (plain markdown, no YAML front matter).

#### `cover_letter.md`
- Tailored cover letter referencing only material grounded in `source_resume.md`.
- 250–400 words. Plain markdown, no header block.

#### `audit_report.yaml`
- Must match the schema produced by the real workflow. Inspect `runtime/crewai/hydra_workflow.py` and the test fixtures under `tests/` to find the actual schema; do not invent fields. Required top-level keys at minimum (verify against the live schema before writing):
  - `final_status` (e.g., `APPROVED`)
  - per-claim entries with `claim`, `source_evidence`, `verdict`, optional `confidence`
- At least 8–12 claim entries covering: a verified metric, a verified role/title, a verified tech-stack item, AND **at least one `MODIFIED` or `REJECTED` claim with a documented reason** — the whole point of the example is to show the audit doing real work, not rubber-stamping everything.

#### `execution_log.txt`
- Plain-text trace, one line per significant step, formatted like the real `execution_log.txt` lines emitted by the workflow. Inspect `runtime/crewai/hydra_workflow.py` for the actual line format.
- Should include: workflow start, each agent stage (gap analysis, interview/interrogation, differentiation, tailoring, ATS optimization, audit), audit retries (if any), and final status. ~30–80 lines is appropriate.
- Timestamps may be omitted OR all set to a single fixed ISO date (e.g., `2026-05-23T19:00:00Z`) — never use real wall-clock timestamps; this is a canned artifact.

#### `README.md`
Use this body (verbatim is fine; minor improvements welcome):

```markdown
# Validated Output Example

This directory contains a sanitized example of Composable Me's output flow:

1. job description input — `job_description.md`
2. source résumé input — `source_resume.md`
3. generated résumé — `resume.md`
4. generated cover letter — `cover_letter.md`
5. claim-by-claim audit report — `audit_report.yaml`
6. execution log — `execution_log.txt`

The point is not to generate plausible prose. The point is to show that every output claim traces back to supplied source material, and that the audit refuses or modifies claims it cannot verify.

This is a canned, hand-curated example committed to the repository. It is not the output of a live run, and it does not consume an API key. To produce real output, see the top-level README and run `./run.sh --jd ... --resume ... --out ...`.
```

## Acceptance Criteria

- [ ] `examples/validated-output/` exists with exactly the seven files listed above.
- [ ] No real PII anywhere — names, emails, companies, dates are clearly synthetic.
- [ ] `audit_report.yaml` parses as valid YAML and matches the live workflow schema (verify by loading it with `yaml.safe_load` in a quick test; do not invent fields).
- [ ] `audit_report.yaml` contains at least one claim that is NOT `APPROVED` (i.e., `MODIFIED`, `REJECTED`, or equivalent), with a documented reason — proves the audit is doing work.
- [ ] Every concrete factual claim (metric, role, tech) in `resume.md` and `cover_letter.md` traces back to something in `source_resume.md`. Spot-check 5+ claims by hand.
- [ ] Repo-root `README.md` gains a short reference to this directory under "Output Files" or "Proof Points" (e.g., a line like: "See [`examples/validated-output/`](examples/validated-output/) for a sanitized end-to-end run.").
- [ ] `git grep -E '(my-real-email|my-real-name|@afgusa\.net|akorshak)'` returns nothing inside `examples/validated-output/`.

## Testing & Validation

### Build verification (G1 — self-check, run in same session)

1. **YAML parse test** — add a tiny test (or run an ad-hoc snippet) that loads `examples/validated-output/audit_report.yaml` with `yaml.safe_load` and asserts the schema's required top-level keys are present. Either:
   - Add it as a new test under `tests/unit/test_examples.py`, OR
   - Add it as an assertion inside an existing examples-related test if one is a natural fit.
2. **Existing test suite must remain green:**
   ```bash
   pytest -q
   ```
   No new failures vs. `main`. Capture and report the before/after pass counts.
3. **CLI smoke (no LLM key required)** — running `./run.sh --help` and `python -m runtime.crewai.cli --help` must still succeed.

### Regression checks (G2 — contract review territory)

- Confirm no production code path was changed. This issue is docs + static artifacts only. Any code change must be limited to a test file under `tests/unit/`. If the implementing agent finds itself touching `runtime/`, `web/`, `cli/`, or `agents/`, **STOP** and escalate — that is out of scope.
- Verify `tests/e2e/` and Playwright tests are NOT affected (no UI surface in this issue).
- Run `git diff --stat main...HEAD` and confirm the only non-test, non-docs changes are inside `examples/validated-output/` and a small README addition. If there are any other modified files, justify each one explicitly in the PR description.

### Completion validation

- [ ] `pytest -q` passes locally (full suite, not just new test).
- [ ] `git status` is clean except for the new directory, the new test, and the README edit.
- [ ] PR description includes a screenshot or terminal paste of `tree examples/validated-output/`.
- [ ] PR description lists the before/after `pytest` pass counts.

## Out of Scope

- Generating this example from a live LLM run. It is canned and hand-authored.
- Adding a CLI flag or any code that consumes this directory. (That is Issue 2.)
- Changing the production workflow, agents, or schemas.
- Adding new test infrastructure or CI jobs.

## Implementation Notes for the Developer Agent

- Re-read the live `audit_report.yaml` schema before writing the example. Best sources: `runtime/crewai/hydra_workflow.py`, `runtime/crewai/models.py`, and any audit fixtures under `tests/`. Do not guess the schema.
- The README claim "every output claim traces back to supplied source material" is the load-bearing promise. If your hand-curated example violates that promise, the whole exercise fails. Audit your own example before opening the PR.
- Treat this as portfolio-quality content. A hiring manager will read it. Tone, formatting, and proofreading matter.
