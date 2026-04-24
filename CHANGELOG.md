# Changelog

All notable changes recorded here. Per §11 of `~/WAYS_OF_WORKING.md`.

Format: [Keep a Changelog](https://keepachangelog.com/) · [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] — 2026-04-24

Initial public release. Migration of the existing Windows-hosted application to Linux + Cloudflare Tunnel + systemd on the home VPC box.

### Added
- Streamlit frontend (`frontend.py`) with license-key auth loaded from external JSON (`clients.json`, gitignored).
- Hybrid regex + local-LLM scrubber (`backend.py`) defaulting to Ollama's OpenAI-compatible endpoint; LM Studio-compatible via `LLM_BASE_URL` / `LLM_MODEL`.
- Six UK PII regex patterns: phone (mobile only — see gaps), NHS, email, postcode, address, NINO.
- Privacy Policy page (`pages/Privacy_Policy.py`) rewritten to match actual behaviour: document content never written to disk, but connection-metric ledger and opt-in feedback log are CSVs.
- Cloudflare Tunnel ingress template (`config/config.yml.example`).
- systemd units for Streamlit + tunnel (`systemd/`).
- Regex-phase smoke tests (7 tests, LLM mocked so they run offline).
- README, LICENSE (MIT), SECURITY.md, THREAT_MODEL.md, DECISIONS.md.

### Security
- Moved the four original license keys (`RedactMe2026`, `recruit-101`, `law-firm-x`, `simon-admin`) out of source into a gitignored `clients.json`. Keys themselves reinstated at the operator's request because this runs as a demo site with no production data (see `DECISIONS.md`); they'd need rotation before handling real client data.
- `.gitignore` excludes `.env`, `clients.json`, `config.yml`, `*.cloudflared.json`, `*.csv`, `.venv`.

### Deployed
- Live at <https://removepii.co.uk> via Cloudflare Tunnel (4 redundant QUIC connections to LHR edge PoPs).
- systemd-managed: `removepii-streamlit`, `removepii-tunnel`, `ollama` — all enabled, restart-on-failure, survive reboot.

### Known gaps
- London landline phone format (`+44 20 XXXX XXXX`) bypasses the phone regex; mobile format covered. Tracked in `THREAT_MODEL.md`.
- LLM errors fall back to regex-only output (fail-open for a scrubber). Documented in `DECISIONS.md`; product decision pending.
- No ruff/lefthook/CI yet (next commit).
- Value metrics unmeasured: PII detection accuracy on a golden set, redaction latency distribution.
- API subdomain (`api.removepii.co.uk`) not yet restored — source wasn't in the Drive folder.
