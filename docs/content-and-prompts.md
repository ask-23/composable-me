# Content and Prompts

How the model-facing text of Composable Me is organized, and how to change it safely.
Prompts are treated as source code: named, scoped, versioned, and free of duplicated
rules.

## Where prompts live

| Text                         | Location                  | Injected by                        |
| ---------------------------- | ------------------------- | ---------------------------------- |
| Per-agent prompt             | `agents/<name>/prompt.md` | `BaseHydraAgent._load_prompt`      |
| Truth rules (all agents)     | `docs/AGENTS.MD`          | `BaseHydraAgent._load_truth_rules` |
| Style guide + banned phrases | `docs/STYLE_GUIDE.MD`     | `BaseHydraAgent._load_style_guide` |

Every agent (except Executive Synthesizer, which has its own
`agents/executive-synthesizer/prompt.md`) loads its markdown prompt by path. At run
time `base_agent` assembles the system prompt as:

```
<agent prompt.md>
+ TRUTH RULES (from docs/AGENTS.MD)          # always
+ STYLE GUIDE (from docs/STYLE_GUIDE.MD)     # content agents only
```

The style guide is injected only for the content-facing agents (Tailoring,
Differentiator, Auditor) — see `_needs_style_guide`.

## Single sources of truth

Two things must **never** be duplicated inside individual prompts, because copies drift:

- **Truth rules** — the inviolable "don't fabricate" contract. Edit `docs/AGENTS.MD`.
- **Banned phrases** — the résumé-cliché blocklist the Auditor enforces. Edit
  `docs/STYLE_GUIDE.MD`.

The Tailoring and Auditor prompts reference these injected docs rather than restating
them.

## Prompt structure

A prompt should separate: role/identity, task, constraints, input expectations, and an
explicit output schema. Output is parsed as **JSON** by `BaseHydraAgent.validate_output`
(fenced blocks are stripped; only trailing-comma repair is applied — no lossy quote
substitution). `create_task` additionally appends a hard instruction to return only
valid JSON with `agent` / `timestamp` / `confidence` fields, so the JSON contract is
enforced at the task layer regardless of a prompt's illustrative examples.

## How output style is controlled

- **Voice and banned phrases**: `docs/STYLE_GUIDE.MD`.
- **Truthfulness**: `docs/AGENTS.MD`, verified at run time by the Auditor.
- **Model per agent**: `runtime/crewai/model_config.py` (temperature + provider).

## Editing safely

1. Change the markdown; no code change is needed for prompt/rule edits.
2. Keep the output schema in the prompt aligned with what the workflow reads via the
   typed contracts (`runtime/crewai/contracts.py`). If you change a field name a
   downstream stage depends on, update the contract's `from_raw`.
3. Run `pytest tests/unit` — prompt-assembly and contract-coercion tests will catch
   structural regressions. Output _quality_ changes require a live model to evaluate.

## Known follow-ups

These are tracked, not yet done, and safe to tackle independently:

- **Example genericization.** Several prompts use one candidate archetype
  (cloud/DevOps) and bracketed placeholders like `[Current Company]` in their examples.
  They are illustrative, not PII, but a broader example set would generalize the prompts.
- **YAML-vs-JSON examples.** A few prompts show YAML-shaped output _examples_ while the
  parser (and the task-level instruction) require JSON. The JSON instruction wins at run
  time, but converting those examples to JSON would remove the mixed signal.
