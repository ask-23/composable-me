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

// getRepoRoot finds the repository root by looking for .git/ or requirements.txt
func getRepoRoot() (string, error) {
	wd, err := os.Getwd()
	if err != nil {
		return "", err
	}

	// Search upward through parent directories
	current := wd
	for {
		// Check for .git directory or requirements.txt file
		if _, err := os.Stat(filepath.Join(current, ".git")); err == nil {
			return current, nil
		}
		if _, err := os.Stat(filepath.Join(current, "requirements.txt")); err == nil {
			return current, nil
		}

		parent := filepath.Dir(current)
		if parent == current {
			// Reached filesystem root
			break
		}
		current = parent
	}

	return "", fmt.Errorf("could not find repository root (looking for .git/ or requirements.txt)")
}

// validateRepoStructure checks for expected directories and warns if missing
func validateRepoStructure(repoRoot string) {
	expectedDirs := []string{"inputs", "examples"}
	var missingDirs []string

	for _, dir := range expectedDirs {
		if _, err := os.Stat(filepath.Join(repoRoot, dir)); os.IsNotExist(err) {
			missingDirs = append(missingDirs, dir)
		}
	}

	if len(missingDirs) > 0 {
		fmt.Printf("⚠️  Warning: Expected directories not found: %s\n", strings.Join(missingDirs, ", "))
		fmt.Printf("   Repository root: %s\n", repoRoot)
	}
}

func main() {
	fmt.Println("Composable Me Hydra - Interactive CLI")
	fmt.Println("=====================================")

	config := &Config{
		OutPath: "output/",
	}

	// Detect and change to repository root directory
	repoRoot, err := getRepoRoot()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error finding repository root: %v\n", err)
		os.Exit(1)
	}

	if err := os.Chdir(repoRoot); err != nil {
		fmt.Fprintf(os.Stderr, "Error changing to repository root: %v\n", err)
		os.Exit(1)
	}

	validateRepoStructure(repoRoot)

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

	// Default sources to same directory as JD file if not specified
	if config.SourcesPath == "" {
		if config.JDPath != "" {
			config.SourcesPath = filepath.Dir(config.JDPath)
			fmt.Printf("ℹ️  No --sources specified, defaulting to: %s\n", config.SourcesPath)
		} else {
			fmt.Print("Enter path to sources directory: ")
			config.SourcesPath, _ = reader.ReadString('\n')
			config.SourcesPath = strings.TrimSpace(config.SourcesPath)
		}
	}

	// Paths are now relative to repo root (we already changed to repo root)
	// No need to adjust paths unless they're absolute

	// Validate that all input paths exist
	if _, err := os.Stat(config.JDPath); os.IsNotExist(err) {
		fmt.Fprintf(os.Stderr, "Job description file not found: %s\n", config.JDPath)
		os.Exit(1)
	}

	if _, err := os.Stat(config.ResumePath); os.IsNotExist(err) {
		fmt.Fprintf(os.Stderr, "Resume file not found: %s\n", config.ResumePath)
		os.Exit(1)
	}

	if _, err := os.Stat(config.SourcesPath); os.IsNotExist(err) {
		fmt.Fprintf(os.Stderr, "Sources directory not found: %s\n", config.SourcesPath)
		os.Exit(1)
	}

	// Validate that sources path is a directory
	if info, err := os.Stat(config.SourcesPath); err == nil && !info.IsDir() {
		fmt.Fprintf(os.Stderr, "Sources path must be a directory: %s\n", config.SourcesPath)
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
				config.Model = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
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

	// Create virtual environment if needed (now in repo root)
	if _, err := os.Stat(".venv"); os.IsNotExist(err) {
		fmt.Println("Creating virtual environment...")
		cmd := exec.Command("python3", "-m", "venv", ".venv")
		if err := cmd.Run(); err != nil {
			fmt.Fprintf(os.Stderr, "Error creating virtual environment: %v\n", err)
			os.Exit(1)
		}
	}

	// Activate virtual environment and install dependencies
	fmt.Println("Installing dependencies...")
	pipPath := filepath.Join(".venv", "bin", "pip")

	// Check if dependencies are already installed
	cmd := exec.Command(pipPath, "show", "crewai")
	if err := cmd.Run(); err != nil {
		// Install dependencies
		cmd = exec.Command(pipPath, "install", "-r", "requirements.txt")
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

	pythonPath := filepath.Join(".venv", "bin", "python")
	cmd = exec.Command(pythonPath, pythonArgs...)
	// We're already in repo root, so no need to change directory
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	if err := cmd.Run(); err != nil {
		fmt.Fprintf(os.Stderr, "Error running Python script: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("Hydra workflow completed successfully!")
}
