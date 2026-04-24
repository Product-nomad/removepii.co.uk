"""RemovePII — Streamlit frontend.

Authentication is license-key based. The client database is loaded from an
external JSON file (path in `REMOVEPII_CLIENTS_FILE`, default `clients.json`)
which is gitignored. See `clients.json.example` for the schema.
"""

import json
import os
import time
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv

from backend import scrub_text_hybrid

load_dotenv()

# --- 1. PAGE CONFIG ---
st.set_page_config(
    page_title="RemovePII | GDPR Document Redactor",
    page_icon="🛡️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --- 2. CSS ---
st.markdown(
    """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="InputInstructions"] { display: none !important; }

    h1, .subtitle { text-align: center; font-family: 'Helvetica Neue', sans-serif; }
    h1 { color: #f0f2f6; margin-bottom: 0px; }
    .subtitle { color: #00ff41; font-weight: bold; margin-bottom: 20px; font-size: 1.1em; }

    .success-box {
        padding: 15px; background-color: #d4edda; color: #155724;
        border-radius: 5px; text-align: center; margin-top: 20px;
    }
    .mission-quote {
        text-align: center; font-style: italic; color: #a0a0a0;
        margin-top: 30px; padding: 20px; border-top: 1px solid #333;
        font-size: 0.95em; line-height: 1.6;
    }
    div[data-testid="column"] { display: flex; align-items: flex-end !important; }
</style>
""",
    unsafe_allow_html=True,
)


# --- 3. CLIENT DATABASE (loaded from external file) ---
def load_client_db() -> dict[str, str]:
    path = Path(os.getenv("REMOVEPII_CLIENTS_FILE", "clients.json"))
    if not path.exists():
        st.error(
            f"Client database not found at `{path}`. "
            "Ask the admin for access; see `clients.json.example` for the schema."
        )
        st.stop()
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as err:
        st.error(f"Client database malformed ({err}).")
        st.stop()


CLIENT_DB = load_client_db()


def check_login(key: str) -> str | None:
    return CLIENT_DB.get(key)


# --- 4. HEADER ---
col1, col2, col3 = st.columns([1, 8, 1])
with col2:
    st.title("🛡️Document Anonymiser")
    st.markdown(
        '<p class="subtitle">SECURE REDACTION • NO CLOUD UPLOADS • NO DATA SAVED</p>',
        unsafe_allow_html=True,
    )

# --- 5. TRUST SIGNALS ---
st.markdown("---")
m1, m2, m3 = st.columns(3)
m1.metric("Server Location", "London, UK", "Active")
m2.metric("Encryption", "AES-256", "On")
m3.metric("Data Log", "Disabled", "0 Records")

with st.expander("🛡️ See How It Works (Technical Architecture)"):
    st.markdown(
        "Our architecture is designed so that data never touches a hard drive. "
        "It flows through a secure tunnel, is scrubbed in-memory, and returned promptly."
    )
    if Path("assets/architecture.png").exists():
        st.image("assets/architecture.png")

with st.expander("🛡️ See How It Works (Infographic)"):
    st.markdown("A visual guide to how we keep your data safe without ever storing it.")
    if Path("assets/piiremoval.png").exists():
        st.image("assets/piiremoval.png")

st.markdown("---")

# --- 6. AUTHENTICATION ---
if "authenticated_client" not in st.session_state:
    st.session_state.authenticated_client = None

if st.session_state.authenticated_client is None:
    st.info("🔒 This secure portal is restricted to authorised clients.")
    lc1, lc2, lc3 = st.columns([1, 2, 1])
    with lc2:
        input_key = st.text_input("Enter License Key", type="password")
        if st.button("Access Portal", type="primary", use_container_width=True):
            client_name = check_login(input_key)
            if client_name:
                st.session_state.authenticated_client = client_name
                st.success(f"Welcome back, {client_name}")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Invalid License Key")

    st.markdown(
        """<div class="mission-quote">"We treat your data like a physical letter. We open it in a secure room in London, black out the personal information, hand it back to you, then burn the original."</div>""",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; font-size: 12px;'>RemovePII Ltd © 2026</div>",
        unsafe_allow_html=True,
    )

else:
    # --- MAIN DASHBOARD (LOGGED IN) ---
    tab1, tab2 = st.tabs(["📝 Paste Text", "📂 Upload CV/Document"])

    # TAB 1: Text Paste
    with tab1:
        col_style, col_spacer = st.columns([1, 2])
        with col_style:
            redaction_style = st.selectbox(
                "Redaction Style:", options=["Redacted", "Removed", "Blank"]
            )

        text_input = st.text_area(
            "Paste text here", height=200, placeholder="e.g. Hi, please send to..."
        )

        btn_col, spacer_col, feedback_col = st.columns([3, 5, 2])
        with btn_col:
            do_process = st.button("Anonymise Text", type="primary")

        with feedback_col, st.popover("Did it work?"):
            st.markdown("**Report an Issue**")
            with st.form("feedback_form_inline", clear_on_submit=True):
                fb_msg = st.text_area("What happened?", height=100)
                fb_email = st.text_input("Your Email (Optional)")
                if st.form_submit_button("Send Report") and fb_msg:
                    try:
                        payload = {"message": fb_msg, "contact": fb_email}
                        requests.post(
                            os.getenv(
                                "FEEDBACK_URL",
                                "http://127.0.0.1:8000/v1/feedback",
                            ),
                            json=payload,
                            timeout=5,
                        )
                        st.toast("✅ Feedback sent!")
                    except Exception:
                        st.error("Connection failed.")

        if do_process:
            if text_input:
                word_count = len(text_input.split())
                est_minutes = round(word_count / 400, 1)
                if est_minutes < 0.1:
                    est_minutes = "less than 1"
                st.info(f"⏳ Processing **{word_count} words**. Expected: **{est_minutes} min**.")
                with st.spinner("🛡️ Scrubbing text..."):
                    time.sleep(0.8)
                    clean = scrub_text_hybrid(
                        text_input,
                        st.session_state.authenticated_client,
                        redaction_style,
                    )
                st.markdown(
                    '<div class="success-box">✅ **Redaction Complete**</div>',
                    unsafe_allow_html=True,
                )
                st.code(clean, language="text")
                st.caption("Copy the text above. No data is saved.")
            else:
                st.warning("Please paste some text first.")

        st.markdown("---")
        st.caption("🧪 **Want to test it? Copy and paste our dummy data:**")
        col_test1, col_test2 = st.columns(2)
        with col_test1:
            st.markdown(
                "📄 [**Test Doc - Example CV**](https://docs.google.com/document/d/1ixUtnB0V9qQ-8kwa4OLXy4GvUDM_n5snaxlsrRU--0s/edit?tab=t.0)"
            )
        with col_test2:
            st.markdown(
                "📄 [**Test Doc - Example SAR**](https://docs.google.com/document/d/1qZX6yLQpvYVXcdtHJC3H0ZAw81QfEBSFnEcTpBKGpjs/edit?tab=t.0)"
            )

    # TAB 2: File Upload
    with tab2:
        col_style_up, col_spacer_up = st.columns([1, 2])
        with col_style_up:
            upload_style = st.selectbox(
                "Redaction Style:",
                options=["Redacted", "Removed", "Blank"],
                key="upload_style_selector",
            )

        st.caption("Upload a `.txt` file (PDF support coming in v2).")
        uploaded_file = st.file_uploader("Drop Document Here", type=["txt"])

        if uploaded_file:
            string_data = uploaded_file.getvalue().decode("utf-8")
            st.info(f"File loaded: **{uploaded_file.name}**")

            if st.button("Process Document", type="primary"):
                with st.spinner("🛡️ Scrubbing document..."):
                    clean = scrub_text_hybrid(
                        string_data,
                        st.session_state.authenticated_client,
                        upload_style,
                    )
                    st.success("Document scrubbed successfully!")
                    st.download_button(
                        label="⬇️ Download Redacted Copy",
                        data=clean,
                        file_name=f"REDACTED_{uploaded_file.name}",
                        mime="text/plain",
                    )

    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; font-size: 12px;'>RemovePII Ltd © 2026</div>",
        unsafe_allow_html=True,
    )
