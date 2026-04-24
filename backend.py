"""RemovePII — hybrid regex + local-LLM PII scrubber.

Uses a two-phase pipeline:
1. Regex against known UK PII shapes (phone, NHS number, email, postcode, address, NINO).
2. Local LLM (Ollama / LM Studio via OpenAI-compatible API) catches names and
   context-dependent entities the regex misses.

No document content touches disk. A connection-metric ledger and optional
feedback log are written as plain CSVs for billing and support; see README.
"""

import csv
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# --- LLM client ---
# Defaults target Ollama's OpenAI-compatible endpoint; LM Studio (port 1234) works
# identically. The API key is ignored by local servers but required by the SDK.
client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
    api_key=os.getenv("LLM_API_KEY", "local"),
)
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2:3b")

USAGE_LOG = Path(os.getenv("USAGE_LEDGER_PATH", "usage_ledger.csv"))
FEEDBACK_LOG = Path(os.getenv("FEEDBACK_LOG_PATH", "feedback_log.csv"))


# --- 1. LOGGING ---
def log_usage(action_type: str, char_count: int, client_name: str) -> None:
    """Append a connection-metrics row to the usage ledger.

    Logs timestamp, client, action, and character count — never document content.
    """
    try:
        new_file = not USAGE_LOG.exists()
        with USAGE_LOG.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if new_file:
                writer.writerow(
                    ["Timestamp", "Client", "Action", "Character_Count"]
                )
            writer.writerow(
                [datetime.now(timezone.utc).isoformat(), client_name, action_type, char_count]
            )
    except Exception as e:
        print(f"Logging Error: {e}")


def log_feedback(contact: str, message: str) -> bool:
    """Append a feedback submission to the feedback log."""
    try:
        new_file = not FEEDBACK_LOG.exists()
        with FEEDBACK_LOG.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if new_file:
                writer.writerow(["Timestamp", "Contact", "Message"])
            writer.writerow([datetime.now(timezone.utc).isoformat(), contact, message])
        print(f"📝 New Feedback Logged: {message}")
        return True
    except Exception as e:
        print(f"❌ Error saving feedback: {e}")
        return False


# --- 2. PATTERNS ---
UK_PATTERNS: list[tuple[str, str]] = [
    ("PHONE", r"(?:(?:\+44\s?|0)(?:1|2|3|7)\d{2,4}[\s-]?\d{3,4}[\s-]?\d{3,4})"),
    ("NHS", r"(?<!\d)(?:\d{3}[\s-]*\d{3}[\s-]*\d{4}|\d{10})(?!\d)"),
    ("EMAIL", r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    ("POSTCODE", r"\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b"),
    (
        "ADDRESS",
        r"(?i)\b\d{1,5}[A-Za-z]?\s+(?:[A-Za-z]+\s+){1,3}(?:Street|St|Road|Rd|Lane|Ln|Avenue|Ave|Drive|Dr|Close|Cl|Square|Sq|Way|Grove|Gardens|Crescent|Mews|Park|Row)\b",
    ),
    ("NINO", r"(?i)\b[A-Z]{2}\s*\d{2}\s*\d{2}\s*\d{2}\s*[A-Z]?\b"),
]


# --- 3. HELPERS ---
def get_tag(label: str, style: str) -> str:
    if style == "Removed":
        return "[REMOVED]"
    if style == "Blank":
        return "       "
    return f"[{label}-REDACTED]"


def split_into_chunks(text: str, max_chars: int = 1000) -> list[str]:
    paragraphs = text.split("\n")
    chunks: list[str] = []
    current_chunk = ""
    for para in paragraphs:
        if len(current_chunk) + len(para) < max_chars:
            current_chunk += para + "\n"
        else:
            chunks.append(current_chunk)
            current_chunk = para + "\n"
    if current_chunk:
        chunks.append(current_chunk)
    return chunks


# --- 4. MAIN LOGIC ---
def scrub_text_hybrid(
    text: str,
    client_name: str = "Unknown",
    redaction_style: str = "Redacted",
) -> str:
    """Scrub UK PII from `text` using regex + local-LLM pipeline.

    Regex is the reliable first pass. The LLM is best-effort — on failure or a
    suspiciously short response, the chunk is passed through unchanged.
    """
    log_usage("Redaction_Job", len(text), client_name)

    # PHASE 1: Regex
    for label, pattern in UK_PATTERNS:
        tag = get_tag(label, redaction_style)
        text = re.sub(pattern, tag, text)

    # PHASE 2: LLM
    chunks = split_into_chunks(text)
    scrubbed_chunks: list[str] = []
    print(f"⚡ Processing {len(chunks)} chunks using AI Logic...")

    system_prompt = f"""You are a GDPR Redaction Engine.
RULES:
0. If you find an NHS Number, replace it with {get_tag('NHS', redaction_style)}.
1. If you find a Name, replace it with {get_tag('NAME', redaction_style)}.
2. If you find an Address, replace it with {get_tag('ADDRESS', redaction_style)}.
3. If you find a Phone Number, replace it with {get_tag('PHONE', redaction_style)}.
4. Output ONLY the processed text. Do not add comments.
5. DO NOT change existing tags like [NHS-REDACTED].
"""

    for chunk in chunks:
        if not chunk.strip():
            scrubbed_chunks.append(chunk)
            continue

        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": chunk},
                ],
                temperature=0.1,
            )
            output = response.choices[0].message.content or ""

            # Defensive: if the LLM produced an unreasonably short response,
            # assume it refused / malfunctioned and keep the regex-cleaned chunk.
            if len(output) < len(chunk) * 0.5:
                scrubbed_chunks.append(chunk)
            else:
                scrubbed_chunks.append(output)

        except Exception as e:
            print(f"AI Error: {e}")
            scrubbed_chunks.append(chunk)

    return "".join(scrubbed_chunks)
