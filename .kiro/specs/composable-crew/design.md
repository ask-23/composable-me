# Design Document

## Overview

Composable Me Hydra is a multi-agent orchestration system built on CrewAI that coordinates specialized AI agents to generate truthful, human-sounding job application materials. The system enforces strict truth constraints while optimizing for ATS compatibility and AI detection avoidance.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Interface Layer                         │
│  (CLI: run.sh, quick_crew.py, crew.py)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    Commander (Orchestrator)                      │
│  - Workflow state management                                     │
│  - Agent dispatch and coordination                               │
│  - Truth law enforcement                                         │
│  - User interaction (greenlight)                                 │
└─────┬──────┬──────┬──────┬──────┬──────┬──────┬────────────────┘
      │      │      │      │      │      │      │
      ▼      ▼      ▼      ▼      ▼      ▼      ▼
┌─────────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐
│Research │ │Gap │ │Int.│ │Diff│ │Tail│ │ATS │ │Aud.│
│ Agent  │ │Ana.│ │Prep│ │    │ │    │ │Opt.│ │Ste.│
└────┬────┘ └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘
     │        │      │      │      │      │      │
     └────────┴──────┴──────┴──────┴──────┴──────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    LLM Provider Layer                            │
│  (OpenRouter → Claude/GPT-4/etc)                                │
└──────────────────────────────────────────────────────────────────┘
```

### Agent Communication Flow

```
Input (JD + Resume)
  │
  ▼
Commander: Parse & Validate
  │
  ▼
Research Agent: Company Intel (optional)
  │
  ▼
Gap Analyzer: Requirement Mapping
  │
  ▼
Commander: Fit Analysis → User Greenlight?
  │
  ├─ NO → Archive & Exit
  │
  └─ YES ▼
     │
     Interrogator-Prepper: Generate Questions
     │
     ▼
     User: Provide Answers (offline)
     │
     ▼
     Differentiator: Identify Unique Value
     │
     ▼
     Tailoring Agent: Generate Resume + Cover Letter
     │
     ▼
     ATS Optimizer: Keyword Optimization
     │
     ▼
     Auditor Suite: Multi-Stage Verification
     │
     ├─ FAIL → Retry Loop (max 2x) → Agent
     │
     └─ PASS ▼
        │
        Commander: Assemble Final Package
        │
        ▼
        Output (Resume, Cover Letter, Audit Trail)
```

## Components and Interfaces

### 1. Commander Agent

**Responsibility:** Orchestrate workflow, enforce truth laws, manage state

**Interface:**
```python
class Commander:
    def analyze_fit(jd: str, resume: str) -> FitAnalysis
    def request_greenlight(fit: FitAnalysis) -> bool
    def dispatch_agent(agent: Agent, context: dict) -> AgentOutput
    def assemble_package(outputs: dict) -> ApplicationPackage
    def handle_error(error: Error, agent: Agent) -> ErrorResolution
```

**Inputs:**
- Job description (text/file)
- Resume (text/file)
- User greenlight (boolean)

**Outputs:**
- Fit analysis (YAML)
- Final application package (YAML)
- Audit trail (YAML)

### 2. Research Agent

**Responsibility:** Gather company and role intelligence

**Interface:**
```python
class ResearchAgent:
    def extract_company_name(jd: str) -> str
    def gather_company_info(company: str) -> CompanyIntel
    def identify_red_flags(intel: CompanyIntel) -> List[RedFlag]
    def discover_tech_stack(company: str) -> TechStack
```

**Inputs:**
- Job description
- Company name (extracted or provided)

**Outputs:**
```yaml
research_output:
  company:
    name: str
    size: str  # startup/small/medium/large/enterprise
    funding: str  # bootstrap/seed/series-X/public
    tech_stack: List[str]
  red_flags:
    - severity: critical|warning|info
      description: str
      source: str
  culture_signals:
    positive: List[str]
    concerning: List[str]
  sources: List[str]
  data_age: str
```

### 3. Gap Analyzer Agent

**Responsibility:** Map JD requirements to candidate experience

**Interface:**
```python
class GapAnalyzer:
    def extract_requirements(jd: str) -> List[Requirement]
    def map_to_experience(req: Requirement, resume: str) -> Classification
    def calculate_fit(mappings: List[Classification]) -> float
```

**Inputs:**
- Job description
- Resume
- Research output (optional)

**Outputs:**
```yaml
gap_analysis:
  requirements:
    - requirement: str
      classification: direct_match|adjacent|gap|blocker
      evidence: str  # quote from resume
      confidence: float
      framing: str  # for adjacent/gap
  fit_percentage: float
  summary:
    direct_matches: int
    adjacent: int
    gaps: int
    blockers: int
```


### 4. Interrogator-Prepper Agent

**Responsibility:** Generate targeted interview questions to extract truthful details

**Interface:**
```python
class InterrogatorPrepper:
    def generate_questions(gaps: List[Gap], jd: str) -> List[Question]
    def group_by_theme(questions: List[Question]) -> Dict[str, List[Question]]
    def format_star_plus(question: Question) -> str
```

**Inputs:**
- Gap analysis output
- Job description

**Outputs:**
```yaml
interview_questions:
  themes:
    technical:
      - question: str
        focus: str  # what we're trying to learn
        star_elements: [situation, task, actions, results, proof]
    leadership:
      - question: str
        focus: str
    outcomes:
      - question: str
        focus: str
  total_questions: int  # 8-12
```

### 5. Differentiator Agent

**Responsibility:** Identify unique value propositions

**Interface:**
```python
class Differentiator:
    def identify_skill_combinations(resume: str, jd: str) -> List[Combination]
    def extract_quantified_outcomes(resume: str, notes: str) -> List[Outcome]
    def find_narrative_thread(resume: str) -> str
    def assess_relevance(diff: Differentiator, jd: str) -> float
```

**Inputs:**
- Resume
- Interview notes
- Gap analysis
- Job description

**Outputs:**
```yaml
differentiators:
  primary:
    hook: str  # one sentence
    evidence: str  # specific proof
    resonance: str  # why it matters for this JD
  secondary:
    - differentiator: str
      evidence: str
  narrative_thread: str
```

### 6. Tailoring Agent

**Responsibility:** Generate tailored resume and cover letter

**Interface:**
```python
class TailoringAgent:
    def generate_resume(resume: str, gaps: GapAnalysis, diffs: Differentiators, jd: str) -> str
    def generate_cover_letter(resume: str, diffs: Differentiators, jd: str) -> str
    def apply_style_guide(content: str) -> str
    def verify_sources(content: str, sources: List[str]) -> bool
```

**Inputs:**
- Baseline resume
- Gap analysis
- Differentiators
- Interview notes
- Job description

**Outputs:**
```yaml
tailored_documents:
  resume:
    format: markdown
    content: str
    source_mapping:
      - claim: str
        source: str
        location: str
  cover_letter:
    format: markdown
    content: str
    word_count: int
  rationale: str
```

### 7. ATS Optimizer Agent

**Responsibility:** Ensure ATS compatibility and keyword coverage

**Interface:**
```python
class ATSOptimizer:
    def extract_keywords(jd: str) -> List[Keyword]
    def check_coverage(resume: str, keywords: List[Keyword]) -> Coverage
    def suggest_insertions(keywords: List[Keyword], resume: str) -> List[Suggestion]
    def validate_format(resume: str) -> List[Issue]
```

**Inputs:**
- Tailored resume
- Job description

**Outputs:**
```yaml
ats_analysis:
  keyword_coverage:
    present: List[str]
    missing_claimable: List[str]
    missing_not_claimable: List[str]
  format_issues: List[str]
  suggestions:
    - keyword: str
      location: str
      truthful: bool
```

### 8. Auditor Suite Agent

**Responsibility:** Multi-stage verification (truth, tone, ATS, compliance)

**Interface:**
```python
class AuditorSuite:
    def truth_audit(content: str, sources: List[str]) -> TruthAudit
    def tone_audit(content: str, style_guide: StyleGuide) -> ToneAudit
    def ats_audit(content: str, jd: str) -> ATSAudit
    def compliance_audit(content: str, rules: Rules) -> ComplianceAudit
```

**Inputs:**
- Tailored documents
- Source documents
- AGENTS.MD rules
- STYLE_GUIDE.MD patterns

**Outputs:**
```yaml
audit_result:
  passed: bool
  truth_audit:
    status: pass|fail
    issues:
      - claim: str
        source_missing: bool
        severity: blocking|warning
  tone_audit:
    status: pass|conditional|fail
    ai_patterns_found: List[str]
    sentence_variation: float
  ats_audit:
    status: pass|fail
    keyword_coverage: float
  compliance_audit:
    status: pass|fail
    violations: List[str]
  overall_verdict: approved|needs_revision
```

## Data Models

### Core Data Structures

```python
@dataclass
class JobDescription:
    text: str
    company: Optional[str]
    role: str
    requirements: List[str]
    
@dataclass
class Resume:
    text: str
    format: str  # markdown, pdf, text
    employment_history: List[Employment]
    skills: List[str]
    
@dataclass
class Employment:
    company: str
    title: str
    start_date: str
    end_date: Optional[str]
    achievements: List[str]
    
@dataclass
class Requirement:
    text: str
    type: str  # explicit, implicit, cultural
    priority: str  # must_have, nice_to_have
    
@dataclass
class Classification:
    requirement: Requirement
    category: str  # direct_match, adjacent, gap, blocker
    evidence: Optional[str]
    confidence: float
    framing: Optional[str]
    
@dataclass
class Differentiator:
    hook: str
    evidence: str
    resonance: str
    relevance_score: float
    
@dataclass
class AuditIssue:
    type: str  # truth, tone, ats, compliance
    severity: str  # blocking, warning, recommendation
    location: str
    description: str
    fix: str
    
@dataclass
class WorkflowState:
    id: str
    status: str  # in_progress, awaiting_user, complete, failed
    current_stage: str
    inputs: Dict[str, Any]
    agent_outputs: Dict[str, Any]
    user_interactions: List[Dict]
    errors: List[Dict]
    audit_trail: List[Dict]
```

### State Machine

```
States:
- INITIALIZED: Inputs received, ready to start
- RESEARCHING: Research Agent gathering intel
- ANALYZING: Gap Analyzer mapping requirements
- AWAITING_GREENLIGHT: Waiting for user approval
- INTERVIEWING: Interrogator-Prepper generating questions
- DIFFERENTIATING: Identifying unique value props
- GENERATING: Tailoring Agent creating documents
- OPTIMIZING: ATS Optimizer checking keywords
- AUDITING: Auditor Suite verifying output
- RETRYING: Fixing audit failures
- COMPLETE: Final package ready
- FAILED: Unrecoverable error
- ARCHIVED: User declined to proceed

Transitions:
INITIALIZED → RESEARCHING (if Research Agent available)
INITIALIZED → ANALYZING (if no Research Agent)
RESEARCHING → ANALYZING
ANALYZING → AWAITING_GREENLIGHT
AWAITING_GREENLIGHT → INTERVIEWING (user approves)
AWAITING_GREENLIGHT → ARCHIVED (user declines)
INTERVIEWING → DIFFERENTIATING
DIFFERENTIATING → GENERATING
GENERATING → OPTIMIZING
OPTIMIZING → AUDITING
AUDITING → COMPLETE (pass)
AUDITING → RETRYING (fail, retries < 2)
AUDITING → FAILED (fail, retries >= 2)
RETRYING → GENERATING (route back to responsible agent)
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Input Validation Properties

**Property 1: Input parsing completeness**
*For any* valid job description input (text or file), the system should successfully parse it and extract structured data without errors.
**Validates: Requirements 1.1**

**Property 2: Resume parsing completeness**
*For any* valid resume input (text or file), the system should successfully parse it and extract employment history and skills.
**Validates: Requirements 1.2**

**Property 3: Workflow initialization**
*For any* valid job description and resume inputs, providing them to the Commander should transition the workflow state to "in_progress".
**Validates: Requirements 1.3**

**Property 4: Missing information handling**
*For any* job description with missing required fields (company name, role title), the system should request clarification rather than proceeding with incomplete data.
**Validates: Requirements 1.4**

### Fit Analysis Properties

**Property 5: Requirement extraction completeness**
*For any* job description, the system should extract a non-empty list of requirements (both explicit and implicit).
**Validates: Requirements 2.1**

**Property 6: Classification completeness**
*For any* set of extracted requirements and resume, each requirement should have exactly one classification (direct_match, adjacent, gap, or blocker).
**Validates: Requirements 2.2, 2.3**

**Property 7: Fit percentage bounds**
*For any* classification result, the calculated fit percentage should be between 0 and 100 inclusive.
**Validates: Requirements 2.4**

**Property 8: Recommendation validity**
*For any* completed fit analysis, the recommendation should be exactly one of: PROCEED, PASS, or DISCUSS.
**Validates: Requirements 2.5**

### Red Flag Detection Properties

**Property 9: Auto-reject checking**
*For any* job description, the system should check all auto-reject criteria (contract-to-hire, level, compensation, relocation).
**Validates: Requirements 3.1**

**Property 10: Auto-reject recommendation**
*For any* job description containing auto-reject criteria, the Commander's recommendation should be PASS.
**Validates: Requirements 3.2**

**Property 11: Red flag presentation ordering**
*For any* workflow where red flags are identified, they must be presented to the user before the greenlight request.
**Validates: Requirements 3.4**

### Workflow Gating Properties

**Property 12: Greenlight enforcement**
*For any* workflow execution, document generation agents (Tailoring, ATS Optimizer) should never execute without user greenlight.
**Validates: Requirements 4.1, 4.5**

**Property 13: Greenlight continuation**
*For any* workflow where the user provides greenlight, the system should proceed to the Interrogator-Prepper stage.
**Validates: Requirements 4.2**

**Property 14: Greenlight termination**
*For any* workflow where the user declines greenlight, the workflow state should transition to "archived" and no further agents should execute.
**Validates: Requirements 4.3**

### Interview Question Properties

**Property 15: Question count bounds**
*For any* gap analysis result, the Interrogator-Prepper should generate between 8 and 12 questions inclusive.
**Validates: Requirements 5.1**

**Property 16: Question grouping completeness**
*For any* set of generated questions, every question should belong to exactly one theme group.
**Validates: Requirements 5.2**

**Property 17: Answer storage round-trip**
*For any* user-provided answer to an interview question, storing it as source material and then retrieving it should return the same content.
**Validates: Requirements 5.4**

### Differentiator Properties

**Property 18: Differentiator count bounds**
*For any* completed differentiator analysis, the output should contain between 2 and 3 primary differentiators inclusive.
**Validates: Requirements 6.3**

**Property 19: Differentiator structure completeness**
*For any* identified differentiator, it should contain all required fields: hook, evidence, and framing.
**Validates: Requirements 6.3**

**Property 20: Differentiator relevance**
*For any* identified differentiator, it should reference at least one keyword from the job description.
**Validates: Requirements 6.4**

### Document Generation Properties

**Property 21: Resume format validity**
*For any* generated resume, it should be valid Markdown that parses without errors.
**Validates: Requirements 7.1**

**Property 22: Cover letter word count bounds**
*For any* generated cover letter, the word count should be between 250 and 400 inclusive.
**Validates: Requirements 7.4**

**Property 23: Source traceability**
*For any* claim in generated documents, it should trace to a source document (resume, interview notes, or user confirmation).
**Validates: Requirements 7.5, 9.1**

### Anti-AI Detection Properties

**Property 24: Forbidden phrase absence**
*For any* generated content, it should not contain any phrases from the forbidden list in STYLE_GUIDE.MD.
**Validates: Requirements 8.1**

**Property 25: Sentence length variation**
*For any* generated content, the standard deviation of sentence lengths should be greater than 5 words (indicating variation).
**Validates: Requirements 8.2**

**Property 26: Human element presence**
*For any* generated content, it should contain at least one human element (contraction, aside, or sentence fragment).
**Validates: Requirements 8.4**

### Truth Law Properties

**Property 27: Chronology preservation**
*For any* employment dates in the source resume, they should appear unchanged in the generated resume (no reordering, no date modifications).
**Validates: Requirements 9.3**

**Property 28: Technology verification**
*For any* technology or tool mentioned in generated documents, it should be present in the source documents.
**Validates: Requirements 9.4**

**Property 29: Adjacent experience framing**
*For any* requirement classified as "adjacent", the generated content should use transferable language (e.g., "familiar with", "experience with similar") rather than direct expertise claims.
**Validates: Requirements 9.5**

### ATS Optimization Properties

**Property 30: Keyword extraction completeness**
*For any* job description, the ATS Optimizer should extract a non-empty list of keywords.
**Validates: Requirements 10.1**

**Property 31: Keyword coverage checking**
*For any* extracted keyword, the ATS Optimizer should check whether it appears in the tailored resume.
**Validates: Requirements 10.2**

**Property 32: No fabrication for missing keywords**
*For any* keyword that is missing and not claimable, the system should note it as a gap without adding it to the resume.
**Validates: Requirements 10.4**

### Audit Properties

**Property 33: Audit execution completeness**
*For any* generated document, all four audit types (truth, tone, ATS, compliance) should execute.
**Validates: Requirements 11.1, 11.3, 11.4, 11.5**

**Property 34: Issue severity categorization**
*For any* identified audit issue, it should have exactly one severity level: blocking, warning, or recommendation.
**Validates: Requirements 12.1**

**Property 35: Blocking issue retry**
*For any* audit result with blocking issues, the Commander should route the output back to the responsible agent for regeneration.
**Validates: Requirements 12.2**

**Property 36: Retry limit enforcement**
*For any* workflow with persistent audit failures, after 2 retry loops the system should escalate to the user rather than continuing to retry.
**Validates: Requirements 12.5**

### Workflow Ordering Properties

**Property 37: Agent execution sequence**
*For any* workflow execution, agents should execute in the correct order: Research → Gap Analysis → [Greenlight] → Interrogator → Differentiator → Tailoring → ATS → Auditor.
**Validates: Requirements 13.3, 15.1, 15.2, 15.4**

**Property 38: Final package completeness**
*For any* completed workflow, the final package should contain resume, cover letter, and audit trail.
**Validates: Requirements 13.5**

### Communication Format Properties

**Property 39: YAML format validity**
*For any* agent output, it should be valid YAML that parses without errors.
**Validates: Requirements 14.1, 14.3**

**Property 40: YAML structure completeness**
*For any* agent output in YAML format, it should contain required fields: agent name, timestamp, and confidence level.
**Validates: Requirements 14.2**

### Audit Trail Properties

**Property 41: Agent invocation logging**
*For any* agent execution, the system should log the invocation with a timestamp in the audit trail.
**Validates: Requirements 16.1**

**Property 42: Source tracking completeness**
*For any* claim in generated documents, the audit trail should contain a source reference (document and location).
**Validates: Requirements 16.3**

**Property 43: Audit trail inclusion**
*For any* completed workflow, the final package should include the complete audit trail.
**Validates: Requirements 16.4**

### Error Handling Properties

**Property 44: Single retry on error**
*For any* agent error, the system should retry exactly once before escalating or proceeding.
**Validates: Requirements 17.1**

**Property 45: Graceful degradation**
*For any* recoverable agent failure, the workflow should continue with available data rather than terminating completely.
**Validates: Requirements 17.3, 17.5**


## Error Handling

### Error Categories

1. **Input Errors**
   - Invalid file format
   - Missing required fields
   - Unparseable content
   - **Handling:** Request clarification from user, provide helpful error messages

2. **Agent Execution Errors**
   - LLM API failures
   - Timeout errors
   - Malformed agent output
   - **Handling:** Retry once, then escalate or proceed with degraded functionality

3. **Validation Errors**
   - YAML parsing failures
   - Schema validation failures
   - Missing required fields in agent output
   - **Handling:** Request regeneration from agent with specific format guidance

4. **Audit Failures**
   - Truth violations (fabricated claims)
   - Tone violations (AI patterns detected)
   - ATS failures (missing keywords)
   - Compliance violations (rule breaches)
   - **Handling:** Route back to responsible agent with specific issues (max 2 retries)

5. **External Service Errors**
   - OpenRouter API unavailable
   - Rate limiting
   - Network failures
   - **Handling:** Exponential backoff, cache failures, proceed with degraded functionality

### Retry Strategy

```python
class RetryPolicy:
    max_agent_retries = 1  # For agent execution errors
    max_audit_retries = 2  # For audit failures
    
    def should_retry(error: Error, attempt: int) -> bool:
        if error.type == "agent_execution":
            return attempt < max_agent_retries
        elif error.type == "audit_failure":
            return attempt < max_audit_retries
        elif error.type == "external_service":
            return attempt < 3  # More retries for transient failures
        else:
            return False
    
    def backoff_delay(attempt: int) -> float:
        return min(2 ** attempt, 30)  # Exponential backoff, max 30s
```

### Error Recovery Workflow

```
Agent Error Detected
  │
  ├─ Attempt < Max Retries?
  │  ├─ YES → Retry with same inputs
  │  └─ NO → Can workflow proceed without this agent?
  │         ├─ YES → Continue with degraded functionality
  │         └─ NO → Escalate to user
  │
Audit Failure Detected
  │
  ├─ Severity = Blocking?
  │  ├─ YES → Route back to responsible agent
  │  │        │
  │  │        ├─ Regenerate with specific fixes
  │  │        │
  │  │        └─ Re-audit
  │  │           │
  │  │           ├─ Pass → Continue
  │  │           └─ Fail → Retry count < 2?
  │  │                    ├─ YES → Retry
  │  │                    └─ NO → Escalate to user
  │  │
  │  └─ NO (Warning/Recommendation) → Flag but continue
```

## Testing Strategy

### Unit Testing

Each agent should have unit tests that verify:
- Input validation and parsing
- Output structure and format (YAML validity)
- Required fields presence
- Error handling for invalid inputs
- Edge cases (empty inputs, malformed data)

Example unit tests:
```python
def test_gap_analyzer_output_structure():
    """Verify Gap Analyzer produces valid YAML with required fields"""
    jd = load_test_jd()
    resume = load_test_resume()
    
    output = gap_analyzer.execute(jd, resume)
    parsed = yaml.safe_load(output)
    
    assert "requirements" in parsed
    assert "fit_percentage" in parsed
    assert 0 <= parsed["fit_percentage"] <= 100
    
def test_tailoring_agent_no_fabrication():
    """Verify Tailoring Agent only uses source material"""
    resume = load_test_resume()
    jd = load_test_jd()
    
    output = tailoring_agent.generate_resume(resume, jd)
    
    # All technologies mentioned should be in source
    mentioned_tech = extract_technologies(output)
    source_tech = extract_technologies(resume)
    assert mentioned_tech.issubset(source_tech)
```

### Property-Based Testing

Property-based tests will verify universal properties across many randomly generated inputs. We'll use **Hypothesis** (Python) as the PBT library.

Each property-based test should:
- Run a minimum of 100 iterations
- Generate diverse inputs (valid and edge cases)
- Tag the test with the property number from this design doc
- Use smart generators that constrain to valid input space

Example property-based tests:
```python
from hypothesis import given, strategies as st

@given(jd=st.text(min_size=100), resume=st.text(min_size=100))
def test_property_6_classification_completeness(jd, resume):
    """
    Feature: composable-me-hydra, Property 6: Classification completeness
    For any set of extracted requirements and resume, each requirement 
    should have exactly one classification.
    """
    gap_analysis = gap_analyzer.execute(jd, resume)
    
    for req in gap_analysis.requirements:
        classifications = [req.direct_match, req.adjacent, req.gap, req.blocker]
        assert sum(classifications) == 1, "Each requirement must have exactly one classification"

@given(content=st.text(min_size=100))
def test_property_24_forbidden_phrase_absence(content):
    """
    Feature: composable-me-hydra, Property 24: Forbidden phrase absence
    For any generated content, it should not contain forbidden phrases.
    """
    forbidden_phrases = load_forbidden_phrases()  # from STYLE_GUIDE.MD
    
    content_lower = content.lower()
    for phrase in forbidden_phrases:
        assert phrase.lower() not in content_lower, f"Forbidden phrase found: {phrase}"

@given(dates=st.lists(st.dates(), min_size=2, max_size=10))
def test_property_27_chronology_preservation(dates):
    """
    Feature: composable-me-hydra, Property 27: Chronology preservation
    For any employment dates in source resume, they should appear unchanged 
    in generated resume.
    """
    source_resume = create_resume_with_dates(dates)
    generated_resume = tailoring_agent.generate_resume(source_resume, test_jd)
    
    source_dates = extract_dates(source_resume)
    generated_dates = extract_dates(generated_resume)
    
    assert source_dates == generated_dates, "Dates must not be modified"
```

### Integration Testing

Integration tests verify the full workflow:
```python
def test_full_workflow_happy_path():
    """Test complete workflow from input to output"""
    jd = load_test_jd()
    resume = load_test_resume()
    
    hydra = HydraCrew(jd, resume)
    result = hydra.run()
    
    assert result["audit"]["passed"] == True
    assert "resume" in result["documents"]
    assert "cover_letter" in result["documents"]
    assert "audit_trail" in result

def test_workflow_with_audit_failure_retry():
    """Test that audit failures trigger retry loop"""
    jd = load_test_jd()
    resume = load_test_resume()
    
    # Mock Tailoring Agent to produce content with fabrication
    with mock_fabricated_content():
        hydra = HydraCrew(jd, resume)
        result = hydra.run()
        
        # Should have retried and fixed
        assert result["audit"]["retry_count"] > 0
        assert result["audit"]["passed"] == True
```

### Prompt Testing

Test that agent prompts produce expected output structure:
```python
def test_gap_analyzer_prompt_structure():
    """Verify Gap Analyzer prompt produces valid YAML structure"""
    response = llm.complete(gap_analyzer_prompt + test_jd + test_resume)
    parsed = yaml.safe_load(response)
    
    assert "requirements" in parsed
    assert "fit_percentage" in parsed
    assert all(req["classification"] in ["direct_match", "adjacent", "gap", "blocker"] 
               for req in parsed["requirements"])
```

### Test Coverage Goals

- Unit tests: 80% code coverage
- Property-based tests: All 45 correctness properties implemented
- Integration tests: All major workflows (happy path, error paths, retry loops)
- Prompt tests: All 8 agents

### Testing Tools

- **pytest**: Test runner
- **Hypothesis**: Property-based testing library
- **pytest-mock**: Mocking for LLM calls
- **pyyaml**: YAML validation
- **coverage.py**: Code coverage measurement


## Implementation Details

### Technology Stack

- **Language:** Python 3.10+
- **Framework:** CrewAI 0.86.0+
- **LLM Provider:** OpenRouter (supports multiple models)
- **Default Model:** anthropic/claude-sonnet-4-20250514
- **Data Format:** YAML for agent communication
- **Testing:** pytest + Hypothesis (PBT)

### File Structure

```
composable-me/
├── agents/                    # Agent prompt definitions
│   ├── commander/
│   │   └── prompt.md
│   ├── research-agent/
│   │   └── prompt.md
│   ├── gap-analyzer/
│   │   └── prompt.md
│   ├── interrogator-prepper/
│   │   └── prompt.md
│   ├── differentiator/
│   │   └── prompt.md
│   ├── tailoring-agent/
│   │   └── prompt.md
│   ├── ats-optimizer/
│   │   └── prompt.md
│   └── auditor-suite/
│       └── prompt.md
│
├── runtime/
│   └── crewai/
│       ├── __init__.py
│       ├── crew.py           # Full implementation
│       ├── quick_crew.py     # Simplified runner
│       └── agents/           # Agent implementations
│           ├── __init__.py
│           ├── base.py       # Base agent class
│           ├── commander.py
│           ├── research.py
│           ├── gap_analyzer.py
│           ├── interrogator.py
│           ├── differentiator.py
│           ├── tailoring.py
│           ├── ats_optimizer.py
│           └── auditor.py
│
├── tests/
│   ├── unit/
│   │   ├── test_commander.py
│   │   ├── test_gap_analyzer.py
│   │   ├── test_interrogator.py
│   │   ├── test_differentiator.py
│   │   ├── test_tailoring.py
│   │   ├── test_ats_optimizer.py
│   │   └── test_auditor.py
│   ├── property/             # Property-based tests
│   │   ├── test_properties_input.py
│   │   ├── test_properties_fit.py
│   │   ├── test_properties_truth.py
│   │   ├── test_properties_workflow.py
│   │   └── test_properties_audit.py
│   ├── integration/
│   │   ├── test_full_workflow.py
│   │   └── test_error_handling.py
│   └── fixtures/
│       ├── sample_jds.py
│       ├── sample_resumes.py
│       └── mock_llm.py
│
├── docs/                      # Immutable documentation
│   ├── AGENTS.MD             # Truth laws
│   ├── AGENT_ROLES.MD        # Agent specifications
│   ├── ARCHITECTURE.MD       # System design
│   └── STYLE_GUIDE.MD        # Language rules
│
├── examples/
│   ├── sample_jd.md
│   └── sample_resume.md
│
├── requirements.txt
├── run.sh
└── README.md
```

### Agent Implementation Pattern

Each agent follows this pattern:

```python
from crewai import Agent, Task
from typing import Dict, Any
import yaml

class BaseHydraAgent:
    """Base class for all Hydra agents"""
    
    def __init__(self, llm, prompt_path: str):
        self.llm = llm
        self.prompt = self._load_prompt(prompt_path)
        self.truth_rules = self._load_truth_rules()
    
    def _load_prompt(self, path: str) -> str:
        """Load agent prompt from file"""
        return Path(path).read_text()
    
    def _load_truth_rules(self) -> str:
        """Load AGENTS.MD truth laws"""
        return Path("docs/AGENTS.MD").read_text()
    
    def create_agent(self) -> Agent:
        """Create CrewAI agent with prompt and rules"""
        return Agent(
            role=self.role,
            goal=self.goal,
            backstory=f"{self.prompt}\n\nTRUTH RULES:\n{self.truth_rules}",
            llm=self.llm,
            verbose=True
        )
    
    def create_task(self, description: str, context: List[Task] = None) -> Task:
        """Create CrewAI task for this agent"""
        return Task(
            description=description,
            expected_output=self.expected_output,
            agent=self.create_agent(),
            context=context or []
        )
    
    def validate_output(self, output: str) -> Dict[str, Any]:
        """Validate and parse agent output"""
        try:
            parsed = yaml.safe_load(output)
            self._validate_schema(parsed)
            return parsed
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML output: {e}")
    
    def _validate_schema(self, data: Dict) -> None:
        """Validate output contains required fields"""
        required_fields = ["agent", "timestamp", "confidence"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")

# Example: Gap Analyzer implementation
class GapAnalyzerAgent(BaseHydraAgent):
    role = "Gap Analyzer"
    goal = "Map job requirements to candidate experience"
    expected_output = "YAML gap analysis with classifications"
    
    def __init__(self, llm):
        super().__init__(llm, "agents/gap-analyzer/prompt.md")
    
    def _validate_schema(self, data: Dict) -> None:
        """Validate Gap Analyzer specific schema"""
        super()._validate_schema(data)
        
        required = ["requirements", "fit_percentage"]
        for field in required:
            if field not in data:
                raise ValidationError(f"Missing field: {field}")
        
        # Validate fit percentage bounds
        if not 0 <= data["fit_percentage"] <= 100:
            raise ValidationError("Fit percentage must be 0-100")
        
        # Validate classifications
        valid_classifications = {"direct_match", "adjacent", "gap", "blocker"}
        for req in data["requirements"]:
            if req["classification"] not in valid_classifications:
                raise ValidationError(f"Invalid classification: {req['classification']}")
```

### Workflow Orchestration

```python
class HydraWorkflow:
    """Orchestrates the multi-agent workflow"""
    
    def __init__(self, jd: str, resume: str, notes: str = ""):
        self.jd = jd
        self.resume = resume
        self.notes = notes
        self.state = WorkflowState()
        self.llm = self._init_llm()
        self.agents = self._init_agents()
    
    def _init_llm(self) -> LLM:
        """Initialize LLM client from environment"""
        api_key = os.environ.get("OPENROUTER_API_KEY")
        model = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-20250514")
        
        return LLM(
            model=f"openrouter/{model}",
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
    
    def _init_agents(self) -> Dict[str, BaseHydraAgent]:
        """Initialize all agents"""
        return {
            "commander": CommanderAgent(self.llm),
            "research": ResearchAgent(self.llm),
            "gap_analyzer": GapAnalyzerAgent(self.llm),
            "interrogator": InterrogatorAgent(self.llm),
            "differentiator": DifferentiatorAgent(self.llm),
            "tailoring": TailoringAgent(self.llm),
            "ats_optimizer": ATSOptimizerAgent(self.llm),
            "auditor": AuditorAgent(self.llm)
        }
    
    def run(self) -> Dict[str, Any]:
        """Execute the full workflow"""
        try:
            # Stage 1: Research (optional)
            if "research" in self.agents:
                self.state.transition("RESEARCHING")
                research_output = self._execute_agent("research", {
                    "jd": self.jd
                })
            
            # Stage 2: Gap Analysis
            self.state.transition("ANALYZING")
            gap_output = self._execute_agent("gap_analyzer", {
                "jd": self.jd,
                "resume": self.resume,
                "research": research_output if research_output else None
            })
            
            # Stage 3: User Greenlight
            self.state.transition("AWAITING_GREENLIGHT")
            if not self._request_greenlight(gap_output):
                self.state.transition("ARCHIVED")
                return {"status": "archived", "reason": "user declined"}
            
            # Stage 4: Interview Questions
            self.state.transition("INTERVIEWING")
            interview_output = self._execute_agent("interrogator", {
                "gap_analysis": gap_output,
                "jd": self.jd
            })
            
            # Stage 5: Differentiators
            self.state.transition("DIFFERENTIATING")
            diff_output = self._execute_agent("differentiator", {
                "resume": self.resume,
                "notes": self.notes,
                "gap_analysis": gap_output,
                "jd": self.jd
            })
            
            # Stage 6: Document Generation
            self.state.transition("GENERATING")
            docs_output = self._execute_agent("tailoring", {
                "resume": self.resume,
                "gap_analysis": gap_output,
                "differentiators": diff_output,
                "jd": self.jd
            })
            
            # Stage 7: ATS Optimization
            self.state.transition("OPTIMIZING")
            ats_output = self._execute_agent("ats_optimizer", {
                "resume": docs_output["resume"],
                "jd": self.jd
            })
            
            # Stage 8: Audit with retry loop
            self.state.transition("AUDITING")
            audit_output = self._audit_with_retry(docs_output, max_retries=2)
            
            if not audit_output["passed"]:
                self.state.transition("FAILED")
                return {"status": "failed", "audit": audit_output}
            
            # Success
            self.state.transition("COMPLETE")
            return {
                "status": "complete",
                "documents": docs_output,
                "audit": audit_output,
                "audit_trail": self.state.audit_trail
            }
            
        except Exception as e:
            self.state.transition("FAILED")
            self.state.log_error(e)
            raise
    
    def _execute_agent(self, agent_name: str, context: Dict) -> Dict:
        """Execute an agent with error handling"""
        agent = self.agents[agent_name]
        
        try:
            output = agent.execute(context)
            self.state.log_agent_execution(agent_name, output)
            return output
        except Exception as e:
            # Retry once
            if self.state.get_retry_count(agent_name) < 1:
                self.state.increment_retry(agent_name)
                return self._execute_agent(agent_name, context)
            else:
                raise
    
    def _audit_with_retry(self, docs: Dict, max_retries: int) -> Dict:
        """Audit documents with retry loop for failures"""
        retry_count = 0
        
        while retry_count <= max_retries:
            audit_result = self.agents["auditor"].execute({
                "documents": docs,
                "sources": [self.resume, self.notes]
            })
            
            if audit_result["passed"]:
                return audit_result
            
            # Check for blocking issues
            blocking_issues = [i for i in audit_result["issues"] 
                             if i["severity"] == "blocking"]
            
            if not blocking_issues:
                # Only warnings/recommendations, pass
                return audit_result
            
            if retry_count >= max_retries:
                # Max retries reached, escalate
                return audit_result
            
            # Route back to responsible agent
            self.state.transition("RETRYING")
            docs = self._fix_issues(docs, blocking_issues)
            retry_count += 1
        
        return audit_result
    
    def _fix_issues(self, docs: Dict, issues: List[Dict]) -> Dict:
        """Route documents back to responsible agent for fixes"""
        # Regenerate with specific feedback
        return self.agents["tailoring"].execute({
            "resume": self.resume,
            "previous_output": docs,
            "issues_to_fix": issues
        })
    
    def _request_greenlight(self, gap_analysis: Dict) -> bool:
        """Request user approval to proceed"""
        # In CLI mode, this would prompt the user
        # For now, auto-approve if fit > 60%
        return gap_analysis["fit_percentage"] > 60
```

### Configuration Management

```python
# config.py
from dataclasses import dataclass
from typing import Optional
import os

@dataclass
class HydraConfig:
    """Configuration for Hydra system"""
    
    # LLM Configuration
    openrouter_api_key: str
    openrouter_model: str = "anthropic/claude-sonnet-4-20250514"
    
    # Workflow Configuration
    enable_research_agent: bool = True
    auto_greenlight_threshold: float = 0.60
    max_agent_retries: int = 1
    max_audit_retries: int = 2
    
    # Performance Configuration
    fit_analysis_timeout: int = 60  # seconds
    document_generation_timeout: int = 180  # seconds
    
    # Output Configuration
    output_format: str = "markdown"
    include_audit_trail: bool = True
    
    @classmethod
    def from_env(cls) -> "HydraConfig":
        """Load configuration from environment variables"""
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable required")
        
        return cls(
            openrouter_api_key=api_key,
            openrouter_model=os.environ.get(
                "OPENROUTER_MODEL", 
                "anthropic/claude-sonnet-4-20250514"
            ),
            enable_research_agent=os.environ.get(
                "ENABLE_RESEARCH", "true"
            ).lower() == "true"
        )
```

## Performance Considerations

### Optimization Strategies

1. **Parallel Agent Execution**
   - Research Agent and Gap Analyzer could run in parallel (both only need JD/resume)
   - Consider using asyncio for concurrent LLM calls where dependencies allow

2. **Caching**
   - Cache research results for 24 hours (company info doesn't change frequently)
   - Cache LLM responses for identical inputs (useful during testing)
   - Cache parsed YAML to avoid repeated parsing

3. **Prompt Optimization**
   - Keep prompts concise to reduce token usage
   - Use few-shot examples only when necessary
   - Compress context passed between agents

4. **Timeout Management**
   - Set reasonable timeouts for each agent (30-60s)
   - Fail fast on timeouts rather than blocking indefinitely
   - Provide partial results when possible

### Performance Targets

- Fit Analysis: < 60 seconds
- Full Workflow (with greenlight): < 3 minutes
- Audit with 1 retry: < 4 minutes total
- Research Agent (with caching): < 10 seconds

## Security Considerations

1. **API Key Management**
   - Never commit API keys to version control
   - Use environment variables for all secrets
   - Validate API key format before use

2. **Input Validation**
   - Sanitize all user inputs (JD, resume, notes)
   - Validate file uploads (size limits, format checks)
   - Prevent injection attacks in prompts

3. **Output Sanitization**
   - Remove any PII that shouldn't be in outputs
   - Validate all generated content before presenting to user
   - Ensure audit trail doesn't leak sensitive information

4. **Rate Limiting**
   - Implement rate limiting for LLM API calls
   - Handle 429 responses gracefully with backoff
   - Monitor API usage to avoid unexpected costs

## Deployment Considerations

### Local Development
- Use `.env` file for configuration
- Run via `./run.sh` script
- Virtual environment for dependency isolation

### Production Deployment
- Container-based deployment (Docker)
- Environment-specific configuration
- Logging and monitoring
- Error tracking (Sentry or similar)
- API usage monitoring

### Scalability
- Current design is single-user, single-workflow
- For multi-user: Add workflow queue and worker pool
- For high volume: Consider caching layer (Redis)
- For cost optimization: Batch similar requests
