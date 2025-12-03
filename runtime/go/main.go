// Package hydra provides the Composable Me multi-agent job search system.
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"time"
)

// WorkflowState tracks the current state of a job application workflow.
type WorkflowState struct {
	ID        string    `json:"id"`
	Created   time.Time `json:"created"`
	Status    string    `json:"status"` // in_progress, awaiting_user, complete, failed
	Stage     string    `json:"stage"`
	
	// Inputs
	JobDescription string `json:"job_description"`
	BaselineResume string `json:"baseline_resume"`
	
	// Agent outputs (stored as raw JSON for flexibility)
	Research     json.RawMessage `json:"research,omitempty"`
	GapAnalysis  json.RawMessage `json:"gap_analysis,omitempty"`
	Interview    json.RawMessage `json:"interview,omitempty"`
	Differentiator json.RawMessage `json:"differentiator,omitempty"`
	Tailored     json.RawMessage `json:"tailored,omitempty"`
	ATSOptimized json.RawMessage `json:"ats_optimized,omitempty"`
	Audit        json.RawMessage `json:"audit,omitempty"`
	
	// User interactions
	Greenlight *bool  `json:"greenlight,omitempty"`
	UserNotes  string `json:"user_notes,omitempty"`
	
	// Error tracking
	Errors []WorkflowError `json:"errors,omitempty"`
}

// WorkflowError captures errors during workflow execution.
type WorkflowError struct {
	Stage      string    `json:"stage"`
	Message    string    `json:"message"`
	Timestamp  time.Time `json:"timestamp"`
	Resolution string    `json:"resolution,omitempty"`
}

// AgentInput is the standard input structure for all agents.
type AgentInput struct {
	JobDescription string          `json:"job_description"`
	BaselineResume string          `json:"baseline_resume"`
	PriorOutputs   map[string]json.RawMessage `json:"prior_outputs,omitempty"`
	UserInput      string          `json:"user_input,omitempty"`
}

// AgentOutput is the standard output structure for all agents.
type AgentOutput struct {
	AgentName  string          `json:"agent_name"`
	Timestamp  time.Time       `json:"timestamp"`
	Success    bool            `json:"success"`
	Data       json.RawMessage `json:"data"`
	Errors     []string        `json:"errors,omitempty"`
	Confidence float64         `json:"confidence,omitempty"`
}

// Agent defines the interface all agents must implement.
type Agent interface {
	Name() string
	Execute(ctx context.Context, input AgentInput) (AgentOutput, error)
}

// LLMClient abstracts the LLM API calls.
type LLMClient interface {
	Complete(ctx context.Context, systemPrompt, userPrompt string) (string, error)
}

// Workflow orchestrates the agent execution.
type Workflow struct {
	State   *WorkflowState
	Agents  map[string]Agent
	LLM     LLMClient
}

// NewWorkflow creates a new workflow instance.
func NewWorkflow(llm LLMClient) *Workflow {
	return &Workflow{
		State: &WorkflowState{
			ID:      generateID(),
			Created: time.Now(),
			Status:  "in_progress",
			Stage:   "init",
		},
		Agents: make(map[string]Agent),
		LLM:    llm,
	}
}

// RegisterAgent adds an agent to the workflow.
func (w *Workflow) RegisterAgent(agent Agent) {
	w.Agents[agent.Name()] = agent
}

// Run executes the full workflow.
func (w *Workflow) Run(ctx context.Context, jd, resume string) error {
	w.State.JobDescription = jd
	w.State.BaselineResume = resume
	
	stages := []string{
		"research",
		"gap_analysis",
		"greenlight",     // Requires user input
		"interview",
		"differentiator",
		"tailoring",
		"ats_optimizer",
		"audit",
	}
	
	for _, stage := range stages {
		w.State.Stage = stage
		log.Printf("Executing stage: %s", stage)
		
		// Handle human-in-the-loop stages
		if stage == "greenlight" {
			if err := w.requestGreenlight(ctx); err != nil {
				return fmt.Errorf("greenlight stage failed: %w", err)
			}
			if w.State.Greenlight != nil && !*w.State.Greenlight {
				w.State.Status = "complete"
				log.Println("User declined to proceed. Workflow complete.")
				return nil
			}
			continue
		}
		
		agent, ok := w.Agents[stage]
		if !ok {
			log.Printf("Warning: no agent registered for stage %s, skipping", stage)
			continue
		}
		
		input := w.buildInput()
		output, err := agent.Execute(ctx, input)
		if err != nil {
			w.State.Errors = append(w.State.Errors, WorkflowError{
				Stage:     stage,
				Message:   err.Error(),
				Timestamp: time.Now(),
			})
			return fmt.Errorf("stage %s failed: %w", stage, err)
		}
		
		if err := w.storeOutput(stage, output); err != nil {
			return fmt.Errorf("failed to store output for %s: %w", stage, err)
		}
		
		// Handle audit failures
		if stage == "audit" && !output.Success {
			log.Println("Audit failed, routing back for fixes...")
			// In a real implementation, this would loop back
		}
	}
	
	w.State.Status = "complete"
	return nil
}

// buildInput creates the input for the next agent.
func (w *Workflow) buildInput() AgentInput {
	return AgentInput{
		JobDescription: w.State.JobDescription,
		BaselineResume: w.State.BaselineResume,
		PriorOutputs: map[string]json.RawMessage{
			"research":      w.State.Research,
			"gap_analysis":  w.State.GapAnalysis,
			"interview":     w.State.Interview,
			"differentiator": w.State.Differentiator,
			"tailored":      w.State.Tailored,
			"ats_optimized": w.State.ATSOptimized,
		},
	}
}

// storeOutput saves agent output to state.
func (w *Workflow) storeOutput(stage string, output AgentOutput) error {
	switch stage {
	case "research":
		w.State.Research = output.Data
	case "gap_analysis":
		w.State.GapAnalysis = output.Data
	case "interview":
		w.State.Interview = output.Data
	case "differentiator":
		w.State.Differentiator = output.Data
	case "tailoring":
		w.State.Tailored = output.Data
	case "ats_optimizer":
		w.State.ATSOptimized = output.Data
	case "audit":
		w.State.Audit = output.Data
	}
	return nil
}

// requestGreenlight prompts user for approval to proceed.
func (w *Workflow) requestGreenlight(ctx context.Context) error {
	// In a real implementation, this would:
	// 1. Present the gap analysis summary to the user
	// 2. Wait for user input
	// 3. Store the decision
	
	// For now, we just log and auto-proceed
	log.Println("Greenlight stage: presenting analysis to user...")
	log.Println("(In production, this would wait for user input)")
	
	proceed := true
	w.State.Greenlight = &proceed
	return nil
}

// generateID creates a unique workflow ID.
func generateID() string {
	return fmt.Sprintf("wf-%d", time.Now().UnixNano())
}

// Example agent implementation
type GapAnalyzer struct {
	llm    LLMClient
	prompt string
}

func NewGapAnalyzer(llm LLMClient, promptPath string) (*GapAnalyzer, error) {
	prompt, err := os.ReadFile(promptPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read prompt: %w", err)
	}
	return &GapAnalyzer{llm: llm, prompt: string(prompt)}, nil
}

func (g *GapAnalyzer) Name() string { return "gap_analysis" }

func (g *GapAnalyzer) Execute(ctx context.Context, input AgentInput) (AgentOutput, error) {
	userPrompt := fmt.Sprintf(`
Job Description:
%s

Candidate Resume:
%s

Analyze the gap between requirements and experience. Output YAML.
`, input.JobDescription, input.BaselineResume)

	response, err := g.llm.Complete(ctx, g.prompt, userPrompt)
	if err != nil {
		return AgentOutput{}, fmt.Errorf("LLM call failed: %w", err)
	}
	
	return AgentOutput{
		AgentName:  g.Name(),
		Timestamp:  time.Now(),
		Success:    true,
		Data:       json.RawMessage(response),
		Confidence: 0.85,
	}, nil
}

// Main entry point (example usage)
func main() {
	log.Println("Composable Me Hydra - Job Search Orchestrator")
	log.Println("This is a skeleton. Wire up your LLM client to make it work.")
	
	// Example:
	// llm := NewClaudeClient(os.Getenv("ANTHROPIC_API_KEY"))
	// wf := NewWorkflow(llm)
	// 
	// gapAnalyzer, _ := NewGapAnalyzer(llm, "agents/gap-analyzer/prompt.md")
	// wf.RegisterAgent(gapAnalyzer)
	// 
	// err := wf.Run(context.Background(), jobDescription, resume)
	// if err != nil {
	//     log.Fatal(err)
	// }
}
