# ADR 0001: CrewAI vs. Direct LiteLLM for the Hydra Agent Spine

- **Status:** Proposed
- **Date:** 2026-07-09
- **Author:** ask-23
- **Deciders:** Composable Me maintainers
- **Source of truth:** Code read directly from `runtime/crewai/` on branch `main`
  (worktree at `docs/adr-crewai-vs-direct-llm`) and the installed dependency tree
  in `.venv13` (Python 3.13), inspected 2026-07-09.

## Context

The Hydra pipeline runs seven agents in a hand-rolled Python sequence
(`runtime/crewai/hydra_workflow.py`): Gap Analyzer, Interrogator-Prepper,
Differentiator, Tailoring Agent, ATS Optimizer, Auditor Suite, and Executive
Synthesizer. CrewAI is the nominal orchestration framework, but the way it is
wired means the app uses it as a **thin, single-call shim** rather than as an
orchestrator.

### How CrewAI is actually used

Every agent invocation flows through `BaseHydraAgent.execute_with_retry`
(`runtime/crewai/base_agent.py:313-319`), which builds a brand-new one-agent,
one-task Crew for each call and kicks it off:

```python
crew = Crew(
    agents=[task.agent],
    tasks=[task],
    process=Process.sequential,
    verbose=False,
)
result = crew.kickoff()
```

- `create_agent()` (`base_agent.py:116-127`) wraps **one** prompt + role/goal/
  backstory, with `allow_delegation=False`.
- `create_task()` (`base_agent.py:152-170`) wraps **one** task description +
  `expected_output`.
- The Crew always contains exactly one agent and one task
  (`tasks=[task]`), so `Process.sequential` orchestrates a sequence of length
  one — a no-op.

CrewAI is effectively a prompt-assembly-and-invoke wrapper around a single LLM
call. Under the hood the LLM itself is **LiteLLM**: `crewai.LLM` wraps
`litellm`, and `runtime/crewai/model_config.py` / `llm_client.py` already speak
LiteLLM's provider-prefixed model naming
(`anthropic/…`, `together_ai/…`, `openai/…`, `openrouter/…`). LiteLLM is also a
first-class direct dependency (`litellm>=1.80.0` in `requirements.txt`).

### CrewAI features that are NOT used anywhere

| Feature                     | Evidence it is unused                                                                                                             |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Tools (`crewai-tools`)      | `crewai_tools` / `crewai.tools` imported in **zero** application modules.                                                         |
| Agent memory                | No `memory=` argument anywhere; no memory store configured.                                                                       |
| Delegation / agent-to-agent | `allow_delegation=False` on every agent.                                                                                          |
| Multi-task graphs           | Every Crew is `tasks=[task]` — a single task.                                                                                     |
| Process orchestration       | `Process.sequential` over one task; no `Process.hierarchical`, no planning, no manager agent.                                     |
| Task context chaining       | `create_task` accepts `context` but the workflow passes plain dicts between stages itself and never chains CrewAI `Task` objects. |

The ordering, state machine, human-in-the-loop pauses, fallback-model logic,
retry loops, and typed stage contracts are all **hand-rolled** in
`hydra_workflow.py` and `contracts.py`. None of it rides on CrewAI.

### Dependency and per-call cost of the shim

Dependency weight (measured in `.venv13`, 2026-07-09):

- **194** installed packages; **~993 MB** of site-packages.
- `crewai` 1.12.2 (~9.8 MB) transitively pulls `chromadb`, `lancedb`,
  `instructor`, `textual`, `tokenizers`, `mcp`, `pdfplumber`, `openpyxl`,
  `portalocker`, `uv`, and more.
- `crewai-tools` 1.12.2 (~3.4 MB) transitively pulls `docker`, `pymupdf`,
  `python-docx`, `pytube`, `youtube-transcript-api`, `tiktoken`,
  `beautifulsoup4` — none of which the app imports.
- `litellm` (~77 MB) would be retained regardless, because it is the actual
  transport.

Version-pin risk: `requirements.txt` pins `crewai[anthropic]>=0.86.0`, but the
resolved install is **1.12.2** — a floor-only pin that has already let a major
version drift (0.86 → 1.x). A heavy framework on a floor pin is a meaningful
supply-chain and breakage surface for a dependency used only to assemble one
prompt.

Per-call overhead: each stage constructs a fresh `Crew`, an agent executor,
and CrewAI's task-output wrapping/telemetry on **every** call. A full run makes
**6–8** such calls (gap, interrogation, differentiation, tailoring, ATS, audit
of résumé, optional audit of cover letter, executive synthesis), plus extra
calls on fallback-model retries and audit retries. The Python-side orchestration
overhead per call (executor construction, memory/planning checks, result
wrapping) is unmeasured today; quantifying it is part of the proposed spike
below. It is strictly additive to the underlying LiteLLM request either way.

## Considered Options

### Option (a): Keep CrewAI as-is

Leave the one-agent/one-task Crew-per-call pattern in place.

- **Pros:** Zero work. Preserves the option to adopt CrewAI tools/memory/
  delegation later with no re-plumbing. Familiar vocabulary (Agent/Task/Crew).
- **Cons:** Carries `crewai` + `crewai-tools` and their large transitive trees
  (chromadb, lancedb, docker, pytube, …) purely to assemble a single prompt.
  Floor-only version pin invites silent major-version drift. Adds per-call
  orchestration overhead with no orchestration benefit. The framework's mental
  model ("a crew of collaborating agents") actively misleads readers about what
  the code does.

### Option (b): Replace only the `Crew.kickoff()` seam with a direct `litellm.completion` call

Change the single seam in `execute_with_retry` to call `litellm.completion(...)`
directly. **Keep everything else:** the agent wrappers, prompt/backstory
assembly (`_build_backstory`), the required-fields task decoration in
`create_task`, the typed stage contracts (`runtime/crewai/contracts.py`),
`validate_output`, the fallback/retry logic, and the telemetry spans
(`trace_agent_execution`, `record_agent_result/error`).

- **Pros:** Removes `crewai` + `crewai-tools` and their transitive weight while
  keeping LiteLLM (already the real transport and an existing direct dep). One
  well-tested seam changes; the public behavior (JSON string in → validated dict
  out) is unchanged. The code then says what it does: assemble a prompt, call a
  model, validate JSON. Smaller, pin-able dependency surface.
- **Cons:** Loses the drop-in path to CrewAI tools/memory/delegation — re-adding
  them later means reintroducing the framework. Requires faithfully reproducing
  the system/user message split that CrewAI assembles from role/goal/backstory +
  task description + `expected_output`, or accepting a deliberate, tested prompt
  change. Net new (small) amount of message-assembly code we now own.

### Option (c): Hybrid

Route mechanical single-call agents through direct `litellm.completion`, but keep
CrewAI available behind the same `BaseHydraAgent` interface for any future agent
that genuinely needs tools/memory/delegation.

- **Pros:** Incremental; lets a future tool-using agent adopt CrewAI without a
  framework-wide decision.
- **Cons:** Keeps both dependency trees installed, so it captures **none** of the
  dependency-weight savings — the main cost driver. Two code paths to test and
  reason about. Adds complexity to hedge against a capability that is not on the
  roadmap.

## Decision

**Recommended: Option (b) — but as a SEPARATE follow-on PR. Do not migrate now.**

This ADR records the decision and rationale; it does not itself change the
runtime. The migration should land as its own reviewable change.

### Decision criteria

1. **Per-call latency/cost overhead.** CrewAI adds Python-side orchestration to
   every one of the 6–8 calls per run for a graph of size one. Option (b) removes
   that layer; (a) keeps it; (c) keeps it for some agents. Favors (b).
2. **Dependency / security surface.** `crewai` + `crewai-tools` pull heavy,
   unused transitive dependencies (chromadb, lancedb, docker, pytube, …) on a
   floor-only version pin. Option (b) drops both trees; (c) keeps them and so
   saves nothing on this axis; (a) keeps them. Favors (b).
3. **Whether any CrewAI capability is on the roadmap.** Tools, memory, and
   delegation are used **nowhere** today and are not on the roadmap. There is no
   capability we would lose in practice. If that changes, CrewAI (or an
   equivalent) can be reintroduced behind the unchanged `BaseHydraAgent`
   interface. Because no roadmap capability depends on it, the framework is not
   earning its weight — favors (b) over the hedge in (c).

Option (b) wins on all three criteria; (c) is rejected because it pays the code
cost of a migration while keeping the dependency cost that motivated it; (a) is
rejected because it pays ongoing weight and cognitive cost for orchestration the
app does not use.

**Why "later" and not "now":** the migration touches the single hottest seam in
the runtime and must preserve the model-facing prompt to avoid silently changing
output quality. That deserves its own PR with a golden-transcript check and a
benchmark, not a rider on an ADR.

## Migration Path (Option b, for the follow-on PR)

### The single seam to change

Only `BaseHydraAgent.execute_with_retry` (`runtime/crewai/base_agent.py:313-319`)
changes. Replace:

```python
crew = Crew(agents=[task.agent], tasks=[task],
            process=Process.sequential, verbose=False)
result = crew.kickoff()
```

with a direct call, gated behind an env flag during the spike:

```python
if os.getenv("HYDRA_DIRECT_LLM", "").lower() in ("1", "true", "yes"):
    result = self._complete_direct(task)   # litellm.completion(...)
else:
    crew = Crew(agents=[task.agent], tasks=[task],
                process=Process.sequential, verbose=False)
    result = crew.kickoff()
```

`_complete_direct` assembles messages that reproduce CrewAI's prompt:

- **system**: the agent role/goal/backstory already built by
  `_build_backstory()` (`base_agent.py:129-144`).
- **user**: the decorated task description + `expected_output` produced by
  `create_task()` (`base_agent.py:152-170`).
- Calls `litellm.completion(model=..., messages=..., temperature=...)` using the
  model string and key the LLM was already configured with in
  `model_config.py`, and returns the assistant message content as a string.

### How contracts and telemetry are preserved

- **Contracts:** `validate_output` (`base_agent.py:172-189`) and the typed stage
  contracts in `runtime/crewai/contracts.py` consume a **string** and are called
  identically. As long as `_complete_direct` returns the model's text, every
  downstream contract (`GapAnalysis`, `TailoredDocuments`, `ATSResult`,
  `AuditVerdict`, `ExecutiveDecision`) is unaffected.
- **Telemetry:** the change is _inside_ the existing
  `with trace_agent_execution(...) as span:` block. `record_agent_result`,
  `record_agent_error`, `span.set_attribute("agent.attempt", …)`, and the retry
  accounting all stay exactly where they are. No span names or attributes change.
- **Fallback / retry:** `hydra_workflow._execute_with_fallback` and the
  `max_retries` loop are untouched; they operate one level above the seam.

### Test strategy

- Existing tests patch `runtime.crewai.base_agent.Crew` and assert
  `kickoff.call_count` (`tests/unit/test_base_agent.py:261-319`). With the flag
  **OFF** (default), these keep passing unchanged — this is the green-with-flag-off
  guarantee.
- Add parallel tests that set `HYDRA_DIRECT_LLM=1`, patch
  `litellm.completion`, and assert the same validated-dict outputs and the same
  telemetry spans, including the retry and failure paths.
- Add a **golden-transcript test**: capture the exact `messages` CrewAI sends for
  a representative agent and assert `_complete_direct` assembles the same
  system/user content (or explicitly document any intended difference).
- Add a small **benchmark note** (not a gating test) comparing wall-clock per call
  for Crew.kickoff vs. direct completion on a mocked/stubbed model, to quantify
  the orchestration overhead this ADR could only describe qualitatively.

### Rollback

- Immediate: set `HYDRA_DIRECT_LLM` unset/`false` to fall back to the Crew path
  with no redeploy of code.
- After the flag is removed and CrewAI deleted: revert the single migration
  commit and restore `crewai[anthropic]` / `crewai-tools` in `requirements.txt`.
  Because the seam is small and contract/telemetry boundaries are unchanged, the
  blast radius of a revert is one function.

## Consequences

### If we adopt Option (b) (recommended, later)

- **Positive:** `crewai` + `crewai-tools` and their unused transitive trees
  (chromadb, lancedb, docker, pytube, youtube-transcript-api, …) leave the
  dependency graph; the install shrinks and the supply-chain/version-pin surface
  narrows. Per-call orchestration overhead disappears. The runtime reads as what
  it is — prompt in, model call, JSON validated out — improving 2am
  debuggability.
- **Negative:** We now own ~a dozen lines of message assembly that CrewAI
  previously owned. Re-adopting tools/memory/delegation later means
  reintroducing a framework. A prompt-shape regression is possible if the
  golden-transcript check is sloppy — hence it is mandatory in the follow-on PR.

### If we keep Option (a) (status quo until the follow-on lands)

- **Positive:** No work; no risk of a prompt regression today.
- **Negative:** Continued dependency weight, floor-pin drift risk, and per-call
  overhead for orchestration the app does not use; the framework keeps misleading
  readers about the architecture.

### Neutral

- LiteLLM remains the transport in every option; model configuration
  (`model_config.py`) and provider selection are unaffected by this decision.
- This ADR does not change any runtime code. The optional env-flagged spike
  described above is **proposed future work**, to be delivered and benchmarked in
  its own PR with tests green when `HYDRA_DIRECT_LLM` is off.
