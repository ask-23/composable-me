# ComposableMe Hydra — Agent Architecture Super Prompt

## Project Context

You are working on **ComposableMe**, an agentic job application workflow system. It takes a job description and candidate resume as inputs, runs them through a multi-agent pipeline, and produces tailored application materials (resume, cover letter) along with strategic analysis.

The system is built with CrewAI in a Python runtime, uses multiple LLM providers strategically assigned by agent role, and emphasizes **truth constraints** (no fabrication) and **human voice** (anti-AI detection).

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        COMPOSABLEME HYDRA                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  INPUTS                                                                  │
│  ├── Job Description (JD)                                               │
│  ├── Candidate Resume                                                   │
│  └── Source Documents (optional, for truth verification)                │
│                                                                          │
│  AGENT PIPELINE (Sequential)                                            │
│  ┌──────────────────┐                                                   │
│  │  Gap Analyzer    │ → Requirements mapping, fit classification        │
│  │  [V3.2 TEE]      │                                                   │
│  └────────┬─────────┘                                                   │
│           ▼                                                              │
│  ┌──────────────────┐                                                   │
│  │  Interrogator    │ → STAR+ interview questions for gaps              │
│  │  [Llama 3.3]     │                                                   │
│  └────────┬─────────┘                                                   │
│           ▼                                                              │
│  ┌──────────────────┐                                                   │
│  │  Differentiator  │ → Unique value propositions, positioning          │
│  │  [Sonnet 4]      │                                                   │
│  └────────┬─────────┘                                                   │
│           ▼                                                              │
│  ┌──────────────────┐                                                   │
│  │  Tailoring Agent │ → Resume + cover letter generation                │
│  │  [Sonnet 4]      │                                                   │
│  └────────┬─────────┘                                                   │
│           ▼                                                              │
│  ┌──────────────────┐                                                   │
│  │  ATS Optimizer   │ → Keyword optimization, format check              │
│  │  [Llama 3.3]     │                                                   │
│  └────────┬─────────┘                                                   │
│           ▼                                                              │
│  ┌──────────────────┐                                                   │
│  │  Auditor Suite   │ → Truth/tone/ATS/compliance verification          │
│  │  [R1 0528 TEE]   │   (with retry loop)                               │
│  └────────┬─────────┘                                                   │
│           ▼                                                              │
│  ┌──────────────────┐                                                   │
│  │  Executive       │ → Strategic synthesis, decision brief             │
│  │  Synthesizer     │                                                   │
│  │  [Opus 4.5]      │                                                   │
│  └──────────────────┘                                                   │
│                                                                          │
│  OUTPUTS                                                                 │
│  ├── Tailored Resume (Markdown)                                         │
│  ├── Cover Letter                                                       │
│  ├── Executive Brief (decision + strategy + action items)               │
│  └── Audit Report                                                       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Model Assignment Strategy

### Design Principles

1. **Right-size the model to the task** — Don't use frontier models for mechanical work
2. **TEE for privacy** — Use Trusted Execution Environments when processing PII (resumes)
3. **Human voice where it matters** — Claude for candidate-facing content
4. **Deep reasoning for verification** — R1 for audit tasks
5. **Frontier for synthesis** — Opus for executive-level cross-document reasoning

### Provider Configuration

```python
# runtime/crewai/model_config.py

"""
Model configuration for Composable Me Hydra agents.
Strategic assignment: cost, quality, privacy (TEE where available).
"""

import os
from typing import Dict, Any
from crewai import LLM


AGENT_MODELS: Dict[str, Dict[str, Any]] = {
    # ═══════════════════════════════════════════════════════════════════════
    # COST-EFFECTIVE TIER — Structured analysis, classification, templates
    # Provider: Chutes.ai (TEE) or Together.ai
    # ═══════════════════════════════════════════════════════════════════════
    
    "gap_analyzer": {
        "provider": "chutes",
        "model": "deepseek-ai/DeepSeek-V3.2-TEE",
        "base_url": "https://llm.chutes.ai/v1",
        "temperature": 0.3,  # Lower for consistent classification
        "rationale": """
            Task: Extract requirements from JD, map to resume, classify fit.
            Why V3.2: Structured analysis doesn't need frontier reasoning.
            Why TEE: Processing resume PII — hardware-protected privacy.
            Why not R1: Overkill for classification; R1 reserved for audit.
        """
    },
    
    "ats_optimizer": {
        "provider": "together",
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "temperature": 0.2,
        "rationale": """
            Task: Keyword extraction, format verification, ATS compatibility.
            Why Llama: Mechanical task, cost-effective, fast.
            Why not TEE: Document already processed; less PII exposure.
        """
    },
    
    "interrogator_prepper": {
        "provider": "together",
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "temperature": 0.5,
        "rationale": """
            Task: Generate STAR+ interview questions based on gaps.
            Why Llama: Template-based generation, adequate quality.
            Why not Sonnet: Questions aren't candidate-facing; cost savings.
        """
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # CREATIVE/WRITING TIER — Human voice, narrative, candidate-facing
    # Provider: Anthropic (Claude)
    # ═══════════════════════════════════════════════════════════════════════
    
    "differentiator": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "temperature": 0.7,
        "rationale": """
            Task: Find narrative threads, rare skill combos, positioning angles.
            Why Sonnet: Creative synthesis requires genuine insight.
            Why not Llama: Can't find non-obvious differentiators.
            Why not Opus: Synthesis here is creative, not cross-document.
        """
    },
    
    "tailoring_agent": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "temperature": 0.6,
        "rationale": """
            Task: Generate tailored resume and cover letter.
            Why Sonnet: CRITICAL — This is what hiring managers see.
                - Best natural sentence variation (anti-AI detection)
                - Authentic senior engineer voice
                - Follows "forbidden phrase" rules without slipping
            Why not Opus: Sonnet sufficient; Opus reserved for synthesis.
        """
    },
    
    "commander": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "temperature": 0.4,
        "rationale": """
            Task: Strategic fit assessment, proceed/pass decision.
            Why Sonnet: Judgment + clear communication of rationale.
        """
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # REASONING TIER — Verification, compliance, deep analysis
    # Provider: Chutes.ai (DeepSeek R1 with TEE)
    # ═══════════════════════════════════════════════════════════════════════
    
    "auditor_suite": {
        "provider": "chutes",
        "model": "deepseek-ai/DeepSeek-R1-0528-TEE",
        "base_url": "https://llm.chutes.ai/v1",
        "temperature": 0.2,  # Low for consistent verification
        "rationale": """
            Task: 4-part audit — truth, tone, ATS, compliance verification.
            Why R1 0528: 
                - 671B MoE with 23K-token reasoning chains
                - 87.5% AIME (up from 70% in original R1)
                - Approaches O3/Gemini 2.5 Pro performance
                - Catches edge cases other models miss
            Why TEE: Still processing candidate PII during verification.
            Why not Sonnet: R1's explicit reasoning chains better for 
                            explaining *why* something fails audit.
        """
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # FRONTIER TIER — Executive synthesis, strategic intelligence
    # Provider: Anthropic (Claude Opus)
    # ═══════════════════════════════════════════════════════════════════════
    
    "executive_synthesizer": {
        "provider": "anthropic",
        "model": "claude-opus-4-20250514",
        "temperature": 0.5,
        "rationale": """
            Task: Synthesize ALL agent outputs into strategic executive brief.
            Why Opus:
                - Cross-document reasoning across 6+ agent outputs
                - Strategic judgment, not just summarization
                - Calibrated confidence (knows when to be certain vs uncertain)
                - Efficient communication for senior decision-maker
            Why not Sonnet: Synthesis of this complexity needs frontier.
            Why not R1: R1 is reasoning; Opus is reasoning + communication.
        """
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# LLM Client Factory
# ═══════════════════════════════════════════════════════════════════════════

class LLMClientError(Exception):
    """Raised when LLM client initialization fails"""
    pass


def get_llm_for_agent(agent_type: str) -> LLM:
    """
    Get appropriately configured LLM for a specific agent type.
    
    Args:
        agent_type: One of the keys in AGENT_MODELS
        
    Returns:
        Configured CrewAI LLM instance
        
    Raises:
        LLMClientError: If required API key is missing
    """
    config = AGENT_MODELS.get(agent_type)
    if not config:
        # Fallback to Llama for unknown agents
        config = {
            "provider": "together",
            "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "temperature": 0.5,
        }
    
    provider = config["provider"]
    model = config["model"]
    temperature = config.get("temperature", 0.5)
    
    if provider == "chutes":
        api_key = os.environ.get("CHUTES_API_KEY")
        if not api_key:
            raise LLMClientError(
                "CHUTES_API_KEY required for Chutes TEE models.\n"
                "Get key from: https://chutes.ai"
            )
        
        return LLM(
            model=f"openai/{model}",  # LiteLLM OpenAI-compatible prefix
            api_key=api_key,
            base_url=config.get("base_url", "https://llm.chutes.ai/v1"),
            temperature=temperature,
        )
    
    elif provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            # Fallback to OpenRouter for Anthropic models
            openrouter_key = os.environ.get("OPENROUTER_API_KEY")
            if not openrouter_key:
                raise LLMClientError(
                    "ANTHROPIC_API_KEY or OPENROUTER_API_KEY required.\n"
                    "Get Anthropic key from: https://console.anthropic.com\n"
                    "Get OpenRouter key from: https://openrouter.ai/keys"
                )
            
            return LLM(
                model=f"openrouter/anthropic/{model}",
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1",
                temperature=temperature,
            )
        
        return LLM(
            model=model,
            api_key=api_key,
            temperature=temperature,
        )
    
    elif provider == "together":
        api_key = os.environ.get("TOGETHER_API_KEY")
        if not api_key:
            raise LLMClientError(
                "TOGETHER_API_KEY required for Together.ai models.\n"
                "Get key from: https://api.together.xyz/settings/api-keys"
            )
        
        return LLM(
            model=f"together_ai/{model}",
            api_key=api_key,
            temperature=temperature,
        )
    
    else:
        raise LLMClientError(f"Unknown provider: {provider}")


def get_all_required_env_vars() -> list[str]:
    """Return list of all environment variables needed for full pipeline."""
    return [
        "CHUTES_API_KEY",      # For V3.2 TEE (gap) and R1 TEE (audit)
        "TOGETHER_API_KEY",    # For Llama 3.3 (ATS, interrogator)
        "ANTHROPIC_API_KEY",   # For Claude Sonnet/Opus (differentiator, tailor, exec)
    ]
```

---

## Agent Definitions

### 1. Gap Analyzer

**Purpose:** Map job requirements to candidate experience with precise classification.

**Model:** `deepseek-ai/DeepSeek-V3.2-TEE` via Chutes.ai

**Input:**
- Job description text
- Candidate resume text
- Optional research data

**Output Schema:**
```yaml
gap_analysis:
  meta:
    role: "Senior DevOps Engineer"
    company: "TechCorp"
    analyzed: "2025-01-10"
  
  summary:
    fit_score: 83
    recommendation: "PURSUE"
    blockers: 0
    interview_topics: 2
  
  requirements:
    - id: 1
      text: "5+ years AWS experience"
      type: "explicit_hard"
      classification: "direct_match"  # direct_match | adjacent | gap | blocker
      evidence: "Limecord, T-Mobile, Agora — 6+ years total"
      confidence: "high"
      interview_needed: false
    
    - id: 2
      text: "Kubernetes experience"
      type: "explicit_soft"
      classification: "adjacent"
      evidence: "ECS Fargate, Docker, container orchestration"
      confidence: "medium"
      interview_needed: true
      framing: "Container orchestration via ECS; Kubernetes-adjacent"
```

**Classification Rules:**
- `direct_match`: Clear evidence of meeting/exceeding requirement
- `adjacent`: Related experience that demonstrates capability (must be framed honestly)
- `gap`: No direct or adjacent experience found
- `blocker`: Cannot be addressed through framing or transfer (dealbreaker)

---

### 2. Interrogator-Prepper

**Purpose:** Generate targeted interview questions to extract truthful details that fill gaps.

**Model:** `meta-llama/Llama-3.3-70B-Instruct-Turbo` via Together.ai

**Input:**
- Job description
- Resume
- Gap analysis output
- Identified gaps list

**Output Schema:**
```yaml
interrogation_prep:
  questions:
    - id: 1
      theme: "technical"  # technical | leadership | outcomes | tools
      question: "Describe your container orchestration experience with ECS."
      format: "STAR+"
      target_gap: "Kubernetes experience"
      why_asking: "Need to establish transferable container knowledge"
      follow_ups:
        - "What orchestration patterns did you implement?"
        - "How does ECS compare to K8s in your understanding?"
    
    - id: 2
      theme: "outcomes"
      question: "Walk me through a deployment transformation you led."
      format: "STAR+"
      target_gap: "CI/CD leadership"
      why_asking: "Need quantified impact story"
  
  verification_framework:
    - "For metrics: ask for source (dashboard, report, estimate)"
    - "For tools: ask for specific version/configuration"
    - "For outcomes: ask for before/after comparison"
```

**STAR+ Format:**
- **S**ituation: Where was this? What was the context?
- **T**ask: What specifically were you responsible for?
- **A**ctions: Walk me through what YOU did (not the team)
- **R**esults: What changed? Can you quantify it?
- **+Proof**: How would someone verify this?

---

### 3. Differentiator

**Purpose:** Find what makes this candidate memorable and distinct from 200 other qualified applicants.

**Model:** `claude-sonnet-4-20250514` via Anthropic

**Input:**
- Job description
- Resume
- Gap analysis
- Interview notes (if available)

**Output Schema:**
```yaml
differentiation_report:
  primary_differentiator:
    hook: "Builds systems that eliminate bottlenecks, including himself"
    evidence:
      - "CI/CD transformation: teams ship without DevOps approval"
      - "Self-service infrastructure: 80% reduction in ops tickets"
    why_compelling: |
      Most DevOps become gatekeepers. This candidate systematically
      removes friction and makes teams autonomous.
    jd_resonance: |
      JD emphasizes 'developer velocity' and 'autonomous teams'—
      this is exactly what they're describing.
  
  secondary_differentiators:
    - angle: "Enterprise compliance + startup speed"
      evidence: "SOC2 at multiple companies without slowing shipping"
      when_to_use: "If compliance mentioned in JD"
    
    - angle: "AWS depth rarely seen outside FAANG"
      evidence: "Multi-account governance, landing zones, org-level"
      when_to_use: "If AWS emphasis in JD"
  
  narrative_thread:
    theme: "The Bottleneck Eliminator"
    story: |
      Career arc is consistent: arrive, find what's slowing people down,
      build systems that remove the friction, move on to harder problems.
  
  contrarian_positions:
    - position: "ECS over Kubernetes"
      framing: "Chose simplicity over hype; right-sized for context"
      when_to_deploy: "If K8s comes up as a gap"
  
  application_guidance:
    resume_emphasis:
      - "Lead with outcomes, not responsibilities"
      - "Quantify the before/after on bottleneck removal"
    cover_letter_angle:
      - "Open with 'builds himself out of the job' hook"
```

**Differentiation Levels:**
1. **Skill Combinations** — Rare combos that most candidates don't have
2. **Outcome Stories** — Not what you did, but what changed because you did it
3. **Narrative Threads** — The through-line that makes sense of a career
4. **Contrarian Strengths** — Things that seem negative but are advantages
5. **Cultural Fit Signals** — Alignment beyond skills

---

### 4. Tailoring Agent

**Purpose:** Generate tailored resume and cover letter that sound human, not AI.

**Model:** `claude-sonnet-4-20250514` via Anthropic

**Input:**
- Job description
- Baseline resume
- Gap analysis
- Interview notes
- Differentiators

**Output Schema:**
```yaml
tailored_output:
  meta:
    role: "Senior Platform Engineer"
    company: "TechCorp"
    version: 1
  
  resume:
    format: "markdown"
    content: |
      # Alex Chen
      San Francisco, CA | alex@email.com | linkedin.com/in/alexchen
      
      ## Summary
      Platform engineer who builds systems that make themselves unnecessary.
      8+ years turning deployment bottlenecks into self-service platforms.
      AWS, Terraform, CI/CD — the boring stuff that lets teams ship.
      
      ## Experience
      
      ### Senior Platform Engineer | Limecord
      2023 – Present | Remote
      
      - Designed multi-account AWS architecture serving 40+ developers;
        environment provisioning dropped from 2 weeks to 2 hours
      - Built CI/CD that removed me as bottleneck — teams deploy without
        waiting for ops approval, ship 3x more frequently
      - Led SOC2 compliance; passed first audit with zero critical findings
      
      ...
    
    notes:
      - "Emphasized cloud architecture per JD priority"
      - "Used 'developer velocity' language from JD"
      - "Quantified all major achievements"
  
  cover_letter:
    format: "markdown"
    content: |
      At T-Mobile, I built the CI/CD system that let 200 developers ship
      without waiting for ops. I'd like to do that for TechCorp.
      
      Your posting mentions "developer velocity" and "autonomous teams."
      That's been my focus for eight years: arrive somewhere, find what's
      slowing people down, build systems that remove the friction. At
      Limecord, that meant multi-account AWS architecture that cut
      environment provisioning from two weeks to two hours...
    
    notes:
      - "Opened with bottleneck elimination angle"
      - "Connected to specific JD language"
  
  source_mapping:
    - claim: "Led SOC2 compliance"
      source: "resume_merged.md, Limecord section"
    - claim: "200 developers"
      source: "interview_notes, T-Mobile theme"
```

**Anti-AI Language Rules (INVIOLABLE):**

```yaml
forbidden_phrases:
  - "proven track record"
  - "passionate about"
  - "leverage my expertise"
  - "drive innovation"
  - "rapidly evolving"
  - "best-in-class"
  - "cutting-edge"
  - "seamlessly"
  - "spearheaded"
  - "synergize"

required_patterns:
  - "Mix of sentence lengths"
  - "Specific numbers (47, not 'approximately 50')"
  - "Active voice dominance"
  - "Occasional sentence fragments. Like this."
  - "Natural rhythm breaks"

bullet_formula: "[Action Verb] + [What You Did] + [Scale/Scope] + [Result/Impact]"
```

---

### 5. ATS Optimizer

**Purpose:** Ensure documents pass automated screening without sacrificing human readability.

**Model:** `meta-llama/Llama-3.3-70B-Instruct-Turbo` via Together.ai

**Input:**
- Tailored resume
- Job description
- Source documents

**Output Schema:**
```yaml
ats_report:
  keyword_analysis:
    hard_requirements:
      - keyword: "AWS"
        status: "present"
        count: 8
      - keyword: "Terraform"
        status: "present"
        count: 5
      - keyword: "Python"
        status: "missing_but_claimable"
        action: "Add to skills section"
    
    coverage_score: "85%"
  
  format_analysis:
    issues_found: 2
    issues_fixed: 2
    fixes:
      - "Converted skills table to comma-separated list"
      - "Standardized bullet characters to -"
  
  optimized_resume: |
    [Full optimized resume with keywords added]
  
  changes_made:
    - "Added 'CI/CD' to deployment bullet"
    - "Added 'IaC' near Terraform mention"
    - "Added 'Linux' to skills"
```

**ATS Rules:**
- No tables (text scrambles)
- No multi-column layouts
- No images or icons
- Standard section headers (Experience, Education, Skills)
- Keywords in context, not just skills section

---

### 6. Auditor Suite

**Purpose:** Final verification that all outputs are truthful, human-sounding, compliant, and ATS-ready.

**Model:** `deepseek-ai/DeepSeek-R1-0528-TEE` via Chutes.ai

**Why R1 0528:**
- 671B MoE with 37B active parameters
- 23K-token reasoning chains (vs 12K in original R1)
- 87.5% on AIME 2025 (up from 70%)
- Approaches O3 and Gemini 2.5 Pro performance
- TEE ensures privacy during PII verification

**Input:**
- Document to audit (resume or cover letter)
- Document type
- Job description
- Source documents
- Target role

**Output Schema:**
```yaml
audit_report:
  meta:
    document_type: "resume"
    target_role: "Senior Platform Engineer"
    audited: "2025-01-10T10:30:00Z"
  
  summary:
    overall_status: "PASS" | "FAIL" | "CONDITIONAL"
    blocking_issues: 0
    warnings: 2
    recommendations: 3
  
  truth_audit:
    status: "PASS"
    verified_claims: 15
    approximate_claims: 2
    issues: []
  
  tone_audit:
    status: "CONDITIONAL"
    score: "human" | "borderline" | "robotic"
    issues:
      - id: "TONE-001"
        location: "Summary, line 2"
        pattern: "leverage my expertise"
        severity: "warning"
        fix: "Replace with specific skill mention"
  
  ats_audit:
    status: "PASS"
    keyword_coverage: "85%"
    format_issues: []
  
  compliance_audit:
    status: "PASS"
    violations: []
  
  approval:
    approved: true | false
    reason: "String explanation"
    next_steps: "What to do if not approved"
```

**Audit Components:**
1. **Truth Audit** — Every claim traceable to source documents
2. **Tone Audit** — Detect AI patterns, enforce human voice
3. **ATS Audit** — Keyword coverage, format verification
4. **Compliance Audit** — AGENTS.MD rules followed

**Severity Levels:**
- `blocking`: Must fix before document can be used
- `warning`: Should fix, but can proceed if urgent
- `recommendation`: Would improve quality

---

### 7. Executive Synthesizer (NEW)

**Purpose:** Transform 6+ agent reports into a single strategic intelligence product.

**Model:** `claude-opus-4-20250514` via Anthropic

**Why Opus:**
- Cross-document reasoning across all agent outputs
- Strategic judgment, not just summarization
- Calibrated confidence (knows when to be certain vs uncertain)
- Efficient communication for senior decision-maker

**Input:**
- All prior agent outputs:
  - Gap analysis
  - Interrogation prep
  - Differentiation
  - Tailored documents
  - ATS optimization
  - Audit report
- Original job description
- Original resume

**Output Schema:**
```yaml
executive_brief:
  meta:
    role: "Senior Platform Engineer"
    company: "TechCorp"
    generated: "2025-01-10T12:00:00Z"
    confidence: 0.85
  
  decision:
    recommendation: "STRONG_PROCEED" | "PROCEED" | "PROCEED_WITH_CAUTION" | "PASS"
    fit_score: 83
    rationale: |
      Strong technical fit (83%) with no blockers. Primary differentiator
      (bottleneck elimination) aligns directly with JD language about
      developer velocity. Two adjacent skills (K8s, GCP) have clear
      mitigation strategies.
    
    deal_breakers: []
    deal_makers:
      - "AWS depth matches their multi-account needs"
      - "SOC2 experience for their compliance push"
      - "Self-service platform builder — exactly what JD describes"
  
  strategic_angle:
    primary_hook: |
      "Builds systems that eliminate bottlenecks, including himself"
    
    positioning_summary: |
      Position as the person who will make their platform team unnecessary
      for routine developer requests. Lead with outcomes (2 weeks → 2 hours),
      not responsibilities.
    
    differentiators_to_emphasize:
      - hook: "Bottleneck eliminator"
        deploy_in: ["resume summary", "cover letter opening", "interview intro"]
      
      - hook: "Enterprise compliance without enterprise slowness"
        deploy_in: ["cover letter body", "if compliance comes up"]
    
    narrative_thread: |
      Career arc: arrive → find friction → build systems that remove it →
      move on. Consistent for 8 years across T-Mobile, Agora, Limecord.
  
  gap_strategy:
    critical_gaps:
      - gap: "Kubernetes (they mention it, you have ECS)"
        mitigation: "Frame as container orchestration expertise; express
                    K8s learning interest; emphasize concepts over tools"
        risk_level: "medium"
    
    adjacent_framing:
      - requirement: "Kubernetes orchestration"
        positioning: "Container orchestration via ECS Fargate; familiar with
                     K8s concepts and patterns, hands-on with ECS"
    
    interview_landmines:
      - topic: "Why no direct Kubernetes experience?"
        preparation: "Chose ECS for simplicity at scale we needed; understand
                     K8s concepts; interested in deepening hands-on"
  
  application_materials:
    resume_verdict: "APPROVED"
    cover_letter_verdict: "APPROVED"
    
    key_changes_made:
      - "Emphasized AWS multi-account per JD priority"
      - "Added 'developer velocity' language from JD"
      - "Quantified all outcomes with before/after"
    
    remaining_issues: []
  
  interview_prep:
    priority_questions:
      - question: "Tell me about a time you improved developer velocity"
        preparation_note: "Use Limecord CI/CD story — 2 weeks to 2 hours"
      
      - question: "How do you approach platform team prioritization?"
        preparation_note: "Talk about bottleneck identification framework"
    
    stories_to_prepare:
      - theme: "Bottleneck elimination"
        example: "Limecord CI/CD transformation"
      
      - theme: "Compliance without slowdown"
        example: "SOC2 first-attempt pass"
    
    company_research_gaps:
      - "What's their current deployment frequency?"
      - "Are they multi-cloud or AWS-only?"
  
  risk_assessment:
    application_risks:
      - risk: "K8s gap flagged in screening"
        probability: "medium"
        mitigation: "Cover letter addresses container experience directly"
    
    role_risks:
      - risk: "JD says 'fast-paced' — may mean under-resourced"
        signal: "'Wear many hats' language"
  
  action_items:
    immediate:
      - "Submit application with tailored resume + cover letter"
      - "Connect with [recruiter name] on LinkedIn if found"
    
    pre_interview:
      - "Polish Limecord CI/CD story with specific metrics"
      - "Research their engineering blog for platform team structure"
    
    research_needed:
      - "Current tech stack (job mentions AWS, confirm no GCP)"
      - "Team size and reporting structure"
```

**Decision Framework:**
```yaml
STRONG_PROCEED:
  - fit_score >= 80
  - blockers == 0
  - at_least_one_strong_differentiator
  - role_level_appropriate

PROCEED:
  - fit_score >= 65
  - blockers == 0
  - gaps_have_mitigation_strategy

PROCEED_WITH_CAUTION:
  - fit_score >= 50
  - blockers <= 1 (with strong mitigation)
  - OR role has significant upside despite gaps

PASS:
  - fit_score < 50
  - OR blockers > 1
  - OR role_level_mismatch
  - OR critical red_flags
```

---

## Truth Laws (INVIOLABLE)

These rules apply to ALL agents and cannot be overridden:

```markdown
1. CHRONOLOGY IS SACRED
   - Dates, job order, and tenure must match reality exactly
   - No reordering jobs to look better
   - No adjusting dates to close gaps

2. NO FABRICATION
   - No invented tools, metrics, or achievements
   - No technologies not in source documents
   - No certifications not held
   - "If it didn't happen, don't write it"

3. SOURCE AUTHORITY
   - Every claim must trace to resume or interview notes
   - "Approximately" must be labeled as such
   - Unverified claims are blocked until confirmed

4. ADJACENT ≠ DIRECT
   - Transferable experience framed honestly
   - "Container orchestration via ECS" NOT "Kubernetes expert"
   - Related skills positioned as related, not equivalent

5. METRICS REQUIRE PROOF
   - Ask for source of numbers
   - Note if exact or approximate
   - Record confidence level
```

---

## Cost Estimation

| Agent | Model | Provider | Est. Cost/Run |
|-------|-------|----------|---------------|
| Gap Analyzer | DeepSeek V3.2 TEE | Chutes | ~$0.03 |
| Interrogator | Llama 3.3 70B | Together | ~$0.01 |
| Differentiator | Claude Sonnet 4 | Anthropic | ~$0.08 |
| Tailoring | Claude Sonnet 4 | Anthropic | ~$0.12 |
| ATS Optimizer | Llama 3.3 70B | Together | ~$0.01 |
| Commander | Claude Sonnet 4 | Anthropic | ~$0.06 |
| Auditor | DeepSeek R1 0528 TEE | Chutes | ~$0.15 |
| Executive | Claude Opus 4.5 | Anthropic | ~$0.30 |
| **Total** | | | **~$0.76/application** |

---

## Environment Setup

```bash
# Required environment variables
export CHUTES_API_KEY="your_chutes_key"        # For V3.2 TEE and R1 0528 TEE
export TOGETHER_API_KEY="your_together_key"    # For Llama 3.3 70B
export ANTHROPIC_API_KEY="your_anthropic_key"  # For Claude Sonnet 4 and Opus 4.5

# Optional fallback
export OPENROUTER_API_KEY="sk-or-..."          # Fallback for Anthropic models
```

---

## File Structure

```
composableme/
├── agents/
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
│   ├── auditor-suite/
│   │   └── prompt.md
│   ├── commander/
│   │   └── prompt.md
│   └── executive-synthesizer/
│       └── prompt.md              # NEW — needs to be created
├── runtime/
│   └── crewai/
│       ├── __init__.py
│       ├── model_config.py        # Model assignments (see above)
│       ├── llm_client.py          # Multi-provider LLM factory
│       ├── base_agent.py          # Base class with truth rules
│       ├── hydra_workflow.py      # Pipeline orchestration
│       ├── cli.py                 # Command-line interface
│       └── agents/
│           ├── gap_analyzer.py
│           ├── interrogator_prepper.py
│           ├── differentiator.py
│           ├── tailoring_agent.py
│           ├── ats_optimizer.py
│           ├── auditor.py
│           ├── commander.py
│           └── executive_synthesizer.py  # NEW — needs to be created
├── docs/
│   ├── AGENTS.MD                  # Truth laws
│   └── STYLE_GUIDE.MD             # Anti-AI writing rules
├── inputs/
│   └── [job descriptions and resumes]
└── output/
    └── [generated documents]
```

---

## Implementation Tasks

1. **Create `agents/executive-synthesizer/prompt.md`** — Full prompt from this spec
2. **Create `runtime/crewai/agents/executive_synthesizer.py`** — Agent implementation
3. **Update `runtime/crewai/model_config.py`** — Add all model assignments
4. **Update `runtime/crewai/llm_client.py`** — Multi-provider factory with Chutes support
5. **Update `runtime/crewai/hydra_workflow.py`** — Add Executive Synthesizer to pipeline
6. **Test full pipeline** — JD → all agents → executive brief

---

## Usage

```bash
# Run full pipeline
python -m runtime.crewai.cli \
  --jd inputs/techcorp-platform-engineer.md \
  --resume inputs/resume.md \
  --sources inputs/ \
  --out output/techcorp/

# Output files
output/techcorp/
├── resume.md           # Tailored resume
├── cover_letter.md     # Tailored cover letter
├── executive_brief.yaml # Strategic decision brief
├── audit_report.yaml   # Verification results
└── execution_log.txt   # Agent execution trace
```

---

## Key Reminders for Implementation

1. **TEE models (Chutes) require `openai/` prefix** for LiteLLM compatibility
2. **R1 0528 has 23K token thinking** — budget for longer responses
3. **Sonnet 4 model string is `claude-sonnet-4-20250514`** — not sonnet-4.5
4. **Opus 4.5 model string is `claude-opus-4-20250514`** — check Anthropic docs
5. **Temperature matters** — low (0.2-0.3) for verification, higher (0.6-0.7) for creative
6. **Truth laws are non-negotiable** — every agent must enforce them
7. **Executive Synthesizer runs LAST** — needs all other outputs as input
