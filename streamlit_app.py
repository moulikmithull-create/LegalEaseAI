"""
LegalEase AI - Streamlit Application Root Entrypoint
Compatible with Streamlit Community Cloud, Hugging Face Spaces, and Local Deployment.
"""

import sys
import os
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from backend.config import DEFAULT_LOGO_PATH, LEGAL_DISCLAIMER
from backend.models.schemas import DocumentRequest
from backend.services.document_service import DocumentService
from frontend.utils.api_client import LegalEaseAPIClient
from frontend.components.input_form import render_input_form
from frontend.components.preview import render_preview_and_editor
from frontend.components.download_buttons import render_download_buttons


# Set Page Configuration
st.set_page_config(
    page_title="LegalEase AI - Legal Document Generator",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load Custom CSS Stylesheet
css_path = PROJECT_ROOT / "frontend" / "styles" / "custom.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Initialize Session State
def init_session_state():
    defaults = {
        "generated_document": None,
        "edited_document": None,
        "document_type": "Employment Contract",
        "parsed_terms": [],
        "custom_logo_bytes": None,
        "is_editing": False,
        "error_message": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session_state()

# Initialize API Client and Local Document Service
api_client = LegalEaseAPIClient()
local_doc_service = DocumentService()

# Sidebar: System Status & Presets
with st.sidebar:
    st.markdown("### ⚖️ LegalEase System")

    # Display Logo
    if st.session_state.get("custom_logo_bytes"):
        st.image(st.session_state["custom_logo_bytes"], width=200)
    elif os.path.exists(DEFAULT_LOGO_PATH):
        st.image(str(DEFAULT_LOGO_PATH), width=200)
    else:
        st.markdown("<h2 style='text-align: center; color: #38bdf8;'>⚖️ LegalEase AI</h2>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### System Status")

    # Verify Connectivity
    is_healthy, health_msg, health_data = api_client.check_health()
    if is_healthy:
        st.markdown("<span class='status-pill online'>● Backend Connected</span>", unsafe_allow_html=True)
        if health_data and health_data.get("api_key_configured"):
            st.caption(f"AI Engine: {health_data.get('model_configured', 'Gemini')} (Online)")
        else:
            st.warning("API key not configured in .env.")
    else:
        # Standalone Direct Engine mode
        api_key_present = bool(os.getenv("GEMINI_API_KEY", "").strip())
        if api_key_present:
            st.markdown("<span class='status-pill online'>● Cloud Standalone Mode</span>", unsafe_allow_html=True)
            st.caption(f"AI Engine: {os.getenv('GEMINI_MODEL', 'gemini-3.5-flash')} (Direct)")
        else:
            st.markdown("<span class='status-pill offline'>● Setup Required</span>", unsafe_allow_html=True)
            st.caption("Please configure GEMINI_API_KEY in .env or secrets.")

    st.markdown("---")
    st.markdown("#### Contract Categories")
    st.markdown("""
    - **Employment Contracts**
    - **Non-Disclosure Agreements**
    - **Lease Agreements**
    - **Service Agreements**
    - **Freelance Contracts**
    - **Partnership Agreements**
    - **Sales Agreements**
    - **General Agreements**
    """)

    st.markdown("---")
    if st.button("🔄 Start New Agreement"):
        st.session_state["generated_document"] = None
        st.session_state["edited_document"] = None
        st.session_state["is_editing"] = False
        st.session_state["error_message"] = None
        st.rerun()


# Application Header Banner
col_hdr1, col_hdr2 = st.columns([1, 5])
with col_hdr1:
    if st.session_state.get("custom_logo_bytes"):
        st.image(st.session_state["custom_logo_bytes"], width=105)
    elif os.path.exists(DEFAULT_LOGO_PATH):
        st.image(str(DEFAULT_LOGO_PATH), width=105)
    else:
        st.markdown("<div style='font-size: 42px; text-align: center;'>⚖️</div>", unsafe_allow_html=True)

with col_hdr2:
    st.markdown("""
    <div style='padding-top: 2px;'>
        <h1 style='margin: 0; font-size: 2.2rem; font-weight: 800; color: #ffffff; letter-spacing: -0.5px;'>LEGALEASE AI</h1>
        <div style='font-size: 0.95rem; color: #38bdf8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px;'>
            AI-Powered Legal Document Generator
        </div>
    </div>
    """, unsafe_allow_html=True)

# Prominent Legal Notice Banner
st.markdown(f"""
<div class='legalease-disclaimer-box'>
    <strong>⚠️ Legal Notice:</strong> {LEGAL_DISCLAIMER}
</div>
""", unsafe_allow_html=True)


# Main Layout (Two Responsive Columns)
col_left, col_right = st.columns([1, 1], gap="large")

# Left Column: Smart Input Form
with col_left:
    payload = render_input_form()

# Process Generation Payload
if payload:
    with st.spinner("🤖 Gemini AI is drafting your comprehensive legal agreement..."):
        # Try REST API backend first
        is_healthy, _, _ = api_client.check_health()
        if is_healthy:
            success, err_msg, resp_data = api_client.generate_document(payload)
            if success and resp_data:
                generated_content = resp_data.get("content", "")
            else:
                generated_content = None
        else:
            # Standalone direct generation fallback
            try:
                doc_req = DocumentRequest(**payload)
                resp = local_doc_service.generate(doc_req)
                success = resp.success
                generated_content = resp.content
                err_msg = resp.error
            except Exception as e:
                success = False
                generated_content = None
                err_msg = str(e)

    if success and generated_content:
        st.session_state["generated_document"] = generated_content
        st.session_state["edited_document"] = generated_content
        st.session_state["document_type"] = payload["document_type"]
        st.session_state["error_message"] = None
        st.toast("✅ Legal Document Generated Successfully!", icon="⚖️")
        st.rerun()
    else:
        st.session_state["error_message"] = err_msg
        st.error(f"Generation Failed: {err_msg}")

# Right Column: Document Preview, Editor & Downloads
with col_right:
    current_doc = st.session_state.get("edited_document") or st.session_state.get("generated_document")

    if current_doc:
        doc_type = st.session_state.get("document_type", "Legal Document")
        terms = st.session_state.get("parsed_terms", [])
        logo_bytes = st.session_state.get("custom_logo_bytes")

        # Render Full-size Preview & Editor
        render_preview_and_editor(
            content=current_doc,
            doc_type=doc_type,
            terms=terms,
            logo_bytes=logo_bytes,
        )

        # Render Download Buttons
        render_download_buttons(
            content=current_doc,
            doc_type=doc_type,
            terms=terms,
            logo_bytes=logo_bytes,
        )

    else:
        st.markdown("<div class='smart-card-title'>📜 Document Preview</div>", unsafe_allow_html=True)
        st.info("👈 Enter agreement terms on the left and click **'✨ Generate Legal Document'** to preview your finalized draft here.")

        st.markdown("""
        <div style='border: 2px dashed #334155; border-radius: 10px; padding: 50px 24px; text-align: center; color: #94a3b8; background-color: #0f172a;'>
            <div style='font-size: 40px; margin-bottom: 12px;'>📄</div>
            <div style='font-size: 16px; font-weight: 700; color: #f8fafc;'>Your generated agreement will appear here</div>
            <div style='font-size: 13.5px; margin-top: 8px; color: #94a3b8; line-height: 1.6;'>
                Structured clauses &bull; Semicolon Terms Schedule Table &bull; Live Inline Editing &bull; Word, PDF & TXT Exports
            </div>
        </div>
        """, unsafe_allow_html=True)
