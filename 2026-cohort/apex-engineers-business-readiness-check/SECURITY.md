# Security and Privacy

## Current Data Handling

The Business Readiness Check does not require an account or database. The
application processes answers in the active Streamlit session and does not
intentionally save them after the session ends.

Users must not enter passwords, payment-card details, customer records,
financial account information, or other sensitive information. The optional
business name is limited to 80 characters, normalized before report generation,
and can be left blank.

## Implemented Safeguards

- Diagnostic responses use fixed answer choices.
- Every question must be answered before scoring.
- Unknown, missing, and invalid answers are rejected by the scoring module.
- Optional report text is normalized and length-limited.
- The application does not use file uploads, external APIs, authentication, or
  a database.
- Reports are generated as plain text.
- Error details and private answers are not intentionally written to logs.
- Streamlit secrets, environment files, caches, and logs are excluded from Git.
- The user interface includes a privacy notice and results disclaimer.
- The generated modernization plan includes general checkpoints for
  multifactor authentication, least-privilege access, backups, controlled
  testing, data export, deletion, and incident support.

## Deployment and Release Safeguards

For the public deployment and later releases:

- Use an HTTPS-enabled hosting provider.
- Deploy only from the intended GitHub repository and branch.
- Confirm that no secrets or private files are committed.
- Install dependencies from `requirements.txt` and review dependency warnings.
- Confirm the deployed application does not retain answers after the session.
- Repeat the complete assessment and report-download checks in the deployed
  environment.

## Limitations

This is an educational readiness tool. It is not a penetration test, formal
security assessment, compliance review, financial audit, or guarantee that a
business is secure. The security checkpoints are general project guidance, not
a NIST assessment or validated control framework. All recommendations must be
evaluated for the business's actual systems, risks, budget, and legal
obligations.

## Reporting a Problem

Do not submit confidential business information in a public GitHub issue. Use
the repository's private maintainer contact method if one is added. Until then,
describe only non-sensitive reproduction steps in the pull-request discussion.
