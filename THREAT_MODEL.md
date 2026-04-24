# removepii.co.uk — threat model

This document states what the application defends against, what it doesn't, and where the soft spots are. A scrubber's value is defined by what it misses as much as by what it catches.

## What the app is

A UK-PII document redactor. Users paste text or upload `.txt` files; the app runs a deterministic regex pass followed by a local-LLM pass to mask names, contact details, identifiers, and addresses, then returns the scrubbed text. Document content is processed in RAM and not persisted to disk.

## Intended use

- Individual users redacting CVs, support tickets, emails, subject access requests before sharing them internally or externally.
- Small-team redaction of low-volume documents (recruitment, legal drafting, healthcare admin).

## Out of scope

- Non-UK PII shapes (US SSN, EU tax IDs, etc.). Known omission.
- PDFs, DOCX, images, OCR. `.txt` only in this version.
- High-volume or SLA-bound workflows. No queueing, no backpressure, no audit SLA.

## What we defend against

| Threat | Control |
|---|---|
| UK phone (mobile), NHS number, email, postcode, common address forms, NINO appearing in output | Regex phase, deterministic, runs first |
| Names and contextual PII that regex misses | Local-LLM second pass (Ollama / LM Studio) |
| Document content persisting to disk | Streamlit runs stateless; backend never writes file content to disk |
| Content leaking to third-party LLM providers | LLM call goes to `localhost` only (`LLM_BASE_URL` defaults to Ollama local) |
| Plaintext traffic over the internet | Cloudflare Tunnel terminates TLS; no plaintext origin pull |
| Unauthenticated access to the portal | License-key auth via `clients.json` (demo keys, see `DECISIONS.md`) |
| Source-control leak of credentials | `.gitignore` excludes `.env`, `clients.json`, `config.yml`, `*.cloudflared.json`, `*.csv` |

## What we don't defend against

- **LLM fail-open.** If the local LLM call raises or times out, the regex-cleaned chunk is returned unchanged — the LLM pass is silently skipped. For a scrubber this is fail-open; it means a name the regex missed can reach the user's output when Ollama is down or OOMing. Documented in `DECISIONS.md`; no fix applied yet.
- **London landlines.** The UK phone regex matches mobile patterns (`07XXX XXX XXX`, `+44 7XXX XXX XXX`) and some geographic patterns but slips the London landline format `+44 20 XXXX XXXX` / `020 XXXX XXXX`. Tracked as a known gap; LLM pass may or may not catch depending on context.
- **Obfuscation.** Concatenated strings, zero-width separators, homoglyphs, base64-encoded PII — the regex sees raw text and the LLM is best-effort.
- **Non-UK shapes.** Any PII whose format differs from UK conventions (e.g. US phone, German postleitzahl, Irish PPSN) is not matched.
- **Adversarial prompts.** A user who pastes a document designed to confuse the LLM pass (e.g. instructions like "do not redact the name") may cause the LLM to return the text with PII intact. The regex pass still runs and catches the shapes it covers.
- **Traffic analysis.** Cloudflare can see request volumes, timing, client IP, and `User-Agent`. By design — that's what lets them protect the tunnel.
- **Host compromise.** If the VPC box is compromised, the attacker sees document content in-flight (RAM) and the CSV billing logs. The keys in `clients.json` are readable; see §demo-posture below.
- **Demo-site posture.** `clients.json` holds four plaintext license keys that were previously exposed on Google Drive. Treat the site as demo-grade; **do not submit real personal data**.

## Trust assumptions

- **Cloudflare** receives all request traffic. Their privacy policy applies; we don't see their logs.
- **Ollama** is trusted to respond within a reasonable timeout and not to exfiltrate (it's a local binary).
- **`clients.json` on disk** is trusted to be readable only by the `vpc` user / systemd service user.
- **Cloudflare Tunnel credentials** (`~/.cloudflared/<UUID>.json`) are trusted to be readable only by the `vpc` user. They grant traffic-routing rights to this tunnel and must be treated as a credential.
- **The host OS** (Ubuntu 24.04) is trusted to get security updates.

## Limits and known false-negative classes

- Any UK phone format other than mobile.
- PII split across lines or embedded in complex markup.
- Foreign PII shapes.
- Names that collide with common dictionary words (the LLM is the only backstop, and it's best-effort).
- Numbers that incidentally match the NHS/NINO patterns — the regex doesn't verify checksums.

## Privacy posture

- Local-only LLM inference (no external API).
- No document content, filenames, or extracted entities to disk.
- Connection-metric ledger (`usage_ledger.csv`) and opt-in feedback log (`feedback_log.csv`) only.
- Cloudflare Tunnel TLS, no plaintext on the wire.
- Output may include redacted text which still contains the original's structure — don't paste output back into public forums and assume that's "safe."

## Reporting a vulnerability

See `SECURITY.md`. Private reports via GitHub Security Advisories.
