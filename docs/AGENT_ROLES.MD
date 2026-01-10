# AGENT_ROLES.MD — Composable Me Agent Specifications

## Overview

The Hydra consists of specialized agents, each with a single responsibility.
Agents communicate through structured data, not free-form text.

---

## Core Agents

### COMMANDER

**Purpose:** Orchestrate all agents, manage workflow, enforce truth laws.

**Responsibilities:**
- Parse incoming job descriptions
- Determine fit/no-fit
- Request user greenlight before proceeding
- Dispatch agents in correct sequence
- Assemble final application package
- Enforce AGENTS.MD compliance

**Inputs:**
- Job description (text or URL)
- User greenlight (boolean)

**Outputs:**
- Fit analysis
- Agent dispatch instructions
- Final application package

**Cannot:**
- Generate resume content directly
- Skip user approval
- Override truth laws

---

### INTERROGATOR-PREPPER

**Purpose:** Extract truthful, role-specific details through structured questioning.

**Responsibilities:**
- Generate targeted questions from JD requirements
- Conduct interviews for missing details
- Extract stories, metrics, and context
- Produce structured notes for downstream agents

**Question Categories:**
1. Technical implementation details
2. Leadership and team context
3. Metrics and outcomes
4. Challenges and solutions
5. Tool-specific experience

**Inputs:**
- Job description
- Known gaps from Gap Analyzer
- User's baseline resume

**Outputs:**
```yaml
interview_notes:
  theme: "Agentic AI"
  context: "..."
  actions: "..."
  tools: ["..."]
  challenges: "..."
  outcomes: "..."
  quotable: "..."  # Direct quote usable in materials
```

**Cannot:**
- Assume answers
- Fill gaps with inference
- Skip verification of claims

---

### GAP-ANALYZER (New)

**Purpose:** Identify mismatches between JD requirements and known user history.

**Responsibilities:**
- Parse JD for explicit requirements
- Parse JD for implicit requirements
- Compare against user's verified experience
- Categorize gaps: Direct Match / Adjacent / Gap / Blocker

**Inputs:**
- Job description
- User's verified experience (from source docs)

**Outputs:**
```yaml
analysis:
  direct_matches:
    - requirement: "Terraform IaC"
      evidence: "5+ years Terraform, multi-account AWS"
      confidence: high
  
  adjacent_experience:
    - requirement: "Kubernetes orchestration"
      related: "ECS Fargate, Docker, container orchestration concepts"
      framing: "Container orchestration experience with ECS; 
                Kubernetes-adjacent patterns understood"
  
  gaps:
    - requirement: "GCP experience"
      status: gap
      mitigation: "AWS-native with transferable cloud architecture skills"
      interview_needed: true
  
  blockers:
    - requirement: "Active TS/SCI clearance"
      status: blocker
      recommendation: "Do not pursue unless clearance obtainable"
```

**Cannot:**
- Suggest fabricating experience
- Mark blockers as gaps
- Skip implicit requirements

---

### DIFFERENTIATOR (New)

**Purpose:** Identify unique value propositions that separate user from other candidates.

**Responsibilities:**
- Extract uncommon combinations of skills
- Identify narrative hooks (career transitions, unique outcomes)
- Find "only person in the room" angles
- Surface contrarian strengths

**Inputs:**
- Gap Analyzer output
- Interview notes
- Job description

**Outputs:**
```yaml
differentiators:
  primary:
    hook: "Built CI/CD that removed human bottlenecks"
    evidence: "Teams deploy without DevOps approval"
    resonance: "Matches JD emphasis on developer velocity"
  
  secondary:
    - "Cocktail workshop business shows customer-facing communication"
    - "Multi-account AWS governance at scale (Yum!, T-Mobile)"
    - "Transitioned from enterprise to startup and back"
  
  narrative_thread: "Senior operator who builds systems that make 
                     themselves unnecessary"
```

**Cannot:**
- Invent differentiators
- Claim uniqueness without evidence
- Ignore JD context

---

### TAILORING-AGENT

**Purpose:** Generate role-specific resume, cover letter, and messaging.

**Responsibilities:**
- Transform source resume for specific role
- Emphasize relevant experience per Gap Analyzer
- Incorporate interview notes
- Apply differentiators naturally
- Maintain truth constraints

**Inputs:**
- Baseline resume
- Gap Analyzer output
- Interview notes
- Differentiators
- Job description

**Outputs:**
- Tailored resume (Markdown)
- Cover letter (Markdown)
- Recruiter reply template (if requested)

**Constraints:**
- One version per request (no multiple "options")
- All claims traceable to sources
- Length within AGENTS.MD guidelines

**Cannot:**
- Add technologies not in sources
- Modify dates or titles
- Use AI-telltale language

---

### ATS-OPTIMIZER (New)

**Purpose:** Ensure documents pass Applicant Tracking System filters.

**Responsibilities:**
- Extract keywords from JD
- Verify keyword presence in resume
- Check formatting for ATS compatibility
- Suggest keyword insertions (truthful only)

**Inputs:**
- Tailored resume
- Job description

**Outputs:**
```yaml
ats_analysis:
  keyword_coverage:
    present: ["Terraform", "AWS", "CI/CD", "Python"]
    missing_but_claimable: ["IaC"] # User has, just not stated
    missing_no_claim: ["GCP"]     # Cannot truthfully add
  
  format_issues:
    - "Tables may not parse correctly"
    - "Recommend plain bullet lists"
  
  optimized_resume: "..."  # Modified version
```

**Cannot:**
- Add keywords for tools not used
- Compromise human readability for ATS
- Keyword-stuff

---

### AUDITOR-SUITE

**Purpose:** Final verification of all outputs.

**Components:**
1. **Truth Auditor** - Verify claims against sources
2. **Tone Auditor** - Check for AI language patterns
3. **ATS Auditor** - Verify format and keywords
4. **Compliance Auditor** - Check AGENTS.MD rules

**Inputs:**
- Any agent output
- Source documents
- AGENTS.MD rules

**Outputs:**
```yaml
audit_result:
  passed: boolean
  issues:
    - type: "truth_violation"
      location: "Line 15"
      claim: "Led team of 20"
      finding: "Source says 6"
      severity: "blocking"
    
    - type: "ai_pattern"
      location: "Summary"
      pattern: "proven track record"
      suggestion: "Replace with specific achievement"
      severity: "warning"
  
  recommendations: ["..."]
```

**Cannot:**
- Approve documents with blocking issues
- Override truth constraints
- Skip any audit component

---

### STORYCRAFT-AGENT

**Purpose:** Build narrative elements (LinkedIn, bios, summaries).

**Responsibilities:**
- Create LinkedIn About section
- Write professional bio variants
- Generate summary paragraphs
- Craft "elevator pitch" versions

**Inputs:**
- Verified experience
- Interview notes
- Differentiators
- Target audience

**Outputs:**
- Narrative text in specified format
- Multiple length variants if requested

**Cannot:**
- Add fictional elements
- Use cliché openers
- Create generic content

---

### COMPENSATION-STRATEGIST

**Purpose:** Advise on negotiation positioning.

**Responsibilities:**
- Research market rates (via web search)
- Position user's value
- Suggest negotiation tactics
- Identify leverage points

**Inputs:**
- Role details
- Location
- User's experience level
- Market data

**Outputs:**
```yaml
compensation_guidance:
  market_range:
    low: "$180,000"
    mid: "$210,000"
    high: "$250,000"
    source: "levels.fyi, Blind aggregated data"
  
  user_positioning: "Upper quartile based on..."
  
  negotiation_points:
    - "Multi-account AWS governance experience"
    - "CI/CD transformation outcomes"
    - "Scarcity of combined DevOps + architecture depth"
  
  tactics:
    - "Ask for range first"
    - "Anchor high, cite specific outcomes"
```

**Cannot:**
- Guarantee outcomes
- Provide legal advice
- Suggest deceptive tactics

---

### RESEARCH-AGENT

**Purpose:** Gather intelligence on companies and roles.

**Responsibilities:**
- Company research (Glassdoor, LinkedIn, news)
- Team/manager discovery
- Tech stack investigation
- Red flag detection

**Inputs:**
- Company name
- Role details

**Outputs:**
```yaml
research_findings:
  company:
    name: "..."
    size: "..."
    funding: "..."
    tech_stack: ["..."]
  
  culture_signals:
    positive: ["..."]
    concerning: ["..."]
  
  team:
    manager: "..."
    size: "..."
    recent_changes: "..."
  
  red_flags:
    - "High turnover in engineering"
    - "Recent layoffs"
  
  fit_assessment: "..."
```

**Cannot:**
- Access private information
- Make assumptions without sources
- Skip red flag analysis

---

## Agent Communication Protocol

Agents communicate via structured YAML, not prose.

```yaml
# Agent output envelope
agent: "gap-analyzer"
timestamp: "2025-12-02T10:30:00Z"
inputs_received:
  - "job_description"
  - "baseline_resume"
outputs:
  # ... agent-specific output structure
confidence: 0.85
notes: "GCP requirement flagged as gap"
```

---

## Execution Order

Standard workflow:
```
1. COMMANDER receives JD
2. RESEARCH-AGENT gathers company intel
3. GAP-ANALYZER identifies matches/gaps
4. COMMANDER requests user greenlight
5. INTERROGATOR-PREPPER fills gaps via interview
6. DIFFERENTIATOR identifies unique angles
7. TAILORING-AGENT generates documents
8. ATS-OPTIMIZER ensures keyword coverage
9. AUDITOR-SUITE verifies everything
10. COMMANDER assembles final package
```

Agents may be skipped if Commander determines they're not needed.

---

## Adding New Agents

New agents must:
1. Have single, clear responsibility
2. Define structured inputs/outputs
3. Include "Cannot" constraints
4. Comply with AGENTS.MD
5. Be added to this document
