# Security policy

RemovePII is a privacy-focused tool. Its own supply chain and operational security matter more than for a typical project.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting: <https://github.com/Product-nomad/removepii.co.uk/security/advisories/new>.

Do not open a public issue or PR containing an exploit payload.

## What counts as a vulnerability

In scope:

- A PII pattern that's clearly in scope (UK phone / NHS / email / postcode / address / NINO) slipping through both regex and LLM phases on realistic input.
- Session-state leakage between authenticated users.
- Document content appearing in `usage_ledger.csv` or anywhere on disk.
- A way to bypass license-key authentication.
- Credentials or secrets exposed in logs, error messages, or the client bundle.

Out of scope (documented limits):

- Obfuscated PII the regex + local LLM miss on adversarial input — known long tail.
- Non-UK PII shapes (planned, not implemented).
- Denial-of-service of the local LLM (best-effort only).

## Response timeline

- Acknowledgement within 3 working days.
- Triage within 10 working days.
- Fix within 30 days for critical / 60 days for high / 90 days for others.
- Coordinated disclosure once a fix is released. Credit in the advisory unless you ask not to.

## Safe harbour

Good-faith research against the site itself is welcomed — please stay within the constraints of the UK Computer Misuse Act and avoid touching any data that isn't yours. Don't probe third-party integrations (Cloudflare, Ollama infrastructure, etc.) as part of this programme.
