/**
 * Mock responses for Hydra E2E tests.
 * These fixtures mirror the backend Pydantic models.
 */

import type {
    Job,
    JobState,
    FinalDocuments,
    AuditReport,
    ExecutiveBrief,
    SSEProgressEvent,
    SSECompleteEvent,
    SSELogEvent,
    SSEStageCompleteEvent,
} from '../../src/lib/types';

// Job state progression order
export const JOB_STATES: JobState[] = [
    'initialized',
    'gap_analysis',
    'interrogation',
    'differentiation',
    'tailoring',
    'ats_optimization',
    'auditing',
    'completed',
];

// Sample job description content
export const SAMPLE_JOB_DESCRIPTION = `# Senior Software Engineer

## About the Role
We are looking for an experienced software engineer to join our team.

## Requirements
- 5+ years of experience with Python or TypeScript
- Experience with cloud infrastructure (AWS, GCP)
- Strong understanding of distributed systems
- Excellent communication skills

## Nice to Have
- Experience with machine learning
- Kubernetes experience
`;

// Sample resume content
export const SAMPLE_RESUME = `# John Doe
## Senior Software Engineer

### Experience
**Tech Corp** - Senior Engineer (2019-Present)
- Built scalable Python microservices serving 10M+ users
- Led migration to AWS infrastructure
- Mentored junior developers

**Startup Inc** - Software Engineer (2016-2019)
- Developed TypeScript frontend applications
- Implemented CI/CD pipelines

### Skills
Python, TypeScript, AWS, Docker, PostgreSQL
`;

// Mock final documents
export const mockFinalDocuments: FinalDocuments = {
    resume: `# John Doe
## Senior Software Engineer | Python & Cloud Specialist

### Professional Summary
Experienced software engineer with 8+ years building scalable distributed systems.

### Experience
**Tech Corp** - Senior Engineer (2019-Present)
- Architected Python microservices handling 10M+ daily active users
- Led AWS infrastructure migration reducing costs by 40%
- Mentored team of 5 junior developers

### Skills
Python, TypeScript, AWS, Docker, Kubernetes, PostgreSQL
`,
    cover_letter: `Dear Hiring Manager,

I am writing to express my strong interest in the Senior Software Engineer position at your company.

With over 8 years of experience building scalable systems with Python and cloud infrastructure, I am confident I can contribute to your team's success.

At Tech Corp, I led the migration of our core services to AWS, which reduced infrastructure costs by 40% while improving system reliability.

I am excited about the opportunity to bring my expertise in distributed systems and team leadership to your organization.

Best regards,
John Doe
`,
};

// Mock audit report - approved
export const mockAuditReportApproved: AuditReport = {
    final_status: 'APPROVED',
    retry_count: 0,
    resume_audit: {
        truth_check: { passed: true, issues: [] },
        tone_check: { passed: true, issues: [] },
        ats_check: { passed: true, score: 95 },
    },
    cover_letter_audit: {
        truth_check: { passed: true, issues: [] },
        tone_check: { passed: true, issues: [] },
    },
};

// Mock audit report - rejected
export const mockAuditReportRejected: AuditReport = {
    final_status: 'REJECTED',
    retry_count: 2,
    rejection_reason: 'Resume contains unverifiable claims about "10x improvement"',
    resume_audit: {
        truth_check: { passed: false, issues: ['Claim "10x improvement" not supported by source documents'] },
        tone_check: { passed: true, issues: [] },
    },
};

// Mock audit report - crashed
export const mockAuditReportCrashed: AuditReport = {
    final_status: 'AUDIT_CRASHED',
    retry_count: 3,
    crash_error: 'LLM API rate limit exceeded',
};

// Mock executive brief
export const mockExecutiveBrief: ExecutiveBrief = {
    decision: {
        recommendation: 'STRONG_PROCEED',
        fit_score: 85,
        rationale: 'Strong alignment between candidate experience and role requirements, particularly in Python and AWS.',
        deal_makers: [
            '8+ years Python experience exceeds 5 year requirement',
            'Direct AWS migration experience',
            'Team leadership background',
        ],
        deal_breakers: [],
    },
    strategic_angle: {
        primary_hook: 'AWS migration specialist who reduced costs by 40%',
        positioning_summary: 'Position as a senior technical leader who delivers measurable business impact',
        differentiators: [
            { hook: 'Cost optimization expertise', when_to_use: 'When discussing infrastructure decisions' },
            { hook: 'Mentorship track record', when_to_use: 'When discussing team growth' },
        ],
    },
    gap_strategy: {
        critical_gaps: [
            { gap: 'No Kubernetes experience listed', mitigation: 'Emphasize Docker experience and quick learning ability', risk_level: 'low' },
        ],
        interview_landmines: [
            { topic: 'ML experience', preparation: 'Acknowledge as growth area, highlight related data processing work' },
        ],
    },
    action_items: {
        immediate: ['Review tailored resume', 'Practice gap mitigation talking points'],
        pre_interview: ['Research company tech stack', 'Prepare STAR stories for leadership questions'],
        research_needed: ['Company recent product launches', 'Team structure and size'],
    },
    application_materials: {
        resume_verdict: 'Ready to submit - all checks passed',
        cover_letter_verdict: 'Ready to submit - compelling narrative',
        key_changes_made: [
            'Quantified AWS migration impact',
            'Highlighted Python expertise in summary',
            'Added relevant keywords for ATS',
        ],
    },
};

// Mock intermediate results
export const mockIntermediateResults: Record<string, unknown> = {
    gap_analysis: {
        matches: [
            { requirement: 'Python experience', evidence: '5+ years Python development' },
            { requirement: 'AWS experience', evidence: 'Led AWS migration project' },
        ],
        gaps: [
            { requirement: 'Kubernetes', mitigation: 'Docker experience is transferable' },
        ],
    },
    differentiation: {
        differentiators: [
            { angle: 'Cost optimization', evidence: '40% infrastructure cost reduction' },
            { angle: 'Team leadership', evidence: 'Mentored 5 junior developers' },
        ],
    },
    interrogation: {
        questions: [
            {
                gap: 'Kubernetes experience',
                question: 'Describe a time you quickly learned a new technology to solve a business problem',
                star_hints: {
                    situation: 'New project requirement',
                    task: 'Learn and implement',
                    action: 'Self-study and hands-on practice',
                    result: 'Successful delivery',
                },
            },
        ],
    },
};

// Factory function for creating a mock job at any state
export function createMockJob(state: JobState, overrides?: Partial<Job>): Job {
    const stateIndex = JOB_STATES.indexOf(state);
    const progress = state === 'completed' ? 100 : state === 'failed' ? 0 : Math.round((stateIndex / (JOB_STATES.length - 1)) * 100);

    const baseJob: Job = {
        job_id: 'test-job-' + Math.random().toString(36).slice(2, 10),
        state,
        success: state === 'completed',
        progress_percent: progress,
        created_at: new Date().toISOString(),
        started_at: stateIndex > 0 ? new Date().toISOString() : undefined,
        completed_at: state === 'completed' || state === 'failed' ? new Date().toISOString() : undefined,
        execution_log: [],
        audit_failed: false,
    };

    // Add documents and audit report for completed jobs
    if (state === 'completed') {
        baseJob.final_documents = mockFinalDocuments;
        baseJob.audit_report = mockAuditReportApproved;
        baseJob.executive_brief = mockExecutiveBrief;
        baseJob.intermediate_results = mockIntermediateResults;
    }

    // Add error info for failed jobs
    if (state === 'failed') {
        baseJob.error_message = 'Processing failed: LLM API error';
    }

    return { ...baseJob, ...overrides };
}

// SSE event generators
export const mockSSEEvents = {
    connected: (state: JobState = 'initialized', progress: number = 0): string => {
        return `event: connected\ndata: ${JSON.stringify({ state, progress })}\n\n`;
    },

    progress: (state: JobState, progress: number, agent_models?: Record<string, string>): string => {
        const event: SSEProgressEvent = { state, progress, agent_models };
        return `event: progress\ndata: ${JSON.stringify(event)}\n\n`;
    },

    log: (message: string): string => {
        const event: SSELogEvent = { message };
        return `event: log\ndata: ${JSON.stringify(event)}\n\n`;
    },

    stageComplete: (stage: string, result: Record<string, unknown> = {}): string => {
        const event: SSEStageCompleteEvent = { stage, result };
        return `event: stage_complete\ndata: ${JSON.stringify(event)}\n\n`;
    },

    complete: (overrides?: Partial<SSECompleteEvent>): string => {
        const event: SSECompleteEvent = {
            job_id: 'test-job-123',
            success: true,
            state: 'completed',
            final_documents: mockFinalDocuments,
            audit_report: mockAuditReportApproved,
            executive_brief: mockExecutiveBrief,
            audit_failed: false,
            ...overrides,
        };
        return `event: complete\ndata: ${JSON.stringify(event)}\n\n`;
    },

    error: (message: string): string => {
        return `event: error\ndata: ${JSON.stringify({ error: message })}\n\n`;
    },
};

// Full SSE stream simulation for happy path
export function generateHappyPathSSEStream(): string[] {
    const events: string[] = [];

    events.push(mockSSEEvents.connected('initialized', 0));

    const stages: Array<{ state: JobState; progress: number }> = [
        { state: 'gap_analysis', progress: 15 },
        { state: 'interrogation', progress: 30 },
        { state: 'differentiation', progress: 45 },
        { state: 'tailoring', progress: 60 },
        { state: 'ats_optimization', progress: 75 },
        { state: 'auditing', progress: 90 },
    ];

    for (const stage of stages) {
        events.push(mockSSEEvents.progress(stage.state, stage.progress));
        events.push(mockSSEEvents.log(`Starting ${stage.state}...`));
        events.push(mockSSEEvents.stageComplete(stage.state));
    }

    events.push(mockSSEEvents.complete());

    return events;
}

// Full SSE stream simulation for failure path
export function generateFailureSSEStream(failAtState: JobState = 'tailoring'): string[] {
    const events: string[] = [];

    events.push(mockSSEEvents.connected('initialized', 0));

    const stages: Array<{ state: JobState; progress: number }> = [
        { state: 'gap_analysis', progress: 15 },
        { state: 'interrogation', progress: 30 },
        { state: 'differentiation', progress: 45 },
        { state: 'tailoring', progress: 60 },
    ];

    for (const stage of stages) {
        if (stage.state === failAtState) {
            events.push(mockSSEEvents.error(`Processing failed at ${stage.state}`));
            events.push(mockSSEEvents.complete({
                success: false,
                state: 'failed',
                final_documents: undefined,
                audit_report: undefined,
                error_message: `Processing failed at ${stage.state}: LLM API error`,
            }));
            break;
        }
        events.push(mockSSEEvents.progress(stage.state, stage.progress));
        events.push(mockSSEEvents.stageComplete(stage.state));
    }

    return events;
}

// Mock HITL-related responses
export const mockHITLResponses = {
    gapAnalysisReview: {
        gaps: [
            { requirement: 'Kubernetes experience', severity: 'medium', mitigation: 'Docker experience transfers well' },
            { requirement: 'ML experience', severity: 'low', mitigation: 'Data processing background is relevant' },
        ],
        matches: [
            { requirement: 'Python 5+ years', evidence: '8 years of Python development' },
            { requirement: 'AWS experience', evidence: 'Led AWS migration project' },
        ],
    },
    interrogationQuestions: [
        {
            id: 'q1',
            question: 'Describe a time you quickly learned a new technology to meet project requirements.',
            context: 'To address the Kubernetes gap',
            starHints: {
                situation: 'New project requiring unfamiliar tech',
                task: 'Learn and deliver within deadline',
                action: 'Self-study, hands-on practice, team collaboration',
                result: 'Successful implementation',
            },
        },
        {
            id: 'q2',
            question: 'Tell me about a challenging infrastructure optimization you implemented.',
            context: 'To highlight your AWS expertise',
            starHints: {
                situation: 'Performance or cost issue',
                task: 'Identify and implement solution',
                action: 'Analysis, planning, execution',
                result: 'Measurable improvement',
            },
        },
    ],
};

// API error responses
export const mockAPIErrors = {
    notFound: { message: 'Job not found', status: 404 },
    serverError: { message: 'Internal server error', status: 500 },
    validationError: { message: 'Job description is required (min 10 chars)', status: 400 },
    rateLimitError: { message: 'Rate limit exceeded. Please try again later.', status: 429 },
    backendUnavailable: { message: 'Failed to connect to backend. Is the API server running?', status: 503 },
};
