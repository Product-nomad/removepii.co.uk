# Changelog

All notable changes recorded here. Per §11 of `~/WAYS_OF_WORKING.md`.

Format: [Keep a Changelog](https://keepachangelog.com/) · [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed
- **Names weren't being redacted on real CVs** — the default model (`llama3.2:3b`) was returning input verbatim on ≥500-char chunks, so only the regex-phase redactions survived. Upgraded the recommended model to `llama3.1:8b` (4.9 GB, still local, still no external API calls). Latency went up (~5s → ~30s per CV) but accuracy matches expectations. Documented in `DECISIONS.md`.
- **Student IDs were being mis-redacted as NHS numbers.** The NHS regex matched any bare 10-digit number. Tightened to require separators (`XXX XXX XXXX`) which is how NHS numbers are actually written in the wild. Bare 10-digit strings are now preserved.
- **Dates of birth weren't being redacted.** Added a `DOB` regex pattern matching `DOB: 14/03/1988`, `Date of Birth: 14-03-1988`, etc. Preserves other dates (employment history).

### Changed
- LLM chunk size halved from 1000 → 500 chars. Smaller chunks are easier for any local model to stay on-task. Trade-off: more LLM calls, so total latency increases ~2× per document.
- System prompt rewritten to be more prescriptive — explicit rules per PII class, "err toward redaction" guidance, explicit list of pre-existing tags to preserve.

### Added
- Regression tests for the student-ID false positive and the DOB pattern. Test count: 7 → 10.

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
