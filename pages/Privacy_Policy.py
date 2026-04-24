"""Privacy policy page — static content."""

import streamlit as st

st.set_page_config(
    page_title="Privacy Policy | RemovePII",
    page_icon="⚖️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    [data-testid="stSidebarNav"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stToolbar"] { visibility: hidden !important; }
    [data-testid="stDecoration"] { display: none !important; }
    footer { visibility: hidden !important; }
    .block-container { padding-top: 1rem !important; }
    h1 { color: #f0f2f6; }
    .subtitle { color: #00ff41; font-weight: bold; margin-bottom: 20px; }
    .stButton button { width: 100%; border-radius: 5px; font-weight: bold; }
</style>
""",
    unsafe_allow_html=True,
)

st.title("⚖️ Data Sovereignty & Privacy")
st.markdown(
    '<p class="subtitle">EFFECTIVE DATE: JANUARY 2026</p>',
    unsafe_allow_html=True,
)

st.info(
    """
**Core Mission:** This application is engineered for **Data Sovereignty**.
We do not sell data. We do not train AI on your data.
Processing occurs in-memory on our secure London infrastructure.
"""
)

st.markdown("---")

st.markdown(
    """
### 1. Architecture & Data Flow
Unlike typical SaaS tools, **RemovePII** operates on a **Zero-Persistence** architecture for document content.
* **Transport:** Your data is transmitted via an encrypted Cloudflare Tunnel (Enterprise Grade).
* **Processing:** Documents are processed in volatile memory (RAM) on our secure server.
* **Document Storage:** We do not write document content to disk. Once the redaction is complete and you download the file, the document data is wiped from RAM immediately.

### 2. Artificial Intelligence
We utilise a **Local LLM (Hybrid Engine)** to detect context.
* **No External APIs:** We do not send your text to OpenAI, Anthropic, or Google. The "Brain" is located physically on our server.
* **No Training:** Your inputs are never logged for model training purposes.

### 3. Usage Logs
* **What we log:** Connection metrics for billing and system stability — timestamp, client ID, action type, and document character count. No document content, no entity values, no filenames.
* **What we do NOT log:** Document content, filenames, extracted PII entities, or any content that could identify individuals in your data.
* **Feedback:** If you choose to submit feedback via the in-app form, we store your message and optional contact email so we can respond. You decide what to share.

### 4. Your Rights (GDPR / UK Data Protection Act 2018)
You retain full "Controller" status over your data. Because we do not store your document content, we cannot facilitate "Right to be Forgotten" requests on document content — there is nothing to forget. The connection-metric log and any feedback you submitted can be deleted on request.

### 5. Contact
For security audits, compliance certifications, or deletion requests, please contact the Admin Owner.
"""
)

st.markdown("---")

if st.button("⬅️ Homepage"):
    st.switch_page("frontend.py")
