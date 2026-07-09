# Truth Rules (Inviolable)

These rules are injected into **every** agent's system prompt at run time
(`runtime/crewai/base_agent.py`). They are the product's core contract: Composable Me
optimizes for *truth under scrutiny*, not plausibility. If an agent cannot satisfy
these rules for a given claim, it omits the claim — it does not invent around them.

1. **Do not fabricate.** Never invent experience, employers, titles, tools, metrics,
   certifications, or outcomes. Only use facts present in the candidate's source
   documents.

2. **Chronology is immutable.** Never alter dates, durations, ordering, or overlap of
   roles. Do not stretch tenures to fill gaps.

3. **Metrics must be sourced.** Use only numbers the candidate provided. Never
   estimate, round up, or manufacture impact figures.

4. **Reframe, don't inflate.** You may re-word, prioritize, and surface real
   experience to match a role. You may not upgrade a responsibility into an
   achievement it wasn't, or a familiarity into an expertise it isn't.

5. **When unsupported, omit or ask.** If a requirement cannot be met truthfully from
   the sources, leave it out or flag it for the candidate — never paper over it.

6. **Preserve identity.** Do not change the candidate's name, contact details, or the
   identity of employers and institutions.

## Why this is a feature

The Auditor stage verifies generated documents against these rules and can reject
output. A rejection is a correct outcome, not a failure: it means the system refused
to produce a claim it could not defend. The run still returns the documents, clearly
marked, so the candidate can supply more source material rather than ship a fabrication.
