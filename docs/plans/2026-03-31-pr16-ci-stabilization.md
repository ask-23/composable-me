# PR #16 CI Stabilization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Eliminate the PR #16 CI failure by making the newly added property-based test dependency available in every CI environment that installs `requirements.txt`.

**Architecture:** Keep the fix minimal and dependency-focused. The failure is caused during pytest collection, not by runtime logic, so the correct repair is to align the Python dependency manifest with the new test suite rather than changing workflow commands or test code.

**Tech Stack:** GitHub Actions, Python 3.11, pytest, Hypothesis, Docker, PostgreSQL 16, Astro, Node 20

### Task 1: Reproduce the failure exactly

**Files:**
- Inspect: `.github/workflows/ci.yml`
- Inspect: `requirements.txt`
- Inspect: `tests/unit/test_property_based.py`

**Step 1: Confirm the failing CI job**

Run:
```bash
curl -sS https://api.github.com/repos/ask-23/composable-me/actions/runs/23830475547/jobs
```

Expected:
- `unit-tests` is the only failing job.
- The failing step is `Run unit tests`.

**Step 2: Write the failing repro command**

Run:
```bash
docker run --rm -v /tmp/composable-me-pr16-pristine:/app -w /app python:3.11 bash -lc "pip install -q -r requirements.txt -r web/backend/requirements.txt && python -m pytest tests/unit/test_property_based.py -v"
```

Expected:
- pytest exits with code `2`
- collection fails with `ModuleNotFoundError: No module named 'hypothesis'`

### Task 2: Apply the minimal fix

**Files:**
- Modify: `requirements.txt`

**Step 1: Add the missing dependency**

Add this line under the existing pytest dependencies:
```txt
hypothesis>=6.0.0
```

**Step 2: Do not modify CI workflow steps**

Reason:
- `ci.yml` already installs `requirements.txt`
- once `hypothesis` is declared, the failing unit job gets the package automatically

### Task 3: Verify the exact failure is resolved

**Files:**
- Verify: `requirements.txt`
- Verify: `tests/unit/test_property_based.py`

**Step 1: Re-run the previously failing property-test collection**

Run:
```bash
docker run --rm -v /Users/alex/git/composable-me:/app -w /app python:3.11 bash -lc "pip install -q -r requirements.txt -r web/backend/requirements.txt && python -m pytest tests/unit/test_property_based.py -v"
```

Expected:
- `46 passed`
- Hypothesis plugin is present during collection

**Step 2: Re-run the exact CI unit job shape**

Run:
```bash
docker run --rm --add-host host.docker.internal:host-gateway -e HYDRA_DATABASE_URL=postgresql://hydra:hydra@host.docker.internal:5432/hydra_test -v /Users/alex/git/composable-me:/app -w /app python:3.11 bash -lc "pip install -q -r requirements.txt -r web/backend/requirements.txt && python -m pytest tests/unit/ -v --cov=runtime --cov=web/backend --cov-report=xml"
```

Expected:
- `499 passed`
- `Coverage XML written to file coverage.xml`

### Task 4: Validate from a pristine GitHub clone

**Files:**
- Create temp clone: `/tmp/composable-me-pr16-pristine`

**Step 1: Create the clean-room repo**

Run:
```bash
git clone https://github.com/ask-23/composable-me.git /tmp/composable-me-pr16-pristine
cd /tmp/composable-me-pr16-pristine
git checkout 55dfb939cb076cdb2f3162a1da6e2847e56c9a42
```

Expected:
- detached HEAD at the PR head SHA before the fix

**Step 2: Apply the same one-line dependency fix**

Add:
```txt
hypothesis>=6.0.0
```

**Step 3: Run pristine-clone unit validation**

Run:
```bash
docker run --rm --add-host host.docker.internal:host-gateway -e HYDRA_DATABASE_URL=postgresql://hydra:hydra@host.docker.internal:5432/hydra_test -v /tmp/composable-me-pr16-pristine:/app -w /app python:3.11 bash -lc "pip install -q -r requirements.txt -r web/backend/requirements.txt && python -m pytest tests/unit/ -v --cov=runtime --cov=web/backend --cov-report=xml"
```

Expected:
- `499 passed`

**Step 4: Run pristine-clone integration validation**

Run:
```bash
docker run --rm --add-host host.docker.internal:host-gateway -e HYDRA_DATABASE_URL=postgresql://hydra:hydra@host.docker.internal:5432/hydra_test -v /tmp/composable-me-pr16-pristine:/app -w /app python:3.11 bash -lc "pip install -q -r requirements.txt -r web/backend/requirements.txt && python -m pytest tests/integration/ -v"
```

Expected:
- `127 passed, 3 skipped`

**Step 5: Run pristine-clone frontend checks**

Run:
```bash
docker run --rm -v /tmp/composable-me-pr16-pristine/web/frontend:/app -w /app node:20 bash -lc "npm install && npx astro check && npm run build && cd /tmp && if grep -rn 'goto.*\\/job\\/' /app/tests/e2e/; then exit 1; fi"
```

Expected:
- Astro check succeeds with `0 errors`
- Astro build succeeds
- no `/job/` route mismatch is found in E2E tests

### Task 5: Prevent repeat CI failures of this class

**Files:**
- Keep current fix in: `requirements.txt`
- Document in PR / review notes

**Step 1: Adopt the dependency rule**

Rule:
- any new imported test library must be added in the same PR to the dependency file installed by CI

**Step 2: Add pre-push validation to PR workflow**

Run before resubmitting PRs:
```bash
docker run --rm --add-host host.docker.internal:host-gateway -e HYDRA_DATABASE_URL=postgresql://hydra:hydra@host.docker.internal:5432/hydra_test -v "$PWD":/app -w /app python:3.11 bash -lc "pip install -q -r requirements.txt -r web/backend/requirements.txt && python -m pytest tests/unit/ -v --cov=runtime --cov=web/backend --cov-report=xml"
docker run --rm --add-host host.docker.internal:host-gateway -e HYDRA_DATABASE_URL=postgresql://hydra:hydra@host.docker.internal:5432/hydra_test -v "$PWD":/app -w /app python:3.11 bash -lc "pip install -q -r requirements.txt -r web/backend/requirements.txt && python -m pytest tests/integration/ -v"
docker run --rm -v "$PWD"/web/frontend:/app -w /app node:20 bash -lc "npm install && npx astro check && npm run build"
```

**Step 3: Keep RCA attached to the PR**

Publish:
- failing job name
- exact root cause
- exact verification commands
- pristine-clone evidence

