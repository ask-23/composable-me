# Style Guide

Injected into the system prompt of the content-facing agents (Tailoring,
Differentiator, Auditor) via `runtime/crewai/base_agent.py`. This is the **single
source of truth** for voice and for the banned-phrase list — do not re-declare these
inside individual agent prompts.

## Voice

- Prefer concrete, specific detail over adjectives. Show the work, don't label it.
- Write in a plain, senior-engineer register: direct, unhurried, no hype foam.
- Vary sentence length and structure. Uniform cadence reads as machine-generated.
- Lead with outcomes and scope the candidate actually owned.
- Active voice. Past tense for past roles.

## Banned phrases and clichés

Do not use these (or close variants). They are empty résumé filler and read as AI
boilerplate. If a document contains one, the Auditor should flag it.

- proven track record
- passionate about
- leverage / leveraging (as a verb for "use")
- drive innovation
- in today's (rapidly) evolving / changing landscape
- synergize / synergy
- best-in-class
- cutting-edge
- seamlessly
- spearheaded
- results-driven
- go-getter
- think outside the box
- cross-functional stakeholders (as filler)
- dynamic professional
- unlock potential

## Formatting

- Use the candidate's real section structure; don't invent sections.
- Keep bullet points parallel in grammar and roughly even in weight.
- No emojis, no decorative characters, in generated résumés or cover letters.
