"""
Command-line interface for running the Hydra workflow end-to-end.

Usage:
    python -m runtime.crewai.cli --jd path/to/jd.md --resume path/to/resume.md \
        --sources sources/ --out output/
"""

import argparse
import os
import sys
from pathlib import Path

from runtime.crewai.artifacts import RunInputs, generate_run_id, write_run_artifacts
from runtime.crewai.hydra_workflow import HydraWorkflow, RunStatus
from runtime.crewai.llm_client import LLMClientError, get_llm_client

# Map an explicit run status to a process exit code.
EXIT_CODES = {
    RunStatus.COMPLETED: 0,
    RunStatus.COMPLETED_WITH_AUDIT_CONCERNS: 1,
    RunStatus.AUDIT_ERROR: 1,
    RunStatus.PAUSED: 1,
    RunStatus.FAILED: 2,
}


def _get_repo_root() -> Path:
    """
    Find the repository root directory by looking for .git/ or requirements.txt.

    Searches upward from the current working directory until it finds a directory
    containing either .git/ or requirements.txt, which indicates the repo root.

    Returns:
        Path: The repository root directory

    Raises:
        FileNotFoundError: If no repo root indicators are found
    """
    current = Path.cwd()

    # Search upward through parent directories
    for path in [current] + list(current.parents):
        # Check for .git directory or requirements.txt file
        if (path / ".git").exists() or (path / "requirements.txt").exists():
            return path

    # If we can't find repo root, raise an error
    raise FileNotFoundError(
        "Could not find repository root. Looking for directory containing .git/ or requirements.txt"
    )


def _validate_repo_structure(repo_root: Path) -> None:
    """
    Validate that the repository has expected directories.

    Args:
        repo_root: The repository root directory

    Raises:
        FileNotFoundError: If expected directories are missing
    """
    expected_dirs = ["inputs", "examples"]
    missing_dirs = []

    for dir_name in expected_dirs:
        if not (repo_root / dir_name).exists():
            missing_dirs.append(dir_name)

    if missing_dirs:
        print(f"⚠️  Warning: Expected directories not found: {', '.join(missing_dirs)}")
        print(f"   Repository root: {repo_root}")


def build_parser() -> argparse.ArgumentParser:
    """Create an argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        description="Composable Crew - Hydra Workflow Runner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--jd", required=True, help="Path to job description file")
    parser.add_argument("--resume", required=True, help="Path to resume file")
    parser.add_argument(
        "--sources",
        help="Path to directory containing source documents for truth verification (defaults to same directory as --jd file)",
    )
    parser.add_argument(
        "--out",
        default="output/",
        help="Directory where outputs will be written",
    )
    parser.add_argument(
        "--model",
        help="Override model name (defaults to OPENROUTER_MODEL or anthropic/claude-sonnet-4.5)",
    )
    parser.add_argument(
        "--max-audit-retries",
        type=int,
        default=2,
        help="Maximum number of audit retry attempts",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Enable interactive mode (Human-in-the-Loop) for interviews and approvals",
    )
    return parser


def _read_file(path: Path) -> str:
    """Read a text file, raising a helpful error if missing."""
    if not path.is_file():
        raise FileNotFoundError(f"Input file not found: {path}")
    return path.read_text()


def _read_sources(directory: Path) -> str:
    """Read all files in a sources directory into a single string."""
    if not directory.exists():
        raise FileNotFoundError(f"Sources directory not found: {directory}")
    if not directory.is_dir():
        raise ValueError(f"--sources must be a directory: {directory}")

    parts: list[str] = []
    for path in sorted(directory.iterdir()):
        if path.is_file():
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                print(f"Skipping non-text source file (unable to decode UTF-8): {path.name}")
                continue
            parts.append(f"# {path.name}\n{content}\n")
    if not parts:
        raise ValueError(f"No UTF-8 text source documents found in {directory}")
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint. Returns an exit code instead of exiting for testability."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Detect and change to repository root directory
    try:
        repo_root = _get_repo_root()
        os.chdir(repo_root)
        _validate_repo_structure(repo_root)
    except FileNotFoundError as err:
        parser.error(str(err))

    # Resolve paths relative to repo root
    jd_path = Path(args.jd)
    resume_path = Path(args.resume)

    # Default sources to same directory as JD file if not specified
    if args.sources:
        sources_dir = Path(args.sources)
    else:
        sources_dir = jd_path.parent
        print(f"ℹ️  No --sources specified, defaulting to: {sources_dir}")

    out_dir = Path(args.out)

    # Validate that all input paths exist
    if not jd_path.exists():
        parser.error(f"Job description file not found: {jd_path}")
    if not resume_path.exists():
        parser.error(f"Resume file not found: {resume_path}")
    if not sources_dir.exists():
        parser.error(f"Sources directory not found: {sources_dir}")
    if not sources_dir.is_dir():
        parser.error(f"Sources path must be a directory: {sources_dir}")

    try:
        jd_text = _read_file(jd_path)
        resume_text = _read_file(resume_path)
        sources_text = _read_sources(sources_dir)
    except (FileNotFoundError, ValueError) as err:
        parser.error(str(err))

    try:
        llm = get_llm_client(model=args.model)
    except LLMClientError as err:
        print(f"❌ LLM configuration error: {err}", file=sys.stderr)
        return 1

    workflow = HydraWorkflow(
        llm, max_audit_retries=args.max_audit_retries, interactive=args.interactive
    )

    print("Starting Hydra workflow...\n")
    print(f"Job description: {jd_path}")
    print(f"Resume: {resume_path}")
    print(f"Sources: {sources_dir}")
    print(f"Output directory: {out_dir}\n")

    context = {
        "job_description": jd_text,
        "resume": resume_text,
        "source_documents": sources_text,
    }

    result = workflow.execute(context)

    # Run-scoped output directory + PII-free manifest.
    run_id = generate_run_id()
    inputs = RunInputs(
        job_description_chars=len(jd_text),
        resume_chars=len(resume_text),
        sources_chars=len(sources_text),
        jd_path=str(jd_path),
        resume_path=str(resume_path),
        sources_path=str(sources_dir),
    )
    status = result.status
    # Preserve intermediate stage outputs whenever the run didn't cleanly complete.
    include_intermediate = status is not RunStatus.COMPLETED
    run_dir = write_run_artifacts(
        out_dir, result, run_id=run_id, inputs=inputs, include_intermediate=include_intermediate
    )

    exit_code = EXIT_CODES.get(status, 2)
    final_status = result.audit_report.get("final_status") if result.audit_report else None

    if status is RunStatus.COMPLETED:
        print(f"✅ Success! Audit: {final_status}. Outputs → {run_dir}")
    elif status is RunStatus.COMPLETED_WITH_AUDIT_CONCERNS:
        print(f"⚠️  Documents generated but audit rejected: {result.audit_error}")
        print(f"   Outputs → {run_dir} — review audit_report.yaml before sending.")
    elif status is RunStatus.AUDIT_ERROR:
        print(f"⚠️  Documents generated but the audit stage errored: {result.audit_error}")
        print(f"   Outputs → {run_dir} — MANUAL REVIEW REQUIRED.")
    elif status is RunStatus.PAUSED:
        print(f"⏸  Run paused awaiting input: {result.error_message}")
        print("   Re-run with --interactive to answer inline. Partial results →", run_dir)
    else:  # FAILED
        print(f"❌ Workflow failed: {result.error_message}", file=sys.stderr)
        print(f"   Partial results → {run_dir}", file=sys.stderr)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
