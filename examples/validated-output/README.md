# Validated Output Example

This directory contains a sanitized example of Composable Me's output flow:

1. job description input
2. source resume input
3. generated resume
4. generated cover letter
5. claim-by-claim audit report
6. execution log

The point is not to generate plausible prose. The point is to show that every output claim traces back to supplied source material or is rejected.

## Files

| File | Purpose |
| --- | --- |
| `job_description.md` | Synthetic target role based on the existing sample job description. |
| `source_resume.md` | Sanitized source resume based on the existing sample resume structure. |
| `resume.md` | Tailored resume output. |
| `cover_letter.md` | Tailored cover letter output. |
| `audit_report.yaml` | Claim-by-claim verification with rejected unsupported claims. |
| `execution_log.txt` | Canned execution trace using GMT timestamps. |

## Reading Path

Start with `source_resume.md`, then read `resume.md` and `cover_letter.md`. Use `audit_report.yaml` to verify that each concrete claim in the generated artifacts traces back to source material.
