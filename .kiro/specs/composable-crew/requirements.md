# Requirements Document

## Introduction

Composable Crew is a truth-constrained, multi-agent system for generating high-quality job applications. The system coordinates specialized AI agents through a central orchestrator (Commander) to analyze job descriptions, assess fit, extract truthful details through interviews, identify unique positioning, and generate tailored resumes and cover letters that pass AI detection while maintaining complete truthfulness.

## Glossary

- **Composable Crew**: The multi-agent system consisting of Commander and specialized agents
- **Commander**: The orchestrator agent that coordinates all other agents and enforces workflow
- **Gap Analyzer**: Agent that maps job requirements to candidate experience
- **Interrogator-Prepper**: Agent that generates interview questions to extract truthful details
- **Differentiator**: Agent that identifies unique value propositions
- **Tailoring Agent**: Agent that generates tailored resumes and cover letters
- **Auditor Suite**: Agent that verifies truth, tone, ATS compliance, and rule adherence
- **ATS Optimizer**: Agent that ensures documents pass Applicant Tracking Systems
- **Research Agent**: Agent that gathers company and role intelligence
- **JD**: Job Description
- **Truth Laws**: Immutable rules defined in AGENTS.MD that prevent fabrication
- **Adjacent Experience**: Transferable experience framed honestly, not as direct expertise
- **Greenlight**: User approval to proceed with application generation
- **Red Flag**: Concerning signal about a company or role
- **Source Document**: Verified resume or user-confirmed information used as truth source
- **AI Detection**: Tools that identify AI-generated content
- **YAML**: Structured data format used for agent communication

## Requirements

### Requirement 1

**User Story:** As a job seeker, I want to input a job description and my resume, so that the system can analyze fit and generate tailored application materials.

#### Acceptance Criteria

1. WHEN a user provides a job description as text or file THEN the system SHALL accept and parse the input
2. WHEN a user provides a resume as text or file THEN the system SHALL accept and parse the input
3. WHEN inputs are provided THEN the Commander SHALL initiate the workflow
4. WHEN the job description is missing required information THEN the system SHALL request clarification from the user
5. WHEN the resume is missing critical information THEN the system SHALL note gaps and proceed with available data


### Requirement 2

**User Story:** As a job seeker, I want the system to analyze job fit before I invest time, so that I can focus on opportunities where I have a strong match.

#### Acceptance Criteria

1. WHEN the Commander receives a job description THEN the system SHALL extract key requirements (explicit and implicit)
2. WHEN requirements are extracted THEN the Gap Analyzer SHALL map each requirement to the candidate's verified experience
3. WHEN mapping is complete THEN the system SHALL classify each requirement as direct match, adjacent experience, gap, or blocker
4. WHEN classification is complete THEN the Commander SHALL calculate an overall fit percentage
5. WHEN fit analysis is complete THEN the Commander SHALL present a summary to the user with a recommendation (PROCEED, PASS, or DISCUSS)

### Requirement 3

**User Story:** As a job seeker, I want the system to identify red flags automatically, so that I can avoid problematic opportunities early.

#### Acceptance Criteria

1. WHEN the Commander analyzes a job description THEN the system SHALL check for auto-reject criteria (contract-to-hire, below senior level, no compensation, relocation required)
2. WHEN auto-reject criteria are found THEN the Commander SHALL recommend PASS with specific reasons
3. WHEN the Research Agent gathers company information THEN the system SHALL identify red flags (layoffs, high turnover, negative reviews)
4. WHEN red flags are identified THEN the Commander SHALL present them to the user before requesting greenlight
5. WHEN the user reviews red flags THEN the system SHALL allow the user to override and proceed if desired

### Requirement 4

**User Story:** As a job seeker, I want to provide explicit approval before the system generates application materials, so that I maintain control over which opportunities to pursue.

#### Acceptance Criteria

1. WHEN fit analysis is complete THEN the Commander SHALL request user greenlight before proceeding
2. WHEN the user provides greenlight THEN the system SHALL continue with the Interrogator-Prepper and subsequent agents
3. WHEN the user declines greenlight THEN the system SHALL archive the analysis and terminate the workflow
4. WHEN the user requests more information THEN the Commander SHALL provide additional details before requesting greenlight again
5. WHEN greenlight is pending THEN the system SHALL not proceed to document generation agents


### Requirement 5

**User Story:** As a job seeker, I want the system to ask me targeted questions about gaps in my experience, so that I can provide truthful details that strengthen my application.

#### Acceptance Criteria

1. WHEN the user provides greenlight THEN the Interrogator-Prepper SHALL generate 8-12 targeted interview questions based on identified gaps
2. WHEN questions are generated THEN the system SHALL group them by theme (technical, leadership, outcomes, tools)
3. WHEN questions are presented THEN the system SHALL use STAR+ format (Situation, Task, Actions, Results, Proof)
4. WHEN the user provides answers THEN the system SHALL store them as verified source material for downstream agents
5. WHEN the user cannot answer a question THEN the system SHALL note the gap and proceed with conservative framing

### Requirement 6

**User Story:** As a job seeker, I want the system to identify my unique differentiators, so that my application stands out from other candidates.

#### Acceptance Criteria

1. WHEN interview notes are available THEN the Differentiator SHALL analyze the candidate's background for unique value propositions
2. WHEN analyzing background THEN the system SHALL identify rare skill combinations, quantified outcomes, and narrative threads
3. WHEN differentiators are identified THEN the system SHALL output 2-3 primary differentiators with evidence and framing suggestions
4. WHEN differentiators are found THEN the system SHALL ensure they are relevant to the specific job description
5. WHEN no strong differentiators exist THEN the system SHALL identify the best available positioning angles

### Requirement 7

**User Story:** As a job seeker, I want the system to generate a tailored resume and cover letter, so that I can apply with materials optimized for the specific role.

#### Acceptance Criteria

1. WHEN the Differentiator completes THEN the Tailoring Agent SHALL generate a tailored resume in Markdown format
2. WHEN generating the resume THEN the system SHALL emphasize experience relevant to the job description
3. WHEN generating the resume THEN the system SHALL incorporate differentiators naturally
4. WHEN the resume is complete THEN the Tailoring Agent SHALL generate a cover letter (250-400 words)
5. WHEN generating documents THEN the system SHALL use only verified source material (resume, interview notes, user confirmations)


### Requirement 8

**User Story:** As a job seeker, I want all application materials to sound human-written, so that they pass AI detection tools and feel authentic.

#### Acceptance Criteria

1. WHEN the Tailoring Agent generates content THEN the system SHALL avoid forbidden AI-telltale phrases (proven track record, passionate about, leverage, synergize)
2. WHEN generating content THEN the system SHALL vary sentence lengths deliberately (short, medium, long, conversational)
3. WHEN generating content THEN the system SHALL use active voice and specific numbers rather than approximations
4. WHEN generating content THEN the system SHALL include human elements (contractions, occasional asides, sentence fragments)
5. WHEN the Auditor Suite reviews content THEN the system SHALL flag any AI detection triggers for revision

### Requirement 9

**User Story:** As a job seeker, I want the system to enforce truth laws strictly, so that I never submit fabricated or exaggerated claims.

#### Acceptance Criteria

1. WHEN any agent generates content THEN the system SHALL verify all claims trace to source documents
2. WHEN a claim cannot be verified THEN the system SHALL reject the claim or request user confirmation
3. WHEN employment dates or chronology are referenced THEN the system SHALL preserve them exactly as provided
4. WHEN technologies or tools are mentioned THEN the system SHALL only include those present in source documents
5. WHEN adjacent experience is framed THEN the system SHALL clearly indicate it is transferable, not direct expertise

### Requirement 10

**User Story:** As a job seeker, I want the system to optimize documents for ATS systems, so that my application passes automated screening.

#### Acceptance Criteria

1. WHEN documents are generated THEN the ATS Optimizer SHALL extract keywords from the job description
2. WHEN keywords are extracted THEN the system SHALL verify their presence in the tailored resume
3. WHEN keywords are missing but claimable THEN the system SHALL suggest truthful insertions
4. WHEN keywords are missing and not claimable THEN the system SHALL note them as gaps without adding false claims
5. WHEN formatting is checked THEN the system SHALL ensure ATS-compatible structure (single column, plain bullets, no tables)


### Requirement 11

**User Story:** As a job seeker, I want the system to audit all generated materials, so that I can trust the output meets quality and truth standards.

#### Acceptance Criteria

1. WHEN documents are generated THEN the Auditor Suite SHALL perform a truth audit verifying all claims against sources
2. WHEN the truth audit runs THEN the system SHALL flag any fabrications, exaggerations, or unverified claims as blocking issues
3. WHEN documents are generated THEN the Auditor Suite SHALL perform a tone audit checking for AI patterns
4. WHEN documents are generated THEN the Auditor Suite SHALL perform an ATS audit verifying keyword coverage
5. WHEN documents are generated THEN the Auditor Suite SHALL perform a compliance audit ensuring AGENTS.MD rules are followed

### Requirement 12

**User Story:** As a job seeker, I want the system to fix audit failures automatically when possible, so that I receive high-quality output without manual intervention.

#### Acceptance Criteria

1. WHEN the Auditor Suite identifies issues THEN the system SHALL categorize them as blocking, warning, or recommendation
2. WHEN blocking issues are found THEN the Commander SHALL route the output back to the responsible agent with specific fixes
3. WHEN the responsible agent receives feedback THEN the system SHALL regenerate the content addressing the issues
4. WHEN regeneration is complete THEN the Auditor Suite SHALL re-audit the fixed content
5. WHEN audit failures persist after 2 retry loops THEN the system SHALL escalate to the user with options

### Requirement 13

**User Story:** As a job seeker, I want the system to complete the workflow efficiently, so that I can generate applications quickly.

#### Acceptance Criteria

1. WHEN the workflow begins THEN the system SHALL complete fit analysis within 60 seconds
2. WHEN the user provides greenlight THEN the system SHALL complete document generation within 3 minutes
3. WHEN agents run THEN the system SHALL execute them sequentially with proper context passing
4. WHEN an agent completes THEN the system SHALL immediately invoke the next agent without unnecessary delays
5. WHEN the workflow completes THEN the system SHALL present the final package (resume, cover letter, audit report) to the user


### Requirement 14

**User Story:** As a system architect, I want agents to communicate via structured YAML, so that outputs are parseable and validatable.

#### Acceptance Criteria

1. WHEN any agent produces output THEN the system SHALL format it as structured YAML
2. WHEN YAML output is generated THEN the system SHALL include agent name, timestamp, and confidence level
3. WHEN downstream agents consume output THEN the system SHALL parse YAML and validate structure
4. WHEN YAML parsing fails THEN the system SHALL request regeneration from the agent with format guidance
5. WHEN agents communicate THEN the system SHALL never use free-form prose for structured data

### Requirement 15

**User Story:** As a system architect, I want the Commander to enforce workflow order, so that agents execute in the correct sequence with proper dependencies.

#### Acceptance Criteria

1. WHEN the workflow begins THEN the Commander SHALL execute Research Agent (if available) before Gap Analyzer
2. WHEN Research Agent completes THEN the Commander SHALL execute Gap Analyzer with research context
3. WHEN Gap Analyzer completes THEN the Commander SHALL request user greenlight before proceeding
4. WHEN greenlight is received THEN the Commander SHALL execute Interrogator-Prepper, Differentiator, Tailoring Agent, ATS Optimizer, and Auditor Suite in sequence
5. WHEN any agent fails THEN the Commander SHALL handle the error gracefully and either retry or escalate to the user

### Requirement 16

**User Story:** As a system architect, I want the system to maintain an audit trail, so that all decisions and sources are traceable.

#### Acceptance Criteria

1. WHEN the workflow executes THEN the system SHALL log all agent invocations with timestamps
2. WHEN agents make decisions THEN the system SHALL record the decision and rationale
3. WHEN claims are made THEN the system SHALL record the source document and location
4. WHEN the workflow completes THEN the system SHALL include the audit trail in the final package
5. WHEN errors occur THEN the system SHALL log the error, attempted resolution, and outcome


### Requirement 17

**User Story:** As a system architect, I want the system to handle errors gracefully, so that failures don't block the entire workflow.

#### Acceptance Criteria

1. WHEN an agent encounters an error THEN the system SHALL retry once with the same inputs
2. WHEN retry fails THEN the Commander SHALL determine if the workflow can proceed without that agent's output
3. WHEN the workflow can proceed THEN the system SHALL continue with available data and note the limitation
4. WHEN the workflow cannot proceed THEN the system SHALL present the error to the user with options (retry, skip, abort)
5. WHEN external services are unavailable THEN the system SHALL proceed with degraded functionality rather than failing completely

### Requirement 18

**User Story:** As a system architect, I want the system to support multiple LLM providers, so that users can choose their preferred model.

#### Acceptance Criteria

1. WHEN the system initializes THEN the system SHALL read the OPENROUTER_API_KEY environment variable
2. WHEN the API key is set THEN the system SHALL configure the LLM client with OpenRouter
3. WHEN the OPENROUTER_MODEL environment variable is set THEN the system SHALL use the specified model
4. WHEN the OPENROUTER_MODEL is not set THEN the system SHALL default to anthropic/claude-3.5-sonnet
5. WHEN the LLM client is configured THEN the system SHALL use it for all agent invocations

### Requirement 19

**User Story:** As a developer, I want to run the system via a simple command, so that I can quickly test with sample inputs.

#### Acceptance Criteria

1. WHEN a developer runs ./run.sh with job description and resume paths THEN the system SHALL execute the full workflow
2. WHEN the run script executes THEN the system SHALL check for required environment variables and report missing ones
3. WHEN the run script executes THEN the system SHALL create a virtual environment if it doesn't exist
4. WHEN the run script executes THEN the system SHALL install dependencies if they're not present
5. WHEN the workflow completes THEN the system SHALL output results to the console or specified file

### Requirement 20

**User Story:** As a developer, I want comprehensive documentation, so that I can understand the system architecture and extend it.

#### Acceptance Criteria

1. WHEN a developer reads AGENTS.MD THEN the system SHALL provide immutable truth laws that all agents must follow
2. WHEN a developer reads AGENT_ROLES.MD THEN the system SHALL provide detailed specifications for each agent
3. WHEN a developer reads ARCHITECTURE.MD THEN the system SHALL provide system design, data flow, and component structure
4. WHEN a developer reads STYLE_GUIDE.MD THEN the system SHALL provide anti-AI language patterns and human voice standards
5. WHEN a developer adds a new agent THEN the system SHALL require updating AGENT_ROLES.MD with the agent specification
