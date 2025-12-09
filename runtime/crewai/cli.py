"""
Command-line interface for running the Hydra workflow end-to-end.

Usage:
    python -m runtime.crewai.cli --jd path/to/jd.md --resume path/to/resume.md \
        --sources sources/ --out output/
"""

import argparse
import sys
from pathlib import Path
from typing import Iterable

import yaml

from runtime.crewai.hydra_workflow import HydraWorkflow
from runtime.crewai.llm_client import get_llm_client, LLMClientError


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
        required=True,
        help="Path to directory containing source documents for truth verification",
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


def _write_output_files(out_dir: Path, result) -> None:
    """Write workflow outputs to disk."""
    out_dir.mkdir(parents=True, exist_ok=True)

    final_docs = result.final_documents or {}
    (out_dir / "resume.md").write_text(final_docs.get("resume", ""))
    (out_dir / "cover_letter.md").write_text(final_docs.get("cover_letter", ""))

    audit_report = result.audit_report or {}
    (out_dir / "audit_report.yaml").write_text(yaml.safe_dump(audit_report, sort_keys=False))

    log_lines = result.execution_log or []
    if isinstance(log_lines, Iterable):
        (out_dir / "execution_log.txt").write_text("\n".join(log_lines))


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint. Returns an exit code instead of exiting for testability."""
    parser = build_parser()
    args = parser.parse_args(argv)

    jd_path = Path(args.jd)
    resume_path = Path(args.resume)
    sources_dir = Path(args.sources)
    out_dir = Path(args.out)

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

    workflow = HydraWorkflow(llm, max_audit_retries=args.max_audit_retries)

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

    if result.success:
        _write_output_files(out_dir, result)
        final_status = result.audit_report.get("final_status") if result.audit_report else "UNKNOWN"
        print(f"✅ Success! Audit status: {final_status}. Outputs saved to {out_dir}")
        return 0

    print(f"❌ Workflow failed: {result.error_message}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
