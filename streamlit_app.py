"""
LegalEase AI - Streamlit Application Entrypoint
Fully self-contained, crash-proof, and optimized for Streamlit Community Cloud & Local Execution.
"""

import sys
import os
import io
import re
import html
import base64
from pathlib import Path
from datetime import date, timedelta
from typing import List, Optional, Tuple, Dict, Any

# ==============================================================================
# 1. DYNAMIC SYSTEM PATH RESOLUTION
# Ensures local backend packages can be found if running in nested directories
# ==============================================================================
CURRENT_DIR = Path(__file__).resolve().parent
CANDIDATE_PATHS = [
    CURRENT_DIR,
    CURRENT_DIR / "backend",
    CURRENT_DIR / "LegalEase-AI",
    CURRENT_DIR / "LegalEase-AI" / "backend",
    CURRENT_DIR.parent,
    CURRENT_DIR.parent / "LegalEase-AI",
]
for p in CANDIDATE_PATHS:
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

import streamlit as st
import requests

# Try importing optional binary document packages safely
try:
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
    from docx.oxml import OxmlElement, parse_xml
    from docx.oxml.ns import nsdecls, qn
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfgen import canvas
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ==============================================================================
# 2. CONFIGURATION & CONSTANTS
# ==============================================================================
LEGAL_DISCLAIMER = (
    "AI-generated document for drafting purposes only. "
    "This application does not provide legal advice. "
    "Review the generated document with a qualified legal professional before signing or using it."
)

SUPPORTED_DOC_TYPES = [
    "Employment Contract",
    "Non-Disclosure Agreement",
    "Lease Agreement",
    "Service Agreement",
    "Freelance Contract",
    "Partnership Agreement",
    "Sales Agreement",
    "General Agreement",
]

DEFAULT_LOGO_PATH = CURRENT_DIR / "assets" / "logo.png"
if not DEFAULT_LOGO_PATH.exists():
    alt_logo = CURRENT_DIR / "LegalEase-AI" / "assets" / "logo.png"
    if alt_logo.exists():
        DEFAULT_LOGO_PATH = alt_logo

# Resolve Gemini API Key from Streamlit Secrets or Environment Variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip()

try:
    if hasattr(st, "secrets"):
        if "GEMINI_API_KEY" in st.secrets:
            GEMINI_API_KEY = str(st.secrets["GEMINI_API_KEY"]).strip()
        if "GEMINI_MODEL" in st.secrets:
            GEMINI_MODEL = str(st.secrets["GEMINI_MODEL"]).strip()
except Exception:
    pass


# ==============================================================================
# 3. SMART CONTRACT PRESETS
# ==============================================================================
SMART_PRESETS = {
    "Employment Contract": {
        "parties": "Employer: Apex Technologies Pvt. Ltd., having its principal office at Tech Park, Bengaluru, India\nEmployee: John Doe, residing at 123 Palm Grove, Indiranagar, Bengaluru, India",
        "terms": "Annual Compensation of ₹12,00,000 paid in equal monthly installments;\nWorking hours: 40 hours per week Monday through Friday;\nNotice Period: 30 calendar days written notice required for termination by either party;\nStandard non-disclosure and intellectual property assignment covenants apply;\nProbationary period of 3 months from the Effective Date"
    },
    "Non-Disclosure Agreement": {
        "parties": "Disclosing Party: TechNova Solutions LLC, 100 Innovation Way, San Francisco, CA\nReceiving Party: Quantum Software Corp, 200 Enterprise Blvd, Austin, TX",
        "terms": "Confidential Information encompasses all technical data, trade secrets, proprietary algorithms, and source code;\nNon-disclosure obligation shall remain in full effect for 3 years from the Effective Date;\nReceiving Party agrees to exercise reasonable degree of care to prevent unauthorized dissemination;\nExclusions apply to information already in the public domain without breach;\nDisputes shall be governed by the laws of the State of California"
    },
    "Lease Agreement": {
        "parties": "Landlord: Robert Smith, residing at 45 Meadow Lane, New York, NY\nTenant: Sarah Jenkins, residing at 78 Elm Street, Brooklyn, NY",
        "terms": "Monthly rent of $2,400 payable on the 1st business day of each calendar month;\nSecurity deposit of $2,400 deposited with Landlord prior to move-in;\nLease term duration of 12 months with option to renew upon 60 days written notice;\nTenant is responsible for standard interior maintenance and utilities;\nNo subletting permitted without prior written consent from Landlord"
    },
    "Service Agreement": {
        "parties": "Client: Global Retail Enterprises Inc., 500 Commerce St, Chicago, IL\nService Provider: Agile Cloud Solutions LLC, 750 Tech Hub Dr, Seattle, WA",
        "terms": "Total project fee of $35,000 billed on verified milestone delivery schedule;\nProvider agrees to deliver comprehensive cloud migration services as detailed in Statement of Work;\nInvoices payable net 30 days from presentation;\nMutual confidentiality and standard professional liability limits apply;\nEither party may terminate for material breach with 15 days cure notice"
    },
    "Freelance Contract": {
        "parties": "Client: Stellar Marketing Studio, 12 Creative Ave, Los Angeles, CA\nContractor: Jane Doe (Independent UI/UX Designer), Mumbai, India",
        "terms": "Fixed project fee of ₹85,000 with 50% advance deposit upon agreement execution;\nDeliverables include complete mobile app Figma design system and interactive prototype by agreed deadline;\nAll intellectual property transfers to Client upon receipt of final invoice settlement;\nIncludes up to two rounds of design revisions;\nIndependent contractor status without employee benefits"
    },
    "Partnership Agreement": {
        "parties": "Partner 1: Alex Morgan (50% Equity & Managing Partner), London, UK\nPartner 2: David Chen (50% Equity & Technical Partner), London, UK",
        "terms": "Capital contribution of £25,000 by each partner at formation;\nProfit and loss distribution allocated strictly proportional to 50/50 equity shares;\nMajor operational and capital expenditure decisions require unanimous mutual consent;\nDispute resolution through binding professional commercial arbitration;\nBuyout rights triggered upon retirement or withdrawal notice of 90 days"
    },
    "Sales Agreement": {
        "parties": "Seller: Precision Machinery Corp, Industrial Area, Pune, India\nBuyer: Horizon Manufacturing Ltd, Auto Hub, Chennai, India",
        "terms": "Total purchase price of ₹18,50,000 for specified industrial CNC equipment;\nPayment schedule: 30% advance on order, 70% against delivery and operational inspection;\nSeller provides 12 months comprehensive warranty against manufacturing defects;\nDelivery to be completed within 45 days of advance payment receipt;\nRisk of loss transfers upon delivery to Buyer's facility"
    },
    "General Agreement": {
        "parties": "First Party: Alpha Operations Inc., 100 Main Street, Boston, MA\nSecond Party: Omega Logistics Group, 200 Harbor Way, Boston, MA",
        "terms": "Mutual collaboration to streamline regional logistics and fulfillment operations;\nAgreement effective for initial term of 1 year, automatically renewable;\nEach party retains ownership of its pre-existing intellectual property;\nStrict confidentiality and non-solicitation of employees during the term and for 1 year thereafter;\nGoverned by the laws of the Commonwealth of Massachusetts"
    }
}


# ==============================================================================
# 4. SANITIZATION & TERMS PARSER
# ==============================================================================
def sanitize_text(text: str) -> str:
    """Normalizes raw AI text, typographic quotes, and strips markdown wrappers."""
    if not text:
        return ""
    content = str(text)
    content = re.sub(r"^```[a-zA-Z0-9_-]*\s*\n", "", content)
    content = re.sub(r"\n```\s*$", "", content)
    replacements = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "--", "\u00a0": " ", "\ufeff": "", "\u200b": ""
    }
    for orig, repl in replacements.items():
        content = content.replace(orig, repl)
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip()


def parse_terms_to_table_data(terms: List[str]) -> List[Tuple[str, str]]:
    """Converts structured terms into (Category, Details) pairs for the terms schedule."""
    rows: List[Tuple[str, str]] = []
    for idx, term in enumerate(terms, start=1):
        clean_term = term.strip()
        if not clean_term:
            continue
        if ":" in clean_term:
            parts = clean_term.split(":", 1)
            rows.append((parts[0].strip(), parts[1].strip()))
        elif " - " in clean_term:
            parts = clean_term.split(" - ", 1)
            rows.append((parts[0].strip(), parts[1].strip()))
        else:
            rows.append((f"Term {idx}", clean_term))
    return rows


# ==============================================================================
# 5. RESILIENT GEMINI AI GENERATION ENGINE
# Directly uses Google Gemini REST API or SDK (Zero Missing-Package Crash Risk)
# ==============================================================================
def generate_legal_document_ai(
    doc_type: str,
    parties: str,
    terms: List[str],
    agreement_date: str,
    effective_date: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> str:
    """Generates a professional legal contract draft via Google Gemini."""
    active_key = (api_key or GEMINI_API_KEY).strip()
    if not active_key:
        raise ValueError("Google Gemini API key is missing. Please provide it in the sidebar or via secrets.")

    active_model = model_name or GEMINI_MODEL or "gemini-3.5-flash"
    terms_formatted = "\n".join(f"- {t}" for t in terms)
    dates_summary = f"Agreement Date: {agreement_date}\nEffective Date: {effective_date}"
    if start_date:
        dates_summary += f"\nTerm Start Date: {start_date}"
    if end_date:
        dates_summary += f"\nTerm End Date: {end_date}"

    prompt = f"""You are an expert legal document drafting attorney.
Your task is to generate a comprehensive, formal, structured legal contract draft titled "{doc_type}".

CRITICAL DRAFTING INSTRUCTIONS:
1. Generate a formal legal agreement draft based strictly on the user-provided parties, terms, and dates.
2. Structure with Title, Execution Date, Parties Clause, Recitals, Numbered Substantive Clauses (Scope, Payment, Term, Confidentiality, Intellectual Property, Termination, Dispute Resolution, Governing Law), and Formal Execution Signatures Block.
3. Incorporate every key term accurately and expand them into complete, enforceable provisions.
4. If localized addresses or specific state governing laws are missing, insert bracketed placeholders like [State/Jurisdiction].
5. Do not invent factual claims or statutory case citations. Return clean plaintext with section headings.

CONTRACT SPECIFICATIONS:
Document Type: {doc_type}
Parties Involved:
{parties}

Key Terms & Conditions:
{terms_formatted}

Milestone Dates:
{dates_summary}

Draft the complete formal legal agreement now:"""

    # First attempt: Google Gemini REST API v1beta (requires only requests)
    models_to_try = [active_model, "gemini-3.5-flash", "gemini-flash-latest", "gemini-3.1-pro-preview", "gemini-3.8-flash"]
    last_error = None

    for model in dict.fromkeys(models_to_try):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={active_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 8192}
            }
            resp = requests.post(url, json=payload, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                return sanitize_text(raw_text)
            else:
                err_data = resp.json()
                msg = err_data.get("error", {}).get("message", f"HTTP {resp.status_code}")
                last_error = f"{model} returned: {msg}"
        except Exception as e:
            last_error = str(e)
            continue

    raise Exception(f"Gemini generation failed: {last_error}")


# ==============================================================================
# 6. HTML PREVIEW BUILDER (NO INDENTATION TO AVOID MARKDOWN CODE BLOCKS)
# ==============================================================================
def format_html_preview(
    text: str,
    doc_type: str = "Legal Document",
    terms: Optional[List[str]] = None,
    logo_data_uri: Optional[str] = None,
) -> str:
    """Builds a high-resolution, full-size readable HTML document preview."""
    escaped_title = html.escape(doc_type.upper())
    lines = text.strip().split("\n")
    body_parts = []

    for line in lines:
        trimmed = line.strip()
        if not trimmed:
            body_parts.append("<div style='height: 12px;'></div>")
            continue
        escaped = html.escape(trimmed)
        if trimmed.startswith("# "):
            h_text = html.escape(trimmed.lstrip("#").strip())
            body_parts.append(f"<h3 style='color: #0f172a; margin-top: 24px; margin-bottom: 8px; font-weight: 800; border-bottom: 2px solid #0284c7; padding-bottom: 6px; font-size: 17px; font-family: sans-serif;'>{h_text}</h3>")
        elif trimmed.startswith("## "):
            h_text = html.escape(trimmed.lstrip("#").strip())
            body_parts.append(f"<h4 style='color: #1e3a8a; margin-top: 18px; margin-bottom: 8px; font-weight: 700; font-size: 15px; font-family: sans-serif;'>{h_text}</h4>")
        elif trimmed.startswith("### "):
            h_text = html.escape(trimmed.lstrip("#").strip())
            body_parts.append(f"<h5 style='color: #334155; margin-top: 14px; margin-bottom: 6px; font-weight: 700; font-size: 14px; font-family: sans-serif;'>{h_text}</h5>")
        elif any(trimmed.startswith(f"{n}.") for n in range(1, 30)) and len(trimmed) < 80:
            body_parts.append(f"<h4 style='color: #0f172a; margin-top: 16px; margin-bottom: 8px; font-weight: 700; font-size: 15px; font-family: sans-serif;'>{escaped}</h4>")
        elif trimmed.startswith("- ") or trimmed.startswith("* "):
            b_text = html.escape(trimmed[2:])
            body_parts.append(f"<div style='margin-left: 24px; margin-bottom: 8px; color: #1e293b; font-size: 14.5px; line-height: 1.7;'><span style='color: #0284c7; margin-right: 10px; font-weight: bold;'>&bull;</span>{b_text}</div>")
        else:
            body_parts.append(f"<p style='margin: 0 0 12px 0; color: #1e293b; line-height: 1.75; text-align: justify; font-size: 14.5px;'>{escaped}</p>")

    body_html = "\n".join(body_parts)

    terms_html = ""
    if terms and len(terms) > 0:
        parsed_terms = parse_terms_to_table_data(terms)
        rows_list = []
        for idx, (t_name, t_det) in enumerate(parsed_terms):
            bg = "#f8fafc" if idx % 2 == 0 else "#ffffff"
            rows_list.append(
                f"<tr style='background-color: {bg};'>"
                f"<td style='padding: 12px 16px; border: 1px solid #cbd5e1; font-weight: 700; color: #0f172a; width: 35%; font-size: 14px;'>{html.escape(t_name)}</td>"
                f"<td style='padding: 12px 16px; border: 1px solid #cbd5e1; color: #334155; font-size: 14px; line-height: 1.6;'>{html.escape(t_det)}</td>"
                f"</tr>"
            )
        rows_str = "".join(rows_list)
        terms_html = (
            "<div style='margin-top: 30px; margin-bottom: 24px;'>"
            "<h4 style='color: #0f172a; margin-bottom: 12px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; font-size: 15px; font-family: sans-serif;'>"
            "Schedule A: Summary of Agreed Key Terms"
            "</h4>"
            "<table style='width: 100%; border-collapse: collapse; font-size: 14px; border-radius: 6px; overflow: hidden; border: 1px solid #cbd5e1;'>"
            "<thead>"
            "<tr style='background-color: #0f172a; color: #ffffff;'>"
            "<th style='padding: 12px 16px; border: 1px solid #334155; text-align: left; font-weight: 700;'>Agreed Provision</th>"
            "<th style='padding: 12px 16px; border: 1px solid #334155; text-align: left; font-weight: 700;'>Term Specification / Details</th>"
            "</tr>"
            "</thead>"
            f"<tbody>{rows_str}</tbody>"
            "</table>"
            "</div>"
        )

    logo_tag = ""
    if logo_data_uri:
        logo_tag = f"<div style='text-align: center; margin-bottom: 20px;'><img src='{logo_data_uri}' style='max-height: 60px; max-width: 250px; object-fit: contain;' /></div>"

    return (
        "<div class='document-viewer' style='"
        "background-color: #ffffff; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 10px; "
        "padding: 40px 48px; font-family: Georgia, serif; min-height: 500px; max-height: 650px; "
        "overflow-y: auto; width: 100%; box-sizing: border-box; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);'>"
        f"{logo_tag}"
        "<div style='text-align: center; margin-bottom: 26px; border-bottom: 2px solid #0284c7; padding-bottom: 14px;'>"
        f"<h2 style='color: #0f172a; margin: 0 0 8px 0; font-size: 24px; font-weight: 800; font-family: sans-serif;'>{escaped_title}</h2>"
        "<div style='font-size: 13px; color: #0284c7; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; font-family: sans-serif;'>LegalEase AI Formatted Draft</div>"
        "</div>"
        f"<div>{body_html}</div>"
        f"{terms_html}"
        "<div style='margin-top: 36px; padding-top: 16px; border-top: 1px solid #e2e8f0; text-align: center; font-size: 12px; color: #64748b; font-family: sans-serif;'>"
        f"<div><strong>Legal Notice:</strong> {html.escape(LEGAL_DISCLAIMER)}</div>"
        "<div style='margin-top: 6px;'>LegalEase Inc. | contact@legalease.com | All Rights Reserved.</div>"
        "</div>"
        "</div>"
    )


# ==============================================================================
# 7. MULTI-FORMAT EXPORT HELPERS (TXT, DOCX, PDF)
# ==============================================================================
def export_txt(text: str, doc_type: str, terms: Optional[List[str]]) -> bytes:
    """Exports standardized plain text."""
    lines = ["=" * 70, f"  {doc_type.upper()}", "  Generated via LegalEase AI", "=" * 70, "", text.strip(), ""]
    if terms:
        lines += ["-" * 70, "SCHEDULE A: SUMMARY OF AGREED TERMS", "-" * 70]
        for idx, t in enumerate(terms, 1):
            lines.append(f"[{idx}] {t.strip()}")
        lines.append("")
    lines += ["-" * 70, f"NOTICE: {LEGAL_DISCLAIMER}", "LegalEase Inc. | contact@legalease.com | All Rights Reserved."]
    return "\n".join(lines).encode("utf-8")


def export_docx(text: str, doc_type: str, terms: Optional[List[str]], logo_bytes: Optional[bytes]) -> Optional[bytes]:
    """Exports Word .docx if python-docx is installed."""
    if not HAS_DOCX:
        return None
    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        footer_p = section.footer.paragraphs[0]
        footer_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r = footer_p.add_run(f"LegalEase AI Draft | {LEGAL_DISCLAIMER}")
        r.font.name = "Times New Roman"
        r.font.size = Pt(8.5)
        r.font.italic = True

    if logo_bytes:
        try:
            doc.add_paragraph().add_run().add_picture(io.BytesIO(logo_bytes), width=Inches(1.8))
        except Exception:
            pass

    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    tr = title_p.add_run(doc_type.upper())
    tr.font.name = "Times New Roman"
    tr.font.size = Pt(18)
    tr.font.bold = True

    for line in text.strip().split("\n"):
        ln = line.strip()
        if not ln:
            continue
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.15
        run = p.add_run(ln.lstrip("#").strip())
        run.font.name = "Times New Roman"
        if ln.startswith("# ") or ln.isupper():
            run.font.size = Pt(14)
            run.font.bold = True
        elif ln.startswith("## ") or any(ln.startswith(f"{i}.") for i in range(1, 30)):
            run.font.size = Pt(12)
            run.font.bold = True
        else:
            run.font.size = Pt(11)

    if terms:
        doc.add_paragraph().add_run("SCHEDULE A: KEY AGREEMENT TERMS").bold = True
        t_data = parse_terms_to_table_data(terms)
        tbl = doc.add_table(rows=1, cols=2)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.rows[0].cells[0].text = "Agreed Provision"
        tbl.rows[0].cells[1].text = "Specification / Details"
        for t_name, t_det in t_data:
            r_cells = tbl.add_row().cells
            r_cells[0].text = t_name
            r_cells[1].text = t_det

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def export_pdf(text: str, doc_type: str, terms: Optional[List[str]], logo_bytes: Optional[bytes]) -> Optional[bytes]:
    """Exports PDF if ReportLab is installed."""
    if not HAS_REPORTLAB:
        return None
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()
    t_style = ParagraphStyle("T", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=18, leading=22, alignment=1)
    b_style = ParagraphStyle("B", parent=styles["Normal"], fontName="Times-Roman", fontSize=10, leading=14, spaceAfter=6)
    h_style = ParagraphStyle("H", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=12, leading=16, spaceBefore=12, spaceAfter=4)
    story = [Paragraph(doc_type.upper(), t_style), HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0284c7"), spaceAfter=12)]

    for line in text.strip().split("\n"):
        ln = line.strip()
        if not ln:
            continue
        clean = ln.lstrip("#").strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if ln.startswith("# ") or ln.startswith("## ") or any(ln.startswith(f"{i}.") for i in range(1, 30)):
            story.append(Paragraph(clean, h_style))
        else:
            story.append(Paragraph(clean, b_style))

    if terms:
        story.append(Paragraph("SCHEDULE A: KEY AGREEMENT TERMS", h_style))
        t_rows = [[Paragraph("Agreed Provision", h_style), Paragraph("Specification", h_style)]]
        for tn, td in parse_terms_to_table_data(terms):
            t_rows.append([Paragraph(tn, b_style), Paragraph(td, b_style)])
        story.append(Table(t_rows, colWidths=[160, 340]))

    doc.build(story)
    return buf.getvalue()


# ==============================================================================
# 8. STREAMLIT UI SETUP & THEME
# ==============================================================================
st.set_page_config(page_title="LegalEase AI", page_icon="⚖️", layout="wide")

# Custom CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@700;800&family=Outfit:wght@400;500;600;700&family=Source+Serif+4:wght@400;600;700&display=swap');
html, body, [class*="css"], .stApp { font-family: 'Outfit', sans-serif !important; }
h1 { font-family: 'Cinzel', serif !important; color: #ffffff !important; }
.smart-card-title { font-size: 15px; font-weight: 700; color: #38bdf8; margin-bottom: 12px; padding-bottom: 6px; border-bottom: 2px solid #0284c7; text-transform: uppercase; }
.legalease-disclaimer-box { background: rgba(245, 158, 11, 0.08); border-left: 4px solid #f59e0b; border-radius: 8px; padding: 10px 18px; margin-bottom: 18px; color: #fde68a; font-size: 12.5px; }
.stButton > button { background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important; color: #ffffff !important; font-weight: 700 !important; border-radius: 8px !important; border: none !important; padding: 10px 22px !important; }
.stDownloadButton > button { background-color: #0f172a !important; border: 1px solid #0284c7 !important; color: #38bdf8 !important; font-weight: 700 !important; border-radius: 8px !important; }
.document-viewer { background-color: #ffffff !important; color: #0f172a !important; border-radius: 10px !important; padding: 36px 44px !important; font-family: 'Source Serif 4', Georgia, serif !important; }
</style>
""", unsafe_allow_html=True)

# Session State Init
if "generated_document" not in st.session_state:
    st.session_state["generated_document"] = None
if "edited_document" not in st.session_state:
    st.session_state["edited_document"] = None
if "is_editing" not in st.session_state:
    st.session_state["is_editing"] = False
if "document_type" not in st.session_state:
    st.session_state["document_type"] = "Employment Contract"
if "parsed_terms" not in st.session_state:
    st.session_state["parsed_terms"] = []
if "custom_logo_bytes" not in st.session_state:
    st.session_state["custom_logo_bytes"] = None


# Sidebar
with st.sidebar:
    st.markdown("### ⚖️ LegalEase System")
    if DEFAULT_LOGO_PATH.exists():
        st.image(str(DEFAULT_LOGO_PATH), width=200)
    else:
        st.markdown("<h2 style='text-align: center; color: #38bdf8;'>⚖️ LegalEase AI</h2>", unsafe_allow_html=True)
    st.markdown("---")

    # API Key Input
    user_key = st.text_input("Gemini API Key", value=GEMINI_API_KEY, type="password", help="Enter your Google Gemini API key")
    if user_key:
        GEMINI_API_KEY = user_key

    st.markdown("---")
    st.markdown("#### Contract Categories")
    for cat in SUPPORTED_DOC_TYPES:
        st.caption(f"• {cat}")
    st.markdown("---")
    if st.button("🔄 Reset Document Session"):
        st.session_state["generated_document"] = None
        st.session_state["edited_document"] = None
        st.session_state["is_editing"] = False
        st.rerun()


# Top Banner
col_h1, col_h2 = st.columns([1, 5])
with col_h1:
    if DEFAULT_LOGO_PATH.exists():
        st.image(str(DEFAULT_LOGO_PATH), width=105)
    else:
        st.markdown("<div style='font-size: 42px;'>⚖️</div>", unsafe_allow_html=True)
with col_h2:
    st.markdown("""
    <div style='padding-top: 2px;'>
        <h1 style='margin: 0; font-size: 2.2rem;'>LEGALEASE AI</h1>
        <div style='font-size: 0.95rem; color: #38bdf8; font-weight: 700; text-transform: uppercase;'>AI-Powered Legal Document Generator</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"<div class='legalease-disclaimer-box'><strong>⚠️ Legal Notice:</strong> {LEGAL_DISCLAIMER}</div>", unsafe_allow_html=True)

# Main Two-Column Layout
col_left, col_right = st.columns([1, 1], gap="large")

# Left Column: Inputs
with col_left:
    st.markdown("<div class='smart-card-title'>📄 1. Document Configuration</div>", unsafe_allow_html=True)
    selected_doc_type = st.selectbox("Document Category", options=SUPPORTED_DOC_TYPES, index=0)
    preset = SMART_PRESETS.get(selected_doc_type, SMART_PRESETS["Employment Contract"])

    if st.session_state.get("prev_doc_type") != selected_doc_type:
        st.session_state["prev_doc_type"] = selected_doc_type
        st.session_state["parties_val"] = preset["parties"]
        st.session_state["terms_val"] = preset["terms"]

    parties_input = st.text_area("Parties Involved", value=st.session_state.get("parties_val", preset["parties"]), height=95)
    terms_input = st.text_area("Key Terms (Use ';' between clauses)", value=st.session_state.get("terms_val", preset["terms"]), height=125)

    st.markdown("<div class='smart-card-title' style='margin-top: 15px;'>📅 2. Agreement Dates</div>", unsafe_allow_html=True)
    today = date.today()
    c1, c2 = st.columns(2)
    with c1:
        agree_date = st.date_input("Agreement Date", value=today)
        start_d = st.date_input("Start Date", value=today)
    with c2:
        eff_date = st.date_input("Effective Date", value=today)
        end_d = st.date_input("End Date", value=today + timedelta(days=365))

    st.markdown("<div class='smart-card-title' style='margin-top: 15px;'>🏢 3. Branding (Optional)</div>", unsafe_allow_html=True)
    uploaded_logo = st.file_uploader("Upload Organization Logo", type=["png", "jpg", "jpeg"])
    if uploaded_logo:
        st.session_state["custom_logo_bytes"] = uploaded_logo.read()
        st.success("Logo uploaded!")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    generate_btn = st.button("✨ Generate Legal Document", type="primary")

    if generate_btn:
        clean_terms = [t.strip() for t in terms_input.replace("\n", ";").split(";") if t.strip()]
        if not clean_terms:
            st.error("Please enter at least one key term.")
        elif end_d < start_d:
            st.error(f"End date ({end_d}) cannot precede Start date ({start_d}).")
        else:
            with st.spinner("🤖 Gemini AI is drafting your comprehensive legal agreement..."):
                try:
                    draft = generate_legal_document_ai(
                        doc_type=selected_doc_type,
                        parties=parties_input,
                        terms=clean_terms,
                        agreement_date=agree_date.strftime("%Y-%m-%d"),
                        effective_date=eff_date.strftime("%Y-%m-%d"),
                        start_date=start_d.strftime("%Y-%m-%d"),
                        end_date=end_d.strftime("%Y-%m-%d"),
                        api_key=GEMINI_API_KEY,
                    )
                    st.session_state["generated_document"] = draft
                    st.session_state["edited_document"] = draft
                    st.session_state["document_type"] = selected_doc_type
                    st.session_state["parsed_terms"] = clean_terms
                    st.toast("✅ Document Generated Successfully!", icon="⚖️")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Generation error: {ex}")


# Right Column: Document Preview & Downloads
with col_right:
    current_doc = st.session_state.get("edited_document") or st.session_state.get("generated_document")

    if current_doc:
        doc_type = st.session_state.get("document_type", "Legal Document")
        terms = st.session_state.get("parsed_terms", [])
        logo_b = st.session_state.get("custom_logo_bytes")

        # Edit Toggle
        col_t, col_b = st.columns([2, 1])
        with col_t:
            st.markdown("<div class='smart-card-title' style='margin-bottom: 0;'>📜 Document Preview</div>", unsafe_allow_html=True)
        with col_b:
            if st.button("❌ Close Editor" if st.session_state["is_editing"] else "✏️ Edit Draft"):
                st.session_state["is_editing"] = not st.session_state["is_editing"]
                st.rerun()

        if st.session_state["is_editing"]:
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            new_text = st.text_area("Edit Agreement Text", value=current_doc, height=360)
            if st.button("💾 Save Changes", type="primary"):
                st.session_state["edited_document"] = new_text
                st.session_state["is_editing"] = False
                st.success("Draft saved!")
                st.rerun()

        # Render HTML Preview
        logo_uri = None
        if logo_b:
            logo_uri = f"data:image/png;base64,{base64.b64encode(logo_b).decode('utf-8')}"
        html_view = format_html_preview(current_doc, doc_type, terms, logo_uri)
        st.markdown(html_view, unsafe_allow_html=True)

        # Download Buttons
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='smart-card-title'>💾 Download Document</div>", unsafe_allow_html=True)
        c_t, c_w, c_p = st.columns(3)
        safe_name = doc_type.lower().replace(" ", "_")

        with c_t:
            st.download_button("📄 Download .TXT", data=export_txt(current_doc, doc_type, terms), file_name=f"{safe_name}.txt", mime="text/plain")
        with c_w:
            docx_data = export_docx(current_doc, doc_type, terms, logo_b)
            if docx_data:
                st.download_button("📝 Download .DOCX", data=docx_data, file_name=f"{safe_name}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            else:
                st.caption("Install python-docx for Word export")
        with c_p:
            pdf_data = export_pdf(current_doc, doc_type, terms, logo_b)
            if pdf_data:
                st.download_button("📕 Download .PDF", data=pdf_data, file_name=f"{safe_name}.pdf", mime="application/pdf")
            else:
                st.caption("Install reportlab for PDF export")

    else:
        st.markdown("<div class='smart-card-title'>📜 Document Preview</div>", unsafe_allow_html=True)
        st.info("👈 Enter agreement details on the left and click **'✨ Generate Legal Document'** to preview your finalized draft.")
        st.markdown("""
        <div style='border: 2px dashed #334155; border-radius: 10px; padding: 50px 24px; text-align: center; color: #94a3b8; background-color: #0f172a;'>
            <div style='font-size: 40px; margin-bottom: 12px;'>📄</div>
            <div style='font-size: 16px; font-weight: 700; color: #f8fafc;'>Your generated agreement will appear here</div>
            <div style='font-size: 13.5px; margin-top: 8px; color: #94a3b8;'>
                Full-size readable paper view &bull; Schedule A Terms Table &bull; Live Editing &bull; Word, PDF & TXT Exports
            </div>
        </div>
        """, unsafe_allow_html=True)
