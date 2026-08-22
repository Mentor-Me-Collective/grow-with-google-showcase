# Security Audit: Dependency Vulnerability Scan

**Date:** August 2026

**Performed by:** Ashenafi Mekonnen Demssie (Cybersecurity Track)

**Tool used:** [pip-audit](https://pypi.org/project/pip-audit/)

## Summary

Ran `pip-audit` against `backend/requirements.txt` and found 7 known
vulnerabilities across 3 packages.

## Findings

| Package | Version | Vulnerability ID | Fix Version |
|---|---|---|---|
| flask | 3.0.3 | PYSEC-2026-2151 | 3.1.3 |
| flask-cors | 4.0.1 | PYSEC-2024-71 | 4.0.2 |
| flask-cors | 4.0.1 | PYSEC-2024-260 | 4.0.2 |
| flask-cors | 4.0.1 | PYSEC-2026-1383 | 6.0.0 |
| flask-cors | 4.0.1 | PYSEC-2026-1384 | 6.0.0 |
| flask-cors | 4.0.1 | PYSEC-2026-1385 | 6.0.0 |
| python-dotenv | 1.0.1 | PYSEC-2026-2270 | 1.2.2 |

## Fix Applied

Upgraded all three packages in `requirements.txt` to their patched versions:
- flask: 3.0.3 → 3.1.3
- flask-cors: 4.0.1 → 6.0.0
- python-dotenv: 1.0.1 → 1.2.2

## Automation Added

Added `.github/workflows/security-check.yml`, which automatically runs
`pip-audit` and a secret scanner (`gitleaks`) on every future push and
pull request, so dependency vulnerabilities are caught continuously
rather than checked manually.

## Additional Checks Performed

- Manually reviewed the codebase for hardcoded secrets/API keys, none found
- Confirmed `.env` files are properly excluded via `.gitignore`
- Confirmed only safe `.env.example` placeholder files are committed
