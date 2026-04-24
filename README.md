# removepii.co.uk

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

**GDPR-grade document redactor with a zero-persistence architecture for document content.** Paste text or upload a `.txt` file, get it back with UK PII (phones, NHS numbers, emails, postcodes, addresses, National Insurance numbers, names) redacted — processed in-memory, never written to disk.

Live at <https://removepii.co.uk>.

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

See `SECURITY.md` for how to report a vulnerability.

## License

MIT.
