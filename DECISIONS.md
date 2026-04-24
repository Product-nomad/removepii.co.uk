# Decisions

One paragraph per material decision, newest on top. Per §11 of `~/WAYS_OF_WORKING.md`.

## 2026-04-24 — Reinstate the four demo license keys despite prior exposure

The four original license keys (`RedactMe2026`, `recruit-101`, `law-firm-x`, `simon-admin`) were visible in the original source file on Google Drive with broad share settings and must be treated as public. They have been reinstated in `clients.json` (gitignored) at the operator's explicit request because this runs as a **demo site with no production data** — anyone guessing the keys can only see the UI and submit text they already have. *Reinstatement conditions:* none; this stands until the product takes real client data. *Rotation trigger:* first real client signs up → generate fresh keys per client, retire the four demo keys, remove/replace them in `clients.json`. *Recorded because:* the keys are structurally compromised; if someone reports unauthorised access the answer is "yes, by design" not "how did they get in."

## 2026-04-24 — LLM failure falls back to regex-only output (fail-open for now)

`backend.scrub_text_hybrid` wraps each LLM chunk call in `try/except`; on any exception (Ollama down, model missing, timeout, malformed response) it appends the *regex-cleaned* chunk and continues. For a redaction tool this is **fail-open** — the LLM was meant to catch names and contextual PII the regex misses, and on failure that second pass is silently skipped. *Why kept for now:* behaviour-preserving with the pre-migration Windows version; changing semantics without the operator's explicit buy-in would be scope creep on a "re-live the site" task. *To revisit:* decide between three alternatives — (a) display a visible warning banner when LLM fell back, (b) fail the request with a user-facing error, (c) replace unverified text with a blanket `[UNVERIFIED]` tag. Track decision here once made.

## 2026-04-24 — Ollama over LM Studio for the local LLM

Original Windows build ran LM Studio's OpenAI-compatible server on port 1234. On Linux the equivalent choice was [Ollama](https://ollama.com/) — headless, CLI-native, ships with a `systemd` service, well-suited to running under the same init system as the rest of the stack. Both expose the same OpenAI-compatible API shape, so the client code is unchanged; `LLM_BASE_URL` and `LLM_MODEL` env vars let operators swap back to LM Studio if preferred. Default model chosen: `llama3.2:3b` — small (~2 GB), fast, adequate for the redaction task; easy to swap to a larger model without code changes.

## 2026-04-24 — Cloudflare Tunnel, not port-forwarding or a reverse-proxy

The host is behind a domestic UK broadband NAT. Opening ports 80/443 on the router would expose the home network, require dynamic DNS, and break on ISP IP rotation. Cloudflare Tunnel (already used on the prior Windows host) keeps all of that inverted: `cloudflared` initiates outbound connections to Cloudflare edge, Cloudflare terminates TLS and proxies user traffic back over those connections. *What we get:* no public IP on the host, automatic TLS, DNS management via the Cloudflare dashboard, DDoS protection at the edge, multi-PoP HA for the tunnel itself (4 QUIC connections to London edge). *What we don't need:* nginx, caddy, Let's Encrypt, UFW exceptions. *Cost:* £0 — free tier is sufficient for this traffic volume.

## 2026-04-24 — Billing logs live as CSVs in the working directory

`backend.py` writes two plain CSVs — `usage_ledger.csv` (one row per redaction job: timestamp, client ID, action type, character count) and `feedback_log.csv` (one row per opt-in feedback form submission). *Why local CSVs:* trivially grep-able / importable into Excel / adequate for <100 jobs/day. *What never gets written:* document content, filenames, extracted PII entities. *Known limit:* unbounded growth — no rotation. Will move to dated daily files or a lightweight SQLite once traffic justifies it.

## 2026-04-24 — Client DB in JSON on disk, not hashed, not a database

`clients.json` is a plain JSON map of license key → client name, read by `frontend.py` at startup. Not hashed, not behind a DB, no expiry, no per-user rate limits. *Why kept simple:* demo site with ~4 users; a full auth system would be disproportionate. *Upgrade path when real clients onboard:* bcrypt-hashed keys, per-key rate limiting, expiry dates, audit log of authentications. This is intentionally deferred until the product graduates from demo.
