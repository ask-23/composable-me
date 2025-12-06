# Agent Interface Specifications

All agents communicate via structured YAML. Each agent has a defined input schema and output schema.

## General Contract

Every agent MUST:
1. Accept inputs as a dictionary/object
2. Return outputs as structured YAML
3. Include metadata: agent_name, timestamp, confidence_level
4. Handle errors gracefully and return error information in YAML
5. Never fabricate information (Truth Laws from AGENTS.MD apply)

## Agent Interfaces

### 1. Commander Agent

**Input:**
```yaml
job_description: string
resume: string
research_data: object (optional)
```

**Output:**
```yaml
agent: "commander"
timestamp: "ISO-8601"
confidence: float (0.0-1.0)
action: "proceed" | "pass" | "discuss"
fit_analysis:
  overall_fit_percentage: float
  recommendation: string
  reasoning: string
  red_flags: list[string]
  auto_reject_triggered: boolean
  auto_reject_reasons: list[string]
next_step: string
```

---

### 2. Research Agent

**Input:**
```yaml
company_name: string
job_description: string
```

**Output:**
```yaml
agent: "research_agent"
timestamp: "ISO-8601"
confidence: float
company_intel:
  company_name: string
  industry: string
  size: string
  recent_news: list[string]
  red_flags: list[string]
  culture_notes: string
sources: list[string]
```

---

### 3. Gap Analyzer

**Input:**
```yaml
job_description: string
resume: string
research_data: object (optional)
```

**Output:**
```yaml
agent: "gap_analyzer"
timestamp: "ISO-8601"
confidence: float
requirements:
  - requirement: string
    classification: "direct_match" | "adjacent_experience" | "gap" | "blocker"
    evidence: string
    source_location: string
    confidence: float
fit_score: float
gaps: list[string]
blockers: list[string]
```

---

### 4. Interrogator-Prepper

**Input:**
```yaml
job_description: string
resume: string
gaps: list[string]
gap_analysis: object
```

**Output:**
```yaml
agent: "interrogator_prepper"
timestamp: "ISO-8601"
confidence: float
questions:
  - id: string
    theme: "technical" | "leadership" | "outcomes" | "tools"
    question: string
    format: "STAR+"
    target_gap: string
    why_asking: string
interview_notes:
  - question_id: string
    answer: string
    verified: boolean
    source_material: boolean
```

---

### 5. Differentiator

**Input:**
```yaml
job_description: string
resume: string
interview_notes: object
gap_analysis: object
```

**Output:**
```yaml
agent: "differentiator"
timestamp: "ISO-8601"
confidence: float
differentiators:
  - differentiator: string
    evidence: list[string]
    framing_suggestion: string
    relevance_to_jd: string
    uniqueness_score: float
positioning_angles: list[string]
```

---

### 6. Tailoring Agent

**Input:**
```yaml
job_description: string
resume: string
interview_notes: object
differentiators: object
gap_analysis: object
```

**Output:**
```yaml
agent: "tailoring_agent"
timestamp: "ISO-8601"
confidence: float
tailored_resume:
  format: "markdown"
  content: string
cover_letter:
  format: "markdown"
  content: string
  word_count: int
sources_used: list[string]
```

---

### 7. ATS Optimizer

**Input:**
```yaml
job_description: string
tailored_resume: string
cover_letter: string
```

**Output:**
```yaml
agent: "ats_optimizer"
timestamp: "ISO-8601"
confidence: float
keyword_analysis:
  required_keywords: list[string]
  present_keywords: list[string]
  missing_keywords: list[string]
  claimable_missing: list[string]
  unclaimable_missing: list[string]
suggestions: list[string]
ats_score: float
formatting_issues: list[string]
```

---

### 8. Auditor Suite

**Input:**
```yaml
job_description: string
resume: string
tailored_resume: string
cover_letter: string
interview_notes: object
all_agent_outputs: object
```

**Output:**
```yaml
agent: "auditor_suite"
timestamp: "ISO-8601"
confidence: float
audits:
  truth_audit:
    passed: boolean
    issues: list[object]
    blocking_issues: list[object]
  tone_audit:
    passed: boolean
    ai_patterns_detected: list[string]
    issues: list[object]
  ats_audit:
    passed: boolean
    keyword_coverage: float
    issues: list[object]
  compliance_audit:
    passed: boolean
    rule_violations: list[object]
overall_passed: boolean
requires_revision: boolean
revision_instructions: list[string]
```

---

## Error Handling

All agents MUST handle errors and return:

```yaml
agent: "agent_name"
timestamp: "ISO-8601"
error: true
error_type: "validation_error" | "processing_error" | "external_service_error"
error_message: string
error_details: object
recoverable: boolean
retry_suggested: boolean
```

---

## Validation Rules

1. All YAML must be valid and parseable
2. Required fields must be present
3. Confidence scores must be 0.0-1.0
4. Timestamps must be ISO-8601 format
5. All claims must reference source material
6. No fabricated data allowed

---

## Integration Points

The integration framework (Stream A) will:
1. Validate all agent inputs before calling
2. Validate all agent outputs after receiving
3. Handle errors and retry logic
4. Pass context between agents
5. Maintain audit trail of all agent interactions
