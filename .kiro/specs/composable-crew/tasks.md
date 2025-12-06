We can leave the job-discovery feature to one side for now. No need to have it. We can proceed with the Composable crew project now.

One thing I'd like to find out is how are you going to delegate work to your fellow agents outside of this IDE? And how are you going to pick up their work when it's complete? What kind of flag system or file system do you want to use? And where should we do this? # Implementation Plan

This plan is organized to enable parallel development across multiple work streams. Tasks are grouped by dependency, allowing different developers/agents to work simultaneously on independent components.

## Work Stream Organization

- **Stream A: Core Infrastructure** - Foundation that other streams depend on
- **Stream B: Agent Implementations (Group 1)** - Research, Gap Analyzer, Interrogator
- **Stream C: Agent Implementations (Group 2)** - Differentiator, Tailoring, ATS Optimizer
- **Stream D: Agent Implementations (Group 3)** - Auditor Suite
- **Stream E: Workflow Orchestration** - Commander and workflow management
- **Stream F: Testing Infrastructure** - Can start early and run in parallel

---

## Stream A: Core Infrastructure (Foundation)

- [x] 1. Set up project structure and base classes
  - Create directory structure for agents, runtime, tests
  - Implement BaseHydraAgent class with common functionality
  - Set up configuration management (HydraConfig)
  - Create data models (JobDescription, Resume, WorkflowState, etc.)
  - _Requirements: 14.1, 14.2, 18.1, 18.2_

- [x] 1.1 Implement base agent class
  - Create BaseHydraAgent with prompt loading, YAML validation
  - Implement _validate_schema method for common fields
  - Add error handling and retry logic
  - _Requirements: 14.1, 14.2, 17.1_

- [x] 1.2 Create data models
  - Implement JobDescription, Resume, Employment dataclasses
  - Implement Requirement, Classification, Differentiator models
  - Implement WorkflowState with state machine transitions
  - Implement AuditIssue and error models
  - _Requirements: 2.1, 2.2, 16.1_

- [x] 1.3 Set up LLM client integration
  - Implement OpenRouter LLM client configuration
  - Add environment variable loading (OPENROUTER_API_KEY, OPENROUTER_MODEL)
  - Implement default model fallback
  - Add error handling for API failures
  - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

- [x] 1.4 Write unit tests for base infrastructure
  - Test BaseHydraAgent YAML validation
  - Test data model serialization/deserialization
  - Test LLM client initialization
  - Test configuration loading
  - _Requirements: 14.1, 14.3, 18.1_

- [x] 2. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

---

## Stream B: Agent Implementations (Group 1)

These agents can be developed in parallel after Stream A completes.

- [ ] 3. Implement Research Agent
  - Create ResearchAgent class extending BaseHydraAgent
  - Implement company name extraction from JD
  - Implement company intelligence gathering (size, funding, tech stack)
  - Implement red flag detection logic
  - Implement culture signal analysis
  - _Requirements: 3.3, 5.1, 5.2_

- [ ] 3.1 Create Research Agent prompt
  - Write prompt.md for Research Agent in agents/research-agent/
  - Include instructions for company intel gathering
  - Include red flag detection criteria
  - Include tech stack discovery methods
  - _Requirements: 3.1, 3.3_

- [ ]* 3.2 Write property test for Research Agent
  - **Property 11: Red flag presentation ordering**
  - **Validates: Requirements 3.4**

- [ ]* 3.3 Write unit tests for Research Agent
  - Test company name extraction
  - Test red flag categorization
  - Test tech stack identification
  - Test output YAML structure
  - _Requirements: 3.1, 3.3_

- [ ] 4. Implement Gap Analyzer Agent
  - Create GapAnalyzerAgent class extending BaseHydraAgent
  - Implement requirement extraction from JD (explicit and implicit)
  - Implement experience mapping logic
  - Implement classification (direct_match, adjacent, gap, blocker)
  - Implement fit percentage calculation
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 4.1 Create Gap Analyzer prompt
  - Write prompt.md for Gap Analyzer in agents/gap-analyzer/
  - Include classification criteria and examples
  - Include framing suggestions for adjacent experience
  - _Requirements: 2.2, 2.3_

- [ ]* 4.2 Write property test for requirement extraction
  - **Property 5: Requirement extraction completeness**
  - **Validates: Requirements 2.1**

- [ ]* 4.3 Write property test for classification completeness
  - **Property 6: Classification completeness**
  - **Validates: Requirements 2.2, 2.3**

- [ ]* 4.4 Write property test for fit percentage bounds
  - **Property 7: Fit percentage bounds**
  - **Validates: Requirements 2.4**

- [ ]* 4.5 Write unit tests for Gap Analyzer
  - Test requirement extraction
  - Test classification logic
  - Test fit calculation
  - Test output structure
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 5. Implement Interrogator-Prepper Agent
  - Create InterrogatorAgent class extending BaseHydraAgent
  - Implement question generation based on gaps
  - Implement theme grouping logic
  - Implement STAR+ format validation
  - Implement answer storage as source material
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 5.1 Create Interrogator-Prepper prompt
  - Write prompt.md for Interrogator in agents/interrogator-prepper/
  - Include STAR+ format examples
  - Include theme categories (technical, leadership, outcomes, tools)
  - _Requirements: 5.2, 5.3_

- [ ]* 5.2 Write property test for question count
  - **Property 15: Question count bounds**
  - **Validates: Requirements 5.1**

- [ ]* 5.3 Write property test for question grouping
  - **Property 16: Question grouping completeness**
  - **Validates: Requirements 5.2**

- [ ]* 5.4 Write property test for answer storage round-trip
  - **Property 17: Answer storage round-trip**
  - **Validates: Requirements 5.4**

- [ ]* 5.5 Write unit tests for Interrogator-Prepper
  - Test question generation
  - Test theme grouping
  - Test STAR+ format
  - Test answer storage
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

---

## Stream C: Agent Implementations (Group 2)

These agents can be developed in parallel with Stream B after Stream A completes.

- [ ] 7. Implement Differentiator Agent
  - Create DifferentiatorAgent class extending BaseHydraAgent
  - Implement skill combination identification
  - Implement quantified outcome extraction
  - Implement narrative thread discovery
  - Implement relevance assessment to JD
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 7.1 Create Differentiator prompt
  - Write prompt.md for Differentiator in agents/differentiator/
  - Include examples of rare skill combinations
  - Include guidance on narrative thread identification
  - _Requirements: 6.2, 6.3_

- [ ]* 7.2 Write property test for differentiator count
  - **Property 18: Differentiator count bounds**
  - **Validates: Requirements 6.3**

- [ ]* 7.3 Write property test for differentiator structure
  - **Property 19: Differentiator structure completeness**
  - **Validates: Requirements 6.3**

- [ ]* 7.4 Write property test for differentiator relevance
  - **Property 20: Differentiator relevance**
  - **Validates: Requirements 6.4**

- [ ]* 7.5 Write unit tests for Differentiator
  - Test skill combination identification
  - Test outcome extraction
  - Test narrative thread discovery
  - Test output structure
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 8. Implement Tailoring Agent
  - Create TailoringAgent class extending BaseHydraAgent
  - Implement resume generation with Markdown formatting
  - Implement cover letter generation with word count validation
  - Implement style guide application (anti-AI patterns)
  - Implement source verification for all claims
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 8.1 Create Tailoring Agent prompt
  - Write prompt.md for Tailoring Agent in agents/tailoring-agent/
  - Include style guide rules (forbidden phrases, sentence variation)
  - Include examples of human-sounding content
  - Include source traceability requirements
  - _Requirements: 7.2, 7.3, 8.1, 8.2_

- [ ]* 8.2 Write property test for resume format
  - **Property 21: Resume format validity**
  - **Validates: Requirements 7.1**

- [ ]* 8.3 Write property test for cover letter word count
  - **Property 22: Cover letter word count bounds**
  - **Validates: Requirements 7.4**

- [ ]* 8.4 Write property test for source traceability
  - **Property 23: Source traceability**
  - **Validates: Requirements 7.5, 9.1**

- [ ]* 8.5 Write property test for forbidden phrases
  - **Property 24: Forbidden phrase absence**
  - **Validates: Requirements 8.1**

- [ ]* 8.6 Write property test for sentence variation
  - **Property 25: Sentence length variation**
  - **Validates: Requirements 8.2**

- [ ]* 8.7 Write unit tests for Tailoring Agent
  - Test resume generation
  - Test cover letter generation
  - Test Markdown formatting
  - Test style guide application
  - _Requirements: 7.1, 7.2, 7.4, 8.1_

- [ ] 9. Implement ATS Optimizer Agent
  - Create ATSOptimizerAgent class extending BaseHydraAgent
  - Implement keyword extraction from JD
  - Implement keyword coverage checking
  - Implement truthful insertion suggestions
  - Implement format validation (ATS compatibility)
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 9.1 Create ATS Optimizer prompt
  - Write prompt.md for ATS Optimizer in agents/ats-optimizer/
  - Include keyword extraction strategies
  - Include ATS format requirements
  - _Requirements: 10.1, 10.5_

- [ ]* 9.2 Write property test for keyword extraction
  - **Property 30: Keyword extraction completeness**
  - **Validates: Requirements 10.1**

- [ ]* 9.3 Write property test for keyword coverage
  - **Property 31: Keyword coverage checking**
  - **Validates: Requirements 10.2**

- [ ]* 9.4 Write property test for no fabrication
  - **Property 32: No fabrication for missing keywords**
  - **Validates: Requirements 10.4**

- [ ]* 9.5 Write unit tests for ATS Optimizer
  - Test keyword extraction
  - Test coverage checking
  - Test suggestion generation
  - Test format validation
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

---

## Stream D: Agent Implementations (Group 3)

This agent can be developed in parallel with Streams B and C after Stream A completes.


- [ ] 11. Implement Auditor Suite Agent
  - Create AuditorAgent class extending BaseHydraAgent
  - Implement truth audit (verify claims against sources)
  - Implement tone audit (check for AI patterns)
  - Implement ATS audit (verify keyword coverage)
  - Implement compliance audit (check AGENTS.MD rules)
  - Implement issue categorization (blocking, warning, recommendation)
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 12.1_

- [ ] 11.1 Create Auditor Suite prompt
  - Write prompt.md for Auditor Suite in agents/auditor-suite/
  - Include truth verification criteria
  - Include AI pattern detection rules (from STYLE_GUIDE.MD)
  - Include compliance checklist (from AGENTS.MD)
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ]* 11.2 Write property test for audit execution
  - **Property 33: Audit execution completeness**
  - **Validates: Requirements 11.1, 11.3, 11.4, 11.5**

- [ ]* 11.3 Write property test for issue categorization
  - **Property 34: Issue severity categorization**
  - **Validates: Requirements 12.1**

- [ ]* 11.4 Write property test for chronology preservation
  - **Property 27: Chronology preservation**
  - **Validates: Requirements 9.3**

- [ ]* 11.5 Write property test for technology verification
  - **Property 28: Technology verification**
  - **Validates: Requirements 9.4**

- [ ]* 11.6 Write property test for adjacent framing
  - **Property 29: Adjacent experience framing**
  - **Validates: Requirements 9.5**

- [ ]* 11.7 Write unit tests for Auditor Suite
  - Test truth audit logic
  - Test tone audit (AI pattern detection)
  - Test ATS audit
  - Test compliance audit
  - Test issue categorization
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 12.1_

- [ ] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

---

## Stream E: Workflow Orchestration

This stream depends on Streams A, B, C, and D being complete. It integrates all agents.

- [ ] 13. Implement Commander Agent
  - Create CommanderAgent class extending BaseHydraAgent
  - Implement fit analysis presentation
  - Implement greenlight request logic
  - Implement agent dispatch coordination
  - Implement error handling and escalation
  - Implement final package assembly
  - _Requirements: 2.5, 4.1, 4.2, 4.3, 15.1, 15.2, 15.3, 15.4, 15.5_

- [ ] 13.1 Create Commander prompt
  - Write prompt.md for Commander in agents/commander/
  - Include workflow orchestration rules
  - Include auto-reject criteria
  - Include error recovery strategies
  - _Requirements: 3.1, 3.2, 4.1_

- [ ]* 13.2 Write property test for greenlight enforcement
  - **Property 12: Greenlight enforcement**
  - **Validates: Requirements 4.1, 4.5**

- [ ]* 13.3 Write property test for auto-reject
  - **Property 10: Auto-reject recommendation**
  - **Validates: Requirements 3.2**

- [ ]* 13.4 Write unit tests for Commander
  - Test fit analysis presentation
  - Test greenlight logic
  - Test agent dispatch
  - Test error handling
  - Test package assembly
  - _Requirements: 2.5, 4.1, 4.2, 4.3_

- [ ] 14. Implement HydraWorkflow orchestrator
  - Create HydraWorkflow class that coordinates all agents
  - Implement state machine transitions
  - Implement sequential agent execution with context passing
  - Implement audit retry loop (max 2 retries)
  - Implement error recovery and graceful degradation
  - Implement audit trail logging
  - _Requirements: 13.3, 15.1, 15.2, 15.3, 15.4, 16.1, 16.2, 16.3, 17.1, 17.2, 17.3_

- [ ] 14.1 Implement state machine
  - Create WorkflowState class with state transitions
  - Implement state validation (valid transitions only)
  - Implement state persistence for audit trail
  - _Requirements: 16.1, 16.4_

- [ ] 14.2 Implement audit retry loop
  - Create _audit_with_retry method
  - Implement blocking issue detection
  - Implement routing back to responsible agent
  - Implement max retry enforcement (2 retries)
  - _Requirements: 12.2, 12.3, 12.4, 12.5_

- [ ]* 14.3 Write property test for blocking issue retry
  - **Property 35: Blocking issue retry**
  - **Validates: Requirements 12.2**

- [ ]* 14.4 Write property test for retry limit
  - **Property 36: Retry limit enforcement**
  - **Validates: Requirements 12.5**

- [ ]* 14.5 Write property test for agent execution sequence
  - **Property 37: Agent execution sequence**
  - **Validates: Requirements 13.3, 15.1, 15.2, 15.4**

- [ ]* 14.6 Write property test for final package completeness
  - **Property 38: Final package completeness**
  - **Validates: Requirements 13.5**

- [ ]* 14.7 Write property test for audit trail logging
  - **Property 41: Agent invocation logging**
  - **Validates: Requirements 16.1**

- [ ]* 14.8 Write property test for audit trail inclusion
  - **Property 43: Audit trail inclusion**
  - **Validates: Requirements 16.4**

- [ ]* 14.9 Write unit tests for HydraWorkflow
  - Test state transitions
  - Test agent execution order
  - Test context passing between agents
  - Test audit retry loop
  - Test error recovery
  - _Requirements: 13.3, 15.1, 15.2, 15.3, 15.4, 17.1, 17.2, 17.3_

- [ ] 15. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

---

## Stream F: Testing Infrastructure

This stream can start early and run in parallel with agent development.

- [ ] 16. Set up testing framework
  - Install pytest, hypothesis, pytest-mock, coverage
  - Create test directory structure (unit/, property/, integration/, fixtures/)
  - Create base test fixtures (sample JDs, resumes, mock LLM)
  - Set up coverage reporting
  - _Requirements: Testing Strategy_

- [ ] 16.1 Create test fixtures
  - Create sample_jds.py with diverse job descriptions
  - Create sample_resumes.py with test resumes
  - Create mock_llm.py for mocking LLM responses
  - Create hypothesis strategies for generating test data
  - _Requirements: Testing Strategy_

- [ ] 16.2 Create property test generators
  - Create Hypothesis strategies for JobDescription
  - Create Hypothesis strategies for Resume
  - Create Hypothesis strategies for Requirements
  - Create Hypothesis strategies for dates, technologies, etc.
  - _Requirements: Testing Strategy_

- [ ]* 16.3 Write property tests for YAML format
  - **Property 39: YAML format validity**
  - **Validates: Requirements 14.1, 14.3**

- [ ]* 16.4 Write property tests for YAML structure
  - **Property 40: YAML structure completeness**
  - **Validates: Requirements 14.2**

- [ ]* 16.5 Write property tests for input validation
  - **Property 1: Input parsing completeness**
  - **Property 2: Resume parsing completeness**
  - **Property 3: Workflow initialization**
  - **Property 4: Missing information handling**
  - **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

- [ ]* 16.6 Write property tests for error handling
  - **Property 44: Single retry on error**
  - **Property 45: Graceful degradation**
  - **Validates: Requirements 17.1, 17.3, 17.5**

- [ ] 17. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

---

## Stream G: Integration and CLI

This stream depends on Stream E being complete.

- [ ] 18. Implement CLI interface
  - Create run.sh script with environment validation
  - Create quick_crew.py with embedded prompts
  - Create crew.py with file-based prompt loading
  - Implement command-line argument parsing
  - Implement output formatting (console and file)
  - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5_

- [ ] 18.1 Create run.sh script
  - Implement environment variable checking
  - Implement virtual environment creation
  - Implement dependency installation
  - Implement workflow execution
  - _Requirements: 19.1, 19.2, 19.3, 19.4_

- [ ] 18.2 Create quick_crew.py
  - Embed simplified agent prompts
  - Implement argument parsing (--jd, --resume, --notes, --out)
  - Implement HydraWorkflow invocation
  - Implement output formatting
  - _Requirements: 19.1, 19.5_

- [ ] 18.3 Create crew.py
  - Implement prompt loading from agents/*/prompt.md
  - Implement documentation loading (AGENTS.MD, STYLE_GUIDE.MD)
  - Implement full HydraWorkflow with all agents
  - _Requirements: 19.1, 20.1, 20.2, 20.3, 20.4_

- [ ]* 18.4 Write integration tests for CLI
  - Test run.sh execution
  - Test quick_crew.py with sample inputs
  - Test crew.py with sample inputs
  - Test output file generation
  - _Requirements: 19.1, 19.5_

- [ ] 19. Write integration tests for full workflow
  - Test happy path (JD + resume → complete package)
  - Test greenlight decline path
  - Test audit failure retry path
  - Test error recovery paths
  - Test with various JD/resume combinations
  - _Requirements: 13.3, 15.1, 15.2, 15.3, 15.4, 17.1, 17.2, 17.3_

- [ ]* 19.1 Write integration test for happy path
  - Test full workflow from input to approved output
  - Verify all agents execute in correct order
  - Verify final package contains all required components
  - _Requirements: 13.3, 15.4_

- [ ]* 19.2 Write integration test for audit retry
  - Test workflow with intentional audit failures
  - Verify retry loop executes
  - Verify fixes are applied
  - Verify eventual success or escalation
  - _Requirements: 12.2, 12.3, 12.4, 12.5_

- [ ]* 19.3 Write integration test for error recovery
  - Test workflow with agent failures
  - Verify retry logic
  - Verify graceful degradation
  - Verify error escalation
  - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

- [ ] 20. Final Checkpoint - Make sure all tests are passing
  - Ensure all tests pass, ask the user if questions arise.

---

## Stream H: Documentation and Polish

This stream can run in parallel with other streams and finalize at the end.

- [ ] 21. Update documentation
  - Verify AGENTS.MD is complete and accurate
  - Verify AGENT_ROLES.MD includes all 8 agents
  - Verify ARCHITECTURE.MD reflects implementation
  - Verify STYLE_GUIDE.MD is comprehensive
  - Update README.md with usage examples
  - _Requirements: 20.1, 20.2, 20.3, 20.4_

- [ ] 21.1 Create usage examples
  - Add example JDs to examples/
  - Add example resumes to examples/
  - Add example outputs to examples/
  - Document common use cases
  - _Requirements: 19.1_

- [ ] 21.2 Add inline documentation
  - Add docstrings to all classes and methods
  - Add type hints throughout codebase
  - Add comments for complex logic
  - _Requirements: 20.1, 20.2, 20.3, 20.4_

- [ ] 22. Performance optimization
  - Profile workflow execution
  - Identify bottlenecks
  - Implement caching where appropriate
  - Optimize prompt sizes
  - _Requirements: 13.1, 13.2_

- [ ] 23. Final integration and testing
  - Run full test suite
  - Verify all 45 correctness properties pass
  - Test with real job descriptions and resumes
  - Verify truth laws are enforced
  - Verify AI detection avoidance works
  - _Requirements: All_

---

## Parallel Execution Strategy

### Phase 1: Foundation (Week 1)
- **Stream A** (1 developer): Core infrastructure

### Phase 2: Agent Development (Weeks 2-3)
- **Stream B** (1 developer): Research, Gap Analyzer, Interrogator
- **Stream C** (1 developer): Differentiator, Tailoring, ATS Optimizer
- **Stream D** (1 developer): Auditor Suite
- **Stream F** (1 developer): Testing infrastructure

### Phase 3: Integration (Week 4)
- **Stream E** (1 developer): Commander and workflow orchestration
- **Stream G** (1 developer): CLI and integration tests
- **Stream H** (1 developer): Documentation

### Phase 4: Polish (Week 5)
- All developers: Final testing, optimization, documentation

This structure allows up to 4 developers/agents to work in parallel during peak development (Phase 2), with clear dependencies and minimal blocking.
