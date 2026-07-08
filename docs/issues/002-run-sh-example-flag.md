# Issue 2 — Add `./run.sh --example` CLI mode

**Type:** Feature (CLI ergonomics)
**Priority:** Medium — depends on Issue 1 being merged first
**Estimate:** ~3–4 hours
**Labels:** `cli`, `examples`, `dx`
**Depends on:** Issue 1 (`examples/validated-output/` must exist before this can be wired up).

---

## Why

The repo currently advertises `./run.sh --jd ... --resume ... --out ...`, but a visitor has no zero-config way to see the project actually do something. They need an LLM API key, two input files, and the patience to read the README.

`./run.sh --example` should make the repo *feel runnable* without configuration. It uses the canned inputs from Issue 1, writes outputs to a predictable location, and either invokes the live workflow (if a provider key is present) OR falls back to copying the pre-validated artifacts (if no key is present). Either way, the user sees a complete output bundle in seconds.

## Goal

Add an `--example` flag to the existing CLI surface (`run.sh` and `runtime/crewai/cli.py`) that drives a sample end-to-end run against the inputs from `examples/validated-output/`, writing outputs to `output/example/`.

## Behavior

### When invoked: `./run.sh --example`

1. **Validate that `examples/validated-output/job_description.md` and `examples/validated-output/source_resume.md` exist.** If not, exit with a clear error pointing at Issue 1.
2. **Branch on LLM key availability** (the same key-detection logic `run.sh` already uses today — do NOT duplicate it; refactor if needed):
   - **If a provider key is set** (`TOGETHER_API_KEY`, `CHUTES_API_KEY`, or `OPENROUTER_API_KEY`): run the real workflow against the canned inputs. This is equivalent to:
     ```bash
     ./run.sh \
       --jd examples/validated-output/job_description.md \
       --resume examples/validated-output/source_resume.md \
       --sources examples/validated-output/ \
       --out output/example/
     ```
     Print a clear banner that says `Running EXAMPLE mode (live LLM)`.
   - **If NO provider key is set**: fall back to copying the pre-validated artifacts (`resume.md`, `cover_letter.md`, `audit_report.yaml`, `execution_log.txt`) from `examples/validated-output/` into `output/example/`. Print a clear banner that says `Running EXAMPLE mode (canned output, no LLM key found)` and a one-line note about how to set a key to do a live run. Exit 0.
3. **`output/example/` must be overwritten cleanly** on each invocation — do not append to stale outputs. Remove the directory first if it exists, then recreate.
4. **Do not pollute the user's environment.** The flag should not modify `.env`, install global packages, or write outside `output/example/`.

### Flag plumbing

- Surface the flag in `run.sh` first. `run.sh` should detect `--example`, build the equivalent `argparse` invocation, and `exec` into it. Do NOT bypass `runtime/crewai/cli.py` — go through the same code path as a normal CLI invocation so all the workflow guards stay engaged.
- Add `--example` to `runtime/crewai/cli.py::build_parser`. When `args.example` is set, the parser should NOT require `--jd` and `--resume`. Mutual exclusivity:
  - `--example` is incompatible with `--jd`, `--resume`, `--sources`. If any of those are passed alongside `--example`, fail with a clean error message.
  - `--out` may be passed alongside `--example` to override the default `output/example/`.
- The fallback-to-canned-output behavior lives in `run.sh` (it can `cp -R` and exit), NOT inside the Python CLI. The Python CLI's `--example` flag should just resolve the canned input paths and run the workflow normally.

### Output

`output/example/` (or the `--out` override) ends up containing the standard four-file output bundle (`resume.md`, `cover_letter.md`, `audit_report.yaml`, `execution_log.txt`), exactly matching what `_write_output_files` produces today.

### Help text

`./run.sh --help` and `python -m runtime.crewai.cli --help` should both show:

```
--example     Run the canned validated-output example. Uses examples/validated-output/
              as inputs and writes to output/example/. If no LLM API key is set,
              copies pre-validated artifacts instead of running the live workflow.
```

## Acceptance Criteria

- [ ] `./run.sh --example` works with NO env vars set: produces `output/example/{resume,cover_letter}.md`, `audit_report.yaml`, `execution_log.txt`, and exits 0.
- [ ] `./run.sh --example` works WITH `TOGETHER_API_KEY` set: triggers a real workflow run, banner indicates "live LLM" mode.
- [ ] `./run.sh --example --out /tmp/foo` writes to `/tmp/foo`, not `output/example/`.
- [ ] `./run.sh --example --jd whatever.md` fails fast with a clear "mutually exclusive" error and exit code != 0.
- [ ] Running `./run.sh --example` twice in a row leaves `output/example/` containing exactly one bundle — no stale files from the first run.
- [ ] `python -m runtime.crewai.cli --help` lists `--example`.
- [ ] `./run.sh --help` lists `--example`.
- [ ] `./run.sh --jd ... --resume ... --out ...` (the existing happy path) continues to work unchanged — this is the regression bar.
- [ ] README is updated with a short "Try it without a key" snippet:
  ````markdown
  ## Try it without a key

  ```bash
  ./run.sh --example
  ```
  Writes a canned validated example to `output/example/`. Set a provider key (see Configuration) to do a live run instead.
  ````

## Testing Plan

### Unit tests (mandatory)

Add `tests/unit/test_cli_example.py` (or extend an existing CLI test file) covering:

1. `build_parser` accepts `--example` without `--jd` and `--resume`.
2. Passing `--example` together with `--jd` raises a parse error.
3. Passing `--example` together with `--resume` raises a parse error.
4. Passing `--example` together with `--sources` raises a parse error.
5. `--example --out /custom/path` resolves `out_dir` to `/custom/path`.
6. With `--example` and no override, `out_dir` resolves to `output/example/`.
7. With `--example`, the resolved input paths point at `examples/validated-output/job_description.md` and `examples/validated-output/source_resume.md`.

Mock the workflow (`HydraWorkflow.execute`) — do NOT make real LLM calls in tests.

### Integration smoke test (mandatory)

Add a tiny shell-level smoke test (can be a pytest using `subprocess.run` against `./run.sh --example`) that asserts:
- Exit code 0 with no env vars set.
- All four output files exist after the run.
- `audit_report.yaml` parses as valid YAML.

The smoke test must run in CI with no LLM keys configured, so it exercises the canned-fallback path.

### Regression checks (G2 — mandatory)

- `pytest -q` — full suite must remain green. Report before/after pass counts in the PR.
- `python -m runtime.crewai.cli --jd examples/sample_jd.md --resume examples/sample_resume.md --sources examples/ --out /tmp/regression-check` — the existing CLI path must still parse, validate inputs, and reach the workflow boundary unchanged. (Skip the LLM call by setting `--max-audit-retries 0` and mocking, or simply confirm the parser/file-resolution layer still works without making a real API call.)
- `./run.sh --help` output must still contain every flag it contained before this change.
- Web UI (`web/`) is untouched — `git diff --stat web/` should be empty.
- Telemetry/agents (`runtime/crewai/agents/`, `runtime/crewai/telemetry.py`) must not be modified for this issue.

### Completion validation

- [ ] Full `pytest -q` green locally.
- [ ] `./run.sh --example` demonstrated locally with NO key set — paste terminal output in the PR.
- [ ] `./run.sh --example` demonstrated locally WITH a key set — paste terminal output (redact the key) in the PR. If you don't have a key, mark this and request the maintainer verify.
- [ ] `git diff --stat` in the PR shows changes limited to: `run.sh`, `runtime/crewai/cli.py`, `tests/unit/test_cli_example.py` (or equivalent), `README.md`, and possibly a tiny `.gitignore` update for `output/example/`. Anything outside this set must be justified in the PR description.
- [ ] `.gitignore` already excludes `output/` — verify it still does. Do NOT commit `output/example/` itself.

## Out of Scope

- Changing the workflow, agents, or audit logic.
- Adding new LLM providers.
- Changing the web UI.
- Adding caching, telemetry, or progress bars.
- Creating new example input variants. (One canned example is enough; more is scope creep.)

## Implementation Notes for the Developer Agent

- **Read Issue 1 first.** This issue assumes the file layout from Issue 1. If Issue 1's directory looks different from what is referenced here, STOP and reconcile — do not paper over a mismatch.
- The `run.sh` "no key set" branch is the load-bearing UX. Failure mode: the canned output is missing or out of date → the user sees a broken demo. Add a guard in `run.sh` that fails clearly if `examples/validated-output/` is missing or doesn't contain the four artifact files. Don't silently produce a half-empty output dir.
- Be careful with `set -e` in `run.sh` when implementing the fallback `cp`. A missing file should produce a clean, actionable error, not a bare bash trace.
- Argparse mutual-exclusivity is best expressed via `add_mutually_exclusive_group` OR a manual post-parse check that raises `parser.error(...)`. Use whichever keeps the help text clean. Verify with `--help` output that the message is readable.
- Do NOT use destructive shortcuts. `rm -rf output/example/` is fine because it lives under the project's gitignored `output/`. Never `rm -rf` anything outside `output/`.
- This is the kind of feature that gets a "looks good" rubber stamp on review but breaks two weeks later when someone forgets the canned files. Defensive copy: the smoke test catches that.
