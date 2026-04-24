# removepii.co.uk

[![CI](https://github.com/Product-nomad/removepii.co.uk/actions/workflows/ci.yml/badge.svg)](https://github.com/Product-nomad/removepii.co.uk/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python: ≥3.12](https://img.shields.io/badge/python-%E2%89%A53.12-green.svg)](./pyproject.toml)

**GDPR-grade UK document redactor with a zero-persistence architecture for document content.** Paste text or upload a `.txt` file, get it back with UK PII (phones, NHS numbers, emails, postcodes, addresses, National Insurance numbers, names) redacted — processed in-memory, never written to disk.

Live at <https://removepii.co.uk>.

> v0.1 — demo site. Four demo license keys in `clients.json`; do **not** submit real personal data.
> **CPMAI phase VI — Operationalization** (Phase V debt: no golden-set accuracy metric yet, no LLM eval). See [Governance](#governance) below.

## Architecture

```
User → Cloudflare Tunnel → Streamlit frontend (:8501) → backend.scrub_text_hybrid
                                                            │
                                                            ├─ regex phase (UK PII patterns)
                                                            └─ local LLM phase (Ollama, OpenAI-compatible)
```

Two-phase pipeline: deterministic regex catches the obvious cases, a local LLM (Ollama by default, LM Studio supported) catches contextual entities the regex misses. No document content leaves the host.

## What is and isn't logged

Per the Privacy Policy (`pages/Privacy_Policy.py`):

- **We log (for billing + stability)**: timestamp, client ID, action type, document character count — `usage_ledger.csv`. No document content.
- **We log (on user action)**: feedback form submissions — `feedback_log.csv`. Only what the user pastes into the feedback form.
- **We never log**: document content, filenames, extracted PII entities, or any field derived from the payload.

## Local development

### Prerequisites

- Python 3.12+ (tested on 3.12.3)
- [Ollama](https://ollama.com/) or [LM Studio](https://lmstudio.ai/) running locally (for the LLM phase — regex phase works without)
- A clients JSON file at `clients.json` (see `clients.json.example`)

### Setup

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env                 # edit if your Ollama/LM Studio isn't on defaults
cp clients.json.example clients.json # edit to add your own license keys

# Pull a small model (one-time)
ollama pull llama3.2:3b
```

### Run

```sh
streamlit run frontend.py --server.port 8501
```

Open <http://localhost:8501>, log in with any key from your `clients.json`.

### Tests

```sh
pip install pytest
pytest tests/
```

The test suite mocks the LLM call, so it runs offline; it covers the regex pipeline (email, phone, postcode, NHS number, NINO, address, style modes).

## Deployment (Cloudflare Tunnel)

The live site exposes two services via Cloudflare Tunnel — no public IP, no port forwarding, automatic TLS.

| Hostname | Port | Service |
|---|---|---|
| `removepii.co.uk` + `www.removepii.co.uk` | 8501 | Streamlit frontend |
| `api.removepii.co.uk` | 8000 | API backend (separate service — not in this repo) |

### 1. Install cloudflared on the host

```sh
# Debian/Ubuntu
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb \
  -o /tmp/cloudflared.deb
sudo dpkg -i /tmp/cloudflared.deb
```

### 2. Authenticate and create a tunnel

```sh
cloudflared tunnel login
cloudflared tunnel create removepii
cloudflared tunnel route dns removepii removepii.co.uk
cloudflared tunnel route dns removepii www.removepii.co.uk
```

### 3. Configure ingress

Copy `config/config.yml.example` to `~/.cloudflared/config.yml`, fill in your tunnel UUID and the path to the credentials JSON `cloudflared` created. **Never commit the real `config.yml`.**

### 4. Install Ollama + pull a model

```sh
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b
```

The `install.sh` script installs and starts a systemd service automatically.

### 5. Run as systemd services

See `systemd/` for `removepii-streamlit.service` and `removepii-tunnel.service`. Enable with:

```sh
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now removepii-streamlit removepii-tunnel
```

## Project layout

```
removepii/
├── frontend.py                 Streamlit UI (home page)
├── backend.py                  Hybrid regex + LLM scrubber
├── pages/
│   └── Privacy_Policy.py       Auto-discovered by Streamlit
├── tests/
│   └── test_backend.py         Regex-phase smoke tests (LLM mocked)
├── assets/
│   ├── piiremoval.png          Infographic
│   └── architecture.png        Architecture diagram
├── config/
│   └── config.yml.example      Cloudflare Tunnel template
├── clients.json.example        License-key DB template
├── .env.example                Env-var template
├── requirements.txt
└── README.md
```

## Security

See `SECURITY.md` for how to report a vulnerability and `THREAT_MODEL.md` for what the tool defends against and what it doesn't.

## Governance

This project follows the working principles at [`~/WAYS_OF_WORKING.md`](../../WAYS_OF_WORKING.md) and the PMI CPMAI methodology.

### CPMAI phase: VI (Operationalization, with Phase V debt)

| Phase | Status | Artefact |
|---|---|---|
| I. Business Understanding | ✅ complete | `THREAT_MODEL.md`, this README |
| II. Data Understanding | ✅ complete | UK PII taxonomy documented in `backend.py` |
| III. Data Preparation | ✅ complete | `UK_PATTERNS` regex table |
| IV. Model Development | ✅ complete | Hybrid regex + local-LLM pipeline |
| V. Model Evaluation | 🟡 partial | 7 regex unit tests (LLM mocked); **no golden-set accuracy measurement** |
| VI. Model Operationalization | ✅ live | Cloudflare Tunnel + systemd on home VPC; auto-restart; 4 redundant edge connections |

### Value metrics (next to measure)

1. **Precision on a planted golden set** — detects ≥ 95% of the seeded PII entities. Current: unmeasured.
2. **Uptime** — ≥ 99% monthly, measured from Cloudflare analytics. Current: live since 2026-04-24.
3. **Redaction latency p95** — ≤ 5s for a 1-page CV. Current: unmeasured.

### Ethical posture

- Privacy-by-default: local LLM, no external API, document content never on disk.
- Transparency: OSS under MIT, `THREAT_MODEL.md` explicitly lists known gaps.
- Data minimisation: connection metrics only; feedback is opt-in.
- Honest claims: Privacy Policy (`pages/Privacy_Policy.py`) acknowledges the metric ledger rather than claiming "zero disk writes."

### Known gaps

- London landline phone regex gap — see `THREAT_MODEL.md`.
- LLM fail-open on errors — see `DECISIONS.md`.
- API subdomain (`api.removepii.co.uk`) not live.

### Drift monitoring (planned)

- Weekly run against a frozen golden set; alert on precision drop.
- Alert if PII patterns matched per 1k characters deviates > 3σ from baseline.

## Roadmap

- Add a golden red-team fixture set and measure detection accuracy.
- Fix the London-landline regex gap.
- Decide LLM fail-open policy (see `DECISIONS.md`) and implement.
- PDF / DOCX support.
- Restore the API subdomain.
- Hash license keys and add per-client expiry when leaving demo posture.

## License

MIT.
