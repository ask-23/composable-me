/**
 * TypeScript types for Hydra web frontend.
 * These mirror the backend Pydantic models.
 */

export type JobState =
  | 'initialized'
  | 'gap_analysis'
  | 'gap_analysis_review'
  | 'interrogation'
  | 'interrogation_review'
  | 'differentiation'
  | 'tailoring'
  | 'ats_optimization'
  | 'auditing'
  | 'executive_synthesis'
  | 'completed'
  | 'failed';

export type AuditStatus = 'APPROVED' | 'REJECTED' | 'AUDIT_CRASHED';

export interface CreateJobRequest {
  job_description: string;
  resume: string;
  source_documents: string;
  model?: string;
  max_audit_retries?: number;
}

export interface CreateJobResponse {
  job_id: string;
  status: string;
  created_at: string;
}

export interface FinalDocuments {
  resume: string;
  cover_letter: string;
}

export interface AuditReport {
  resume_audit?: Record<string, unknown>;
  cover_letter_audit?: Record<string, unknown>;
  final_status?: AuditStatus;
  retry_count: number;
  rejection_reason?: string;
  crash_error?: string;
}

export interface ExecutiveBrief {
  decision: {
    recommendation: 'STRONG_PROCEED' | 'PROCEED' | 'PROCEED_WITH_CAUTION' | 'PASS';
    fit_score: number;
    rationale: string;
    deal_makers?: string[];
    deal_breakers?: string[];
  };
  strategic_angle?: {
    primary_hook?: string;
    positioning_summary?: string;
    differentiators?: Array<{ hook: string; when_to_use?: string }>;
    narrative_thread?: string;
  };
  gap_strategy?: {
    critical_gaps?: Array<{ gap: string; mitigation: string; risk_level?: string }>;
    interview_landmines?: Array<{ topic: string; preparation: string }>;
  };
  action_items?: {
    immediate?: string[];
    pre_interview?: string[];
    research_needed?: string[];
  };
  application_materials?: {
    resume_verdict?: string;
    cover_letter_verdict?: string;
    key_changes_made?: string[];
  };
}

// Gap Analysis types for HITL review
export interface GapAnalysisRequirement {
  requirement?: string;
  text?: string; // Sometimes used by LLM instead of requirement
  classification: 'direct_match' | 'adjacent_experience' | 'adjacent' | 'gap' | 'blocker';
  evidence?: string;
  confidence?: number | string;
  notes?: string;
}

export interface GapAnalysisResult {
  requirements?: GapAnalysisRequirement[];
  requirements_analysis?: {
    explicit_required?: GapAnalysisRequirement[];
    explicit_preferred?: GapAnalysisRequirement[];
    implicit_requirements?: GapAnalysisRequirement[];
  };
  fit_score?: number | string;
  summary?: {
    fit_score?: number | string;
    overall_assessment?: string;
  };
  gaps?: string[];
  matches?: string[];
  adjacent_skills?: string[];
  blockers?: string[];
}

// Interrogation/Interview types for HITL
export interface InterrogationQuestion {
  id?: string;
  theme?: 'technical' | 'leadership' | 'outcomes' | 'tools' | string;
  question: string;
  format?: string;
  target_gap?: string;
  why_asking?: string;
  context?: string;
  skill_gap?: string;
}

export interface InterrogationResult {
  questions: InterrogationQuestion[];
  interview_notes?: InterviewAnswer[];
}

export interface InterviewAnswer {
  question: string;
  answer: string;
  question_id?: string;
  verified?: boolean;
  source_material?: boolean;
}

export interface Job {
  job_id: string;
  state: JobState;
  success: boolean;
  progress_percent: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  final_documents?: FinalDocuments;
  audit_report?: AuditReport;
  executive_brief?: ExecutiveBrief;
  intermediate_results?: Record<string, unknown>;
  execution_log: string[];
  error_message?: string;
  audit_failed: boolean;
  audit_error?: string;
  agent_models?: Record<string, string>;
}

// SSE event types
export interface SSEProgressEvent {
  state: JobState;
  progress: number;
  agent_models?: Record<string, string>;
}

export interface SSELogEvent {
  message: string;
}

export interface SSEStageCompleteEvent {
  stage: string;
  result: Record<string, unknown>;
}

export interface SSECompleteEvent {
  job_id: string;
  success: boolean;
  state: JobState;
  final_documents?: FinalDocuments;
  audit_report?: AuditReport;
  executive_brief?: ExecutiveBrief;
  audit_failed: boolean;
  audit_error?: string;
  error_message?: string;
  agent_models?: Record<string, string>;
}

// Stage metadata for UI display with agent info and fun facts
export const STAGE_INFO: Record<JobState, {
  label: string;
  description: string;
  agentName: string;
  role: string;
  funFact: string;
}> = {
  initialized: {
    label: 'Starting',
    description: 'Initializing workflow...',
    agentName: 'Hydra Orchestrator',
    role: 'Coordinates the multi-agent pipeline and manages state transitions.',
    funFact: 'Named after the mythical Hydra - cut off one head and two grow back. Our system has 6 specialized heads working in harmony!'
  },
  gap_analysis: {
    label: 'Gap Analysis',
    description: 'Mapping job requirements to your experience...',
    agentName: 'Gap Analyzer',
    role: 'Reads the job description and your resume to identify direct matches, adjacent skills, and gaps that need addressing.',
    funFact: 'This agent reads between the lines - it knows that "Python expertise" and "Django experience" are related even when not explicitly stated!'
  },
  gap_analysis_review: {
    label: 'Review Gap Analysis',
    description: 'Waiting for your review of the gap analysis...',
    agentName: 'Gap Analyzer',
    role: 'The analysis is complete. Review the findings and approve to continue, or request revisions.',
    funFact: 'Your input here shapes how the rest of the pipeline frames your experience!'
  },
  interrogation: {
    label: 'Interview Prep',
    description: 'Generating STAR+ questions for identified gaps...',
    agentName: 'Interrogator-Prepper',
    role: 'Creates behavioral interview questions using the STAR+ method to help you prepare narratives for any skill gaps.',
    funFact: 'STAR+ adds a "Takeaway" to the classic STAR method - because interviewers love candidates who reflect on their growth!'
  },
  interrogation_review: {
    label: 'Answer Questions',
    description: 'Please answer the interview questions to strengthen your application...',
    agentName: 'Interrogator-Prepper',
    role: 'Your answers will be used to add authentic details to your resume and cover letter.',
    funFact: 'The best answers include specific numbers, dates, and outcomes - they make your stories memorable!'
  },
  differentiation: {
    label: 'Differentiation',
    description: 'Finding what makes you uniquely valuable...',
    agentName: 'Differentiator',
    role: 'Analyzes your background to identify unique value propositions that set you apart from other candidates.',
    funFact: 'This agent thinks like a hiring manager who\'s seen 500 resumes - it finds the angle that makes yours memorable!'
  },
  tailoring: {
    label: 'Tailoring',
    description: 'Crafting your resume and cover letter...',
    agentName: 'Tailoring Agent',
    role: 'Creates customized resume and cover letter that highlight relevant experience and address the specific job requirements.',
    funFact: 'Studies show tailored resumes are 3x more likely to get interviews than generic ones. This agent does that tailoring automatically!'
  },
  ats_optimization: {
    label: 'ATS Optimization',
    description: 'Optimizing for automated screening systems...',
    agentName: 'ATS Optimizer',
    role: 'Ensures your documents pass Applicant Tracking Systems by optimizing keywords, formatting, and structure.',
    funFact: '75% of resumes are rejected by ATS before a human ever sees them. This agent speaks fluent robot!'
  },
  auditing: {
    label: 'Auditing',
    description: 'Verifying truth, tone, and compliance...',
    agentName: 'Auditor Suite',
    role: 'Runs 4 audits: Truth (verifies claims against your sources), Tone (removes AI patterns), ATS (keyword coverage), and Compliance (follows rules).',
    funFact: 'This agent is the quality gatekeeper - it catches phrases like "leverage synergies" and replaces them with human language!'
  },
  executive_synthesis: {
    label: 'Executive Brief',
    description: 'Creating strategic summary and recommendations...',
    agentName: 'Executive Synthesizer',
    role: 'Creates a strategic brief summarizing fit analysis, key differentiators, and action items for your application.',
    funFact: 'This agent thinks like a hiring manager - it distills hours of analysis into a 2-minute read!'
  },
  completed: {
    label: 'Complete',
    description: 'Your application materials are ready!',
    agentName: 'Mission Accomplished',
    role: 'All agents have completed their work. Your tailored documents are ready for review.',
    funFact: 'The average job application takes 30 minutes to customize. Hydra just did it in under 2 minutes!'
  },
  failed: {
    label: 'Failed',
    description: 'An error occurred during processing.',
    agentName: 'Error Handler',
    role: 'Something went wrong, but don\'t worry - your partial results may still be useful.',
    funFact: 'Even failures teach us something. Check the debug tab for intermediate results that were saved!'
  },
};

// Ordered stages for progress tracking (all states)
export const STAGES: JobState[] = [
  'initialized',
  'gap_analysis',
  'gap_analysis_review',
  'interrogation',
  'interrogation_review',
  'differentiation',
  'tailoring',
  'ats_optimization',
  'auditing',
  'executive_synthesis',
  'completed',
];

// Stages to display in the progress bar UI (simplified view)
// Excludes review states and executive_synthesis for cleaner UX
export const UI_STAGES: JobState[] = [
  'initialized',
  'gap_analysis',
  'interrogation',
  'tailoring',
  'ats_optimization',
  'auditing',
  'completed',
];

// Helper to check if a state is a HITL review state
export function isReviewState(state: JobState): boolean {
  return state === 'gap_analysis_review' || state === 'interrogation_review';
}
