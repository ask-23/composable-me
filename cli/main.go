package main

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// Config holds the application configuration
type Config struct {
	JDPath      string
	ResumePath  string
	SourcesPath string
	OutPath     string
	Model       string
	Verbose     bool
}

func main() {
	fmt.Println("Composable Me Hydra - Interactive CLI")
	fmt.Println("=====================================")

	config := &Config{
		OutPath: "output/",
	}

	// Get current working directory
	wd, err := os.Getwd()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error getting current directory: %v\n", err)
		os.Exit(1)
	}

	// Parse command line arguments
	args := os.Args[1:]
	for i := 0; i < len(args); i++ {
		arg := args[i]
		switch arg {
		case "--jd":
			if i+1 < len(args) {
				config.JDPath = args[i+1]
				i++
			}
		case "--resume":
			if i+1 < len(args) {
				config.ResumePath = args[i+1]
				i++
			}
		case "--sources":
			if i+1 < len(args) {
				config.SourcesPath = args[i+1]
				i++
			}
		case "--out":
			if i+1 < len(args) {
				config.OutPath = args[i+1]
				i++
			}
		case "--model":
			if i+1 < len(args) {
				config.Model = args[i+1]
				i++
			}
		case "--verbose":
			config.Verbose = true
		}
	}

	// Interactive prompts for missing arguments
	reader := bufio.NewReader(os.Stdin)

	if config.JDPath == "" {
		fmt.Print("Enter path to job description file: ")
		config.JDPath, _ = reader.ReadString('\n')
		config.JDPath = strings.TrimSpace(config.JDPath)
	}

	if config.ResumePath == "" {
		fmt.Print("Enter path to resume file: ")
		config.ResumePath, _ = reader.ReadString('\n')
		config.ResumePath = strings.TrimSpace(config.ResumePath)
	}

	if config.SourcesPath == "" {
		fmt.Print("Enter path to sources directory: ")
		config.SourcesPath, _ = reader.ReadString('\n')
		config.SourcesPath = strings.TrimSpace(config.SourcesPath)
	}

	// Validate paths
	if !filepath.IsAbs(config.JDPath) {
		config.JDPath = filepath.Join(wd, config.JDPath)
	}
	if !filepath.IsAbs(config.ResumePath) {
		config.ResumePath = filepath.Join(wd, config.ResumePath)
	}
	if !filepath.IsAbs(config.SourcesPath) {
		config.SourcesPath = filepath.Join(wd, config.SourcesPath)
	}
	if !filepath.IsAbs(config.OutPath) {
		config.OutPath = filepath.Join(wd, config.OutPath)
	}

	// Check if files/directories exist
	if _, err := os.Stat(config.JDPath); os.IsNotExist(err) {
		fmt.Fprintf(os.Stderr, "Job description file does not exist: %s\n", config.JDPath)
		os.Exit(1)
	}

	if _, err := os.Stat(config.ResumePath); os.IsNotExist(err) {
		fmt.Fprintf(os.Stderr, "Resume file does not exist: %s\n", config.ResumePath)
		os.Exit(1)
	}

	if _, err := os.Stat(config.SourcesPath); os.IsNotExist(err) {
		fmt.Fprintf(os.Stderr, "Sources directory does not exist: %s\n", config.SourcesPath)
		os.Exit(1)
	}

	// Check for API keys
	togetherAPIKey := os.Getenv("TOGETHER_API_KEY")
	chutesAPIKey := os.Getenv("CHUTES_API_KEY")
	openrouterAPIKey := os.Getenv("OPENROUTER_API_KEY")

	if togetherAPIKey == "" && chutesAPIKey == "" && openrouterAPIKey == "" {
		fmt.Print("Enter your API key (TOGETHER_API_KEY, CHUTES_API_KEY, or OPENROUTER_API_KEY): ")
		apiKey, _ := reader.ReadString('\n')
		apiKey = strings.TrimSpace(apiKey)

		fmt.Print("Which provider is this key for? (together/chutes/openrouter): ")
		provider, _ := reader.ReadString('\n')
		provider = strings.TrimSpace(strings.ToLower(provider))

		switch provider {
		case "together":
			os.Setenv("TOGETHER_API_KEY", apiKey)
		case "chutes":
			os.Setenv("CHUTES_API_KEY", apiKey)
		case "openrouter":
			os.Setenv("OPENROUTER_API_KEY", apiKey)
		default:
			fmt.Fprintf(os.Stderr, "Invalid provider: %s\n", provider)
			os.Exit(1)
		}
	}

	// Set model if not provided
	if config.Model == "" {
		if togetherAPIKey != "" {
			config.Model = os.Getenv("TOGETHER_MODEL")
			if config.Model == "" {
				config.Model = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
			}
		} else if chutesAPIKey != "" {
			config.Model = os.Getenv("CHUTES_MODEL")
			if config.Model == "" {
				config.Model = "deepseek-ai/DeepSeek-V3.1"
			}
		} else if openrouterAPIKey != "" {
			config.Model = os.Getenv("OPENROUTER_MODEL")
			if config.Model == "" {
				config.Model = "anthropic/claude-sonnet-4.5"
			}
		}
	}

	// Create virtual environment if needed
	if _, err := os.Stat(filepath.Join(wd, ".venv")); os.IsNotExist(err) {
		fmt.Println("Creating virtual environment...")
		cmd := exec.Command("python3", "-m", "venv", ".venv")
		cmd.Dir = wd
		if err := cmd.Run(); err != nil {
			fmt.Fprintf(os.Stderr, "Error creating virtual environment: %v\n", err)
			os.Exit(1)
		}
	}

	// Activate virtual environment and install dependencies
	fmt.Println("Installing dependencies...")
	pipPath := filepath.Join(wd, ".venv", "bin", "pip")

	// Check if dependencies are already installed
	cmd := exec.Command(pipPath, "show", "crewai")
	if err := cmd.Run(); err != nil {
		// Install dependencies
		cmd = exec.Command(pipPath, "install", "-r", filepath.Join(wd, "requirements.txt"))
		cmd.Dir = wd
		if config.Verbose {
			cmd.Stdout = os.Stdout
			cmd.Stderr = os.Stderr
		}
		if err := cmd.Run(); err != nil {
			fmt.Fprintf(os.Stderr, "Error installing dependencies: %v\n", err)
			os.Exit(1)
		}
	}

	// Build arguments for Python script
	pythonArgs := []string{
		"-m", "runtime.crewai.cli",
		"--jd", config.JDPath,
		"--resume", config.ResumePath,
		"--sources", config.SourcesPath,
		"--out", config.OutPath,
	}

	if config.Model != "" {
		pythonArgs = append(pythonArgs, "--model", config.Model)
	}

	if config.Verbose {
		pythonArgs = append(pythonArgs, "--verbose")
	}

	// Execute Python script
	fmt.Println("Starting Hydra workflow...")
	fmt.Printf("Job description: %s\n", config.JDPath)
	fmt.Printf("Resume: %s\n", config.ResumePath)
	fmt.Printf("Sources: %s\n", config.SourcesPath)
	fmt.Printf("Output directory: %s\n", config.OutPath)

	pythonPath := filepath.Join(wd, ".venv", "bin", "python")
	cmd = exec.Command(pythonPath, pythonArgs...)
	cmd.Dir = wd
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if err := cmd.Run(); err != nil {
		fmt.Fprintf(os.Stderr, "Error running Python script: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("Hydra workflow completed successfully!")
}
