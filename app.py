"""
DocuMind: Intelligent Contract Analyzer
=======================================
Multi-jurisdiction contract analysis with AI-powered risk assessment.

Made by Kashika Wanchoo | kashikaaw@gmail.com
"""

import os
import re
import json
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from document_processor import DocumentProcessor, VisionExtractor, DocumentType, ExtractionMethod
from contract_analyzer import ContractAnalyzer, ContractLLM, ClauseType, RiskLevel, format_risk_badge, analysis_to_dict

# =============================================================================
# JURISDICTION DATABASE
# =============================================================================

JURISDICTIONS = {
    "india_central": {
        "name": "India (Central Law)",
        "region": "India",
        "sub_jurisdiction": "Central",
        "primary_law": "Indian Contract Act, 1872",
        "additional_laws": [
            "Specific Relief Act, 1963",
            "Arbitration and Conciliation Act, 1996",
            "Information Technology Act, 2000",
            "Digital Personal Data Protection Act, 2023",
            "Competition Act, 2002"
        ],
        "key_considerations": [
            "Central law applies uniformly across all states",
            "Stamp duty varies by state",
            "E-contracts valid under IT Act Section 10A",
            "Non-compete clauses generally unenforceable post-employment",
            "Arbitration seat determines procedural law"
        ],
        "detection_signals": ["india", "indian", "rupees", "inr", "mumbai", "delhi", "bangalore", "indian contract act"],
        "official_language": "English / Hindi",
        "court_system": "District Courts - High Courts - Supreme Court"
    },
    "uae_mainland": {
        "name": "UAE (Mainland)",
        "region": "UAE",
        "sub_jurisdiction": "Mainland",
        "primary_law": "UAE Civil Code (Federal Law No. 5 of 1985)",
        "additional_laws": [
            "Federal Commercial Transactions Law",
            "UAE Labor Law",
            "Federal Data Protection Law"
        ],
        "key_considerations": [
            "Arabic is the ONLY official legal language",
            "Sharia principles may influence interpretation",
            "Post-dated cheques carry criminal liability",
            "No concept of consideration in civil law"
        ],
        "detection_signals": ["uae", "dubai", "abu dhabi", "dirhams", "aed", "emirates"],
        "negative_signals": ["difc", "adgm"],
        "official_language": "Arabic",
        "court_system": "Court of First Instance - Court of Appeal - Court of Cassation"
    },
    "uae_difc": {
        "name": "UAE (DIFC)",
        "region": "UAE",
        "sub_jurisdiction": "DIFC",
        "primary_law": "DIFC Contract Law (DIFC Law No. 6 of 2004)",
        "additional_laws": [
            "DIFC Companies Law",
            "DIFC Employment Law",
            "DIFC Data Protection Law"
        ],
        "key_considerations": [
            "English common law applies - NOT UAE Civil Code",
            "DIFC Courts have exclusive jurisdiction",
            "English is the official language",
            "Consideration required for contracts"
        ],
        "detection_signals": ["difc", "dubai international financial centre", "difc law", "difc courts"],
        "official_language": "English",
        "court_system": "DIFC Courts (independent)"
    },
    "uae_adgm": {
        "name": "UAE (ADGM)",
        "region": "UAE",
        "sub_jurisdiction": "ADGM",
        "primary_law": "ADGM Regulations (English common law)",
        "additional_laws": [
            "ADGM Companies Regulations",
            "ADGM Employment Regulations",
            "ADGM Data Protection Regulations"
        ],
        "key_considerations": [
            "English common law applies",
            "ADGM Courts have exclusive jurisdiction",
            "Similar to DIFC but based in Abu Dhabi"
        ],
        "detection_signals": ["adgm", "abu dhabi global market"],
        "official_language": "English",
        "court_system": "ADGM Courts (independent)"
    },
    "usa_delaware": {
        "name": "USA (Delaware)",
        "region": "USA",
        "sub_jurisdiction": "Delaware",
        "primary_law": "Delaware General Corporation Law",
        "additional_laws": [
            "Uniform Commercial Code (Delaware)",
            "Delaware LLC Act"
        ],
        "key_considerations": [
            "Most favorable for corporate contracts",
            "Court of Chancery specializes in business disputes",
            "Over 65% of Fortune 500 incorporated here",
            "Freedom of contract strongly upheld"
        ],
        "detection_signals": ["delaware", "wilmington", "court of chancery", "dgcl", "state of delaware"],
        "official_language": "English",
        "court_system": "Court of Chancery / Superior Court - Supreme Court of Delaware"
    },
    "usa_newyork": {
        "name": "USA (New York)",
        "region": "USA",
        "sub_jurisdiction": "New York",
        "primary_law": "New York General Obligations Law",
        "additional_laws": [
            "New York UCC",
            "New York Business Corporation Law"
        ],
        "key_considerations": [
            "Standard for financial contracts globally",
            "Strict interpretation of contract terms",
            "Contracts over $250K can choose NY law without NY connection"
        ],
        "detection_signals": ["new york", "nyc", "manhattan", "ny law", "new york law"],
        "official_language": "English",
        "court_system": "Supreme Court - Appellate Division - Court of Appeals"
    },
    "usa_california": {
        "name": "USA (California)",
        "region": "USA",
        "sub_jurisdiction": "California",
        "primary_law": "California Civil Code",
        "additional_laws": [
            "California Commercial Code",
            "CCPA/CPRA (Privacy)",
            "California Labor Code"
        ],
        "key_considerations": [
            "Non-compete agreements are VOID (Section 16600)",
            "Strong employee protections",
            "CCPA applies to businesses meeting thresholds",
            "Tech industry standard jurisdiction"
        ],
        "detection_signals": ["california", "san francisco", "los angeles", "silicon valley", "ccpa"],
        "official_language": "English",
        "court_system": "Superior Court - Court of Appeal - Supreme Court of California"
    },
    "usa_texas": {
        "name": "USA (Texas)",
        "region": "USA",
        "sub_jurisdiction": "Texas",
        "primary_law": "Texas Business and Commerce Code",
        "additional_laws": [
            "Texas UCC",
            "Texas Natural Resources Code"
        ],
        "key_considerations": [
            "Oil & gas specific rules",
            "Generally employer-friendly",
            "Non-competes enforceable if reasonable",
            "No state income tax"
        ],
        "detection_signals": ["texas", "houston", "dallas", "austin", "texas law"],
        "official_language": "English",
        "court_system": "District Court - Court of Appeals - Supreme Court of Texas"
    },
    "usa_general": {
        "name": "USA (General)",
        "region": "USA",
        "sub_jurisdiction": "General",
        "primary_law": "Uniform Commercial Code (UCC)",
        "additional_laws": [
            "Restatement (Second) of Contracts",
            "Federal Arbitration Act"
        ],
        "key_considerations": [
            "Contract law is primarily STATE law",
            "UCC adopted in all 50 states with variations",
            "Consider where parties are located"
        ],
        "detection_signals": ["united states", "usa", "u.s.", "american"],
        "official_language": "English",
        "court_system": "Varies by state"
    },
    "eu_germany": {
        "name": "EU (Germany)",
        "region": "EU",
        "sub_jurisdiction": "Germany",
        "primary_law": "German Civil Code (BGB)",
        "additional_laws": [
            "German Commercial Code (HGB)",
            "GDPR (BDSG implementation)"
        ],
        "key_considerations": [
            "Standard terms subject to strict fairness review",
            "Good faith is fundamental principle",
            "GDPR applies",
            "No punitive damages"
        ],
        "detection_signals": ["germany", "german", "bgb", "berlin", "munich", "frankfurt"],
        "official_language": "German",
        "court_system": "Amtsgericht - Landgericht - OLG - BGH"
    },
    "eu_france": {
        "name": "EU (France)",
        "region": "EU",
        "sub_jurisdiction": "France",
        "primary_law": "French Civil Code (Code Civil)",
        "additional_laws": [
            "French Commercial Code",
            "GDPR (French implementation)"
        ],
        "key_considerations": [
            "Good faith required throughout contract lifecycle",
            "Unforeseen circumstances doctrine codified",
            "French language may be required for employment"
        ],
        "detection_signals": ["france", "french", "paris", "code civil", "lyon"],
        "official_language": "French",
        "court_system": "Tribunal Judiciaire - Cour d'appel - Cour de Cassation"
    },
    "eu_general": {
        "name": "EU (General)",
        "region": "EU",
        "sub_jurisdiction": "General",
        "primary_law": "Rome I Regulation",
        "additional_laws": [
            "GDPR",
            "EU AI Act",
            "Consumer Rights Directive"
        ],
        "key_considerations": [
            "Rome I determines applicable law",
            "GDPR applies regardless of choice of law",
            "Consumer protection cannot be contracted out"
        ],
        "detection_signals": ["european union", "eu law", "rome i", "gdpr", "brussels"],
        "official_language": "Varies by member state",
        "court_system": "National courts + CJEU"
    },
    "uk_england": {
        "name": "UK (England & Wales)",
        "region": "UK",
        "sub_jurisdiction": "England & Wales",
        "primary_law": "English Common Law",
        "additional_laws": [
            "Sale of Goods Act 1979",
            "UK GDPR",
            "Arbitration Act 1996"
        ],
        "key_considerations": [
            "Post-Brexit: UK GDPR separate from EU",
            "Most chosen governing law globally",
            "No general duty of good faith",
            "Consideration required"
        ],
        "detection_signals": ["england", "english law", "uk law", "london", "united kingdom"],
        "official_language": "English",
        "court_system": "High Court - Court of Appeal - Supreme Court"
    },
    "singapore": {
        "name": "Singapore",
        "region": "Asia-Pacific",
        "sub_jurisdiction": "Singapore",
        "primary_law": "Singapore Contract Law (common law)",
        "additional_laws": [
            "PDPA 2012",
            "Singapore International Arbitration Act"
        ],
        "key_considerations": [
            "English common law heritage",
            "SIAC globally recognized for arbitration",
            "Regional hub for Asia-Pacific"
        ],
        "detection_signals": ["singapore", "singaporean", "siac", "sgd"],
        "official_language": "English",
        "court_system": "State Courts - High Court - Court of Appeal"
    }
}

REGIONS = {
    "India": ["india_central"],
    "UAE": ["uae_mainland", "uae_difc", "uae_adgm"],
    "USA": ["usa_delaware", "usa_newyork", "usa_california", "usa_texas", "usa_general"],
    "European Union": ["eu_germany", "eu_france", "eu_general"],
    "United Kingdom": ["uk_england"],
    "Asia-Pacific": ["singapore"]
}

# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="DocuMind | Contract Analyzer",
    page_icon="DC",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CSS - ALL CONTRAST ISSUES FIXED
# =============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
    
    /* ===== GLOBAL ===== */
    .main {
        background-color: #f1f5f9 !important;
    }
    .main .block-container {
        padding: 1.5rem 2rem;
        background-color: #f1f5f9 !important;
    }
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;}
    
    /* ===== SIDEBAR ===== */
    section[data-testid="stSidebar"] {
        background: #0f172a !important;
    }
    section[data-testid="stSidebar"] > div {
        background: #0f172a !important;
    }
    
    /* Sidebar text */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] li,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {
        color: #cbd5e1 !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] strong {
        color: #f1f5f9 !important;
    }
    section[data-testid="stSidebar"] a {
        color: #60a5fa !important;
    }
    
    /* Sidebar dividers - make them subtle */
    section[data-testid="stSidebar"] hr {
        border-color: #334155 !important;
        margin: 0.75rem 0 !important;
    }
    
    /* ===== HEADER ===== */
    .main-header {
        background: #ffffff !important;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid #e2e8f0;
    }
    .main-header h1 {
        font-family: 'Playfair Display', serif;
        font-size: 1.75rem;
        color: #0f172a !important;
        margin: 0;
    }
    .main-header p {
        color: #475569 !important;
        margin: 0.25rem 0 0 0;
        font-size: 0.9rem;
    }
    .header-badge {
        display: inline-block;
        background: #1e293b;
        color: #ffffff !important;
        padding: 0.25rem 0.6rem;
        border-radius: 4px;
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-top: 0.5rem;
    }
    
    /* ===== SECTION HEADERS - FIXED: Now clearly visible ===== */
    .section-header {
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        font-weight: 600;
        color: #ffffff !important;
        background: transparent !important;
        margin: 1rem 0 0.5rem 0;
        padding-bottom: 0.25rem;
        border-bottom: 2px solid #3b82f6;
        display: inline-block;
    }
    
    /* ===== METRIC CARDS ===== */
    .metric-card {
        background: #ffffff !important;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .metric-value {
        font-family: 'Playfair Display', serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: #0f172a !important;
    }
    .metric-label {
        font-size: 0.7rem;
        color: #64748b !important;
        margin-top: 0.25rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
    }
    .metric-filename {
        font-size: 0.75rem;
        color: #334155 !important;
        margin-top: 0.25rem;
        word-break: break-all;
    }
    
    /* ===== CONTENT CARDS ===== */
    .content-card {
        background: #ffffff !important;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
    }
    .content-card p,
    .content-card li,
    .content-card span {
        color: #334155 !important;
        font-size: 0.9rem;
        line-height: 1.5;
    }
    .content-card strong {
        color: #0f172a !important;
    }
    
    /* ===== SIDEBAR BOXES ===== */
    .sidebar-status-box {
        padding: 0.6rem 0.8rem;
        border-radius: 6px;
        text-align: center;
        margin: 0.5rem 0;
    }
    .sidebar-status-box p {
        margin: 0;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .sidebar-status-success {
        background: #166534 !important;
    }
    .sidebar-status-success p {
        color: #ffffff !important;
    }
    .sidebar-status-error {
        background: #991b1b !important;
    }
    .sidebar-status-error p {
        color: #ffffff !important;
    }
    
    .sidebar-jurisdiction-box {
        background: #1e3a5f !important;
        border-left: 3px solid #3b82f6;
        padding: 0.75rem;
        border-radius: 0 6px 6px 0;
        margin: 0.5rem 0;
    }
    .sidebar-jurisdiction-box p {
        color: #bfdbfe !important;
        margin: 0.1rem 0;
        font-size: 0.8rem;
    }
    .sidebar-jurisdiction-box strong {
        color: #ffffff !important;
    }
    
    /* ===== MAIN AREA INFO BOXES ===== */
    .info-box-light {
        background: #eff6ff !important;
        border-left: 3px solid #3b82f6;
        padding: 0.75rem;
        border-radius: 0 6px 6px 0;
        margin: 0.5rem 0;
    }
    .info-box-light p,
    .info-box-light span {
        color: #1e40af !important;
        font-size: 0.85rem;
    }
    .info-box-light strong {
        color: #1e3a8a !important;
    }
    
    .detection-box {
        background: #f0fdf4 !important;
        border: 1px solid #86efac;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.75rem 0;
    }
    .detection-box p,
    .detection-box span,
    .detection-box li {
        color: #166534 !important;
    }
    .detection-box strong {
        color: #14532d !important;
    }
    
    /* ===== ALERT BOXES ===== */
    .red-flag {
        background: #fef2f2 !important;
        border-left: 3px solid #dc2626;
        padding: 0.6rem 0.8rem;
        margin: 0.3rem 0;
        border-radius: 0 6px 6px 0;
    }
    .red-flag p {
        color: #991b1b !important;
        margin: 0;
        font-size: 0.85rem;
    }
    
    .recommendation-box {
        background: #f0fdf4 !important;
        border-left: 3px solid #16a34a;
        padding: 0.6rem 0.8rem;
        margin: 0.3rem 0;
        border-radius: 0 6px 6px 0;
    }
    .recommendation-box p {
        color: #166534 !important;
        margin: 0;
        font-size: 0.85rem;
    }
    
    /* ===== RISK BADGES ===== */
    .risk-critical { background: #dc2626 !important; color: #fff !important; padding: 0.3rem 0.7rem; border-radius: 4px; font-weight: 600; font-size: 0.75rem; }
    .risk-high { background: #ea580c !important; color: #fff !important; padding: 0.3rem 0.7rem; border-radius: 4px; font-weight: 600; font-size: 0.75rem; }
    .risk-medium { background: #ca8a04 !important; color: #fff !important; padding: 0.3rem 0.7rem; border-radius: 4px; font-weight: 600; font-size: 0.75rem; }
    .risk-low { background: #16a34a !important; color: #fff !important; padding: 0.3rem 0.7rem; border-radius: 4px; font-weight: 600; font-size: 0.75rem; }
    .risk-standard { background: #2563eb !important; color: #fff !important; padding: 0.3rem 0.7rem; border-radius: 4px; font-weight: 600; font-size: 0.75rem; }
    
    /* ===== STEP INDICATORS ===== */
    .step-item {
        text-align: center;
        padding: 0.75rem;
        background: #ffffff !important;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
    }
    .step-number {
        width: 28px;
        height: 28px;
        background: #1e293b !important;
        color: #ffffff !important;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.8rem;
        margin-bottom: 0.3rem;
    }
    .step-title {
        color: #0f172a !important;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .step-desc {
        color: #64748b !important;
        font-size: 0.7rem;
    }
    
    /* ===== FOOTER ===== */
    .footer {
        background: #0f172a !important;
        padding: 1rem;
        border-radius: 8px;
        margin-top: 1.5rem;
        text-align: center;
    }
    .footer p {
        color: #cbd5e1 !important;
        font-size: 0.8rem;
        margin: 0.15rem 0;
    }
    .footer a {
        color: #60a5fa !important;
    }
    .footer strong {
        color: #f1f5f9 !important;
    }
    
    /* ===== BUTTONS ===== */
    .stButton > button {
        background: #1e293b !important;
        color: #ffffff !important;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .stButton > button:hover {
        background: #334155 !important;
    }
    
    /* ===== STREAMLIT COMPONENT OVERRIDES ===== */
    
    /* File uploader - FIXED */
    [data-testid="stFileUploader"] {
        background: #ffffff !important;
        border: 2px dashed #cbd5e1 !important;
        border-radius: 8px;
        padding: 0.5rem;
    }
    [data-testid="stFileUploader"] label,
    [data-testid="stFileUploader"] p,
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] small,
    [data-testid="stFileUploader"] div {
        color: #475569 !important;
    }
    [data-testid="stFileUploader"] button {
        background: #f1f5f9 !important;
        color: #334155 !important;
        border: 1px solid #cbd5e1 !important;
    }
    /* File name in uploader */
    [data-testid="stFileUploader"] [data-testid="stMarkdownContainer"] p {
        color: #1e293b !important;
    }
    
    /* Checkboxes */
    .stCheckbox label span {
        color: #334155 !important;
    }
    
    /* Selectbox */
    .stSelectbox label {
        color: #334155 !important;
    }
    .stSelectbox > div > div {
        background: #ffffff !important;
        color: #1e293b !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: #e2e8f0;
        padding: 0.2rem;
        border-radius: 6px;
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #475569 !important;
        font-size: 0.8rem;
        padding: 0.4rem 0.8rem;
        border-radius: 4px;
    }
    .stTabs [aria-selected="true"] {
        background: #ffffff !important;
        color: #0f172a !important;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: #ffffff !important;
        color: #0f172a !important;
        font-size: 0.85rem;
    }
    .streamlit-expanderContent {
        background: #ffffff !important;
    }
    .streamlit-expanderContent p,
    .streamlit-expanderContent li,
    .streamlit-expanderContent span {
        color: #334155 !important;
    }
    
    /* Text area */
    .stTextArea textarea {
        background: #ffffff !important;
        color: #1e293b !important;
        border: 1px solid #e2e8f0 !important;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #0f172a !important;
    }
    [data-testid="stMetricLabel"] {
        color: #64748b !important;
    }
    
    /* Info/Warning boxes */
    .stAlert {
        background: #ffffff !important;
    }
    .stAlert p {
        color: #334155 !important;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background: #3b82f6 !important;
    }
    
    /* Divider */
    .custom-divider {
        height: 1px;
        background: #e2e8f0;
        margin: 0.75rem 0;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# SESSION STATE
# =============================================================================

if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = None
if 'processing_info' not in st.session_state:
    st.session_state.processing_info = None
if 'detected_jurisdiction' not in st.session_state:
    st.session_state.detected_jurisdiction = None
if 'selected_jurisdiction' not in st.session_state:
    st.session_state.selected_jurisdiction = None

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def detect_jurisdiction(text: str) -> dict:
    """Auto-detect jurisdiction from contract text."""
    text_lower = text.lower()
    results = {}
    
    for jur_key, jur_data in JURISDICTIONS.items():
        score = 0
        signals_found = []
        
        for signal in jur_data.get("detection_signals", []):
            if signal.lower() in text_lower:
                score += 10
                signals_found.append(signal)
        
        for neg_signal in jur_data.get("negative_signals", []):
            if neg_signal.lower() in text_lower:
                score -= 20
        
        if score > 0:
            results[jur_key] = {"score": score, "signals": signals_found}
    
    sorted_results = sorted(results.items(), key=lambda x: x[1]["score"], reverse=True)
    
    if sorted_results:
        top_key, top_data = sorted_results[0]
        return {
            "detected": True,
            "top_match": top_key,
            "signals": top_data["signals"][:3],
            "alternatives": [k for k, v in sorted_results[1:3]]
        }
    return {"detected": False}


def get_risk_html(risk_level):
    class_map = {
        RiskLevel.CRITICAL: "risk-critical",
        RiskLevel.HIGH: "risk-high",
        RiskLevel.MEDIUM: "risk-medium",
        RiskLevel.LOW: "risk-low",
        RiskLevel.STANDARD: "risk-standard"
    }
    label_map = {
        RiskLevel.CRITICAL: "CRITICAL",
        RiskLevel.HIGH: "HIGH",
        RiskLevel.MEDIUM: "MEDIUM",
        RiskLevel.LOW: "LOW",
        RiskLevel.STANDARD: "STANDARD"
    }
    return f'<span class="{class_map.get(risk_level, "risk-medium")}">{label_map.get(risk_level, "?")}</span>'


def reset_analysis():
    st.session_state.analysis_complete = False
    st.session_state.analysis_result = None
    st.session_state.extracted_text = None
    st.session_state.processing_info = None
    st.session_state.detected_jurisdiction = None
    st.session_state.selected_jurisdiction = None


def check_api_keys():
    """Check available API keys and return provider priority."""
    groq_key = os.getenv("GROQ_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    
    available = []
    if groq_key and groq_key != "your_groq_api_key_here":
        available.append("groq")
    if google_key and google_key != "your_google_api_key_here":
        available.append("gemini")
    
    if available:
        return True, available[0], available
    return False, None, []


def render_footer():
    st.markdown("""
    <div class="footer">
        <p><strong>DocuMind Contract Analyzer</strong></p>
        <p>Made by <strong>Kashika Wanchoo</strong></p>
        <p><a href="mailto:kashikaaw@gmail.com">kashikaaw@gmail.com</a></p>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# MAIN APP
# =============================================================================

def main():
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 0.5rem 0 0.75rem 0;">
            <h1 style="font-family: 'Playfair Display', serif; font-size: 1.3rem; margin: 0; color: #f1f5f9 !important;">DocuMind</h1>
            <p style="color: #94a3b8 !important; font-size: 0.75rem; margin: 0.1rem 0 0 0;">AI Contract Analyzer</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # API Status
        api_ready, primary_provider, all_providers = check_api_keys()
        if api_ready:
            providers_text = " + ".join([p.upper() for p in all_providers])
            st.markdown(f"""
            <div class="sidebar-status-box sidebar-status-success">
                <p>Connected to {providers_text}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="sidebar-status-box sidebar-status-error">
                <p>API Key Required</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Active Jurisdiction
        if st.session_state.selected_jurisdiction:
            jur = JURISDICTIONS.get(st.session_state.selected_jurisdiction, {})
            st.markdown("### Active Jurisdiction")
            st.markdown(f"""
            <div class="sidebar-jurisdiction-box">
                <p><strong>{jur.get('name', '')}</strong></p>
                <p>{jur.get('primary_law', '')}</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("---")
        
        # New Analysis button
        if st.session_state.analysis_complete:
            if st.button("New Analysis", use_container_width=True):
                reset_analysis()
                st.rerun()
            st.markdown("---")
        
        # Capabilities
        st.markdown("### Capabilities")
        st.markdown("""
- Smart jurisdiction detection
- Multi-format documents
- AI clause extraction
- Risk scoring (1-10)
- Legal framework mapping
- Negotiation guidance
        """)
        
        st.markdown("---")
        
        # Supported Regions
        st.markdown("### Supported Regions")
        st.markdown("""
- India (Central Law)
- UAE (Mainland/DIFC/ADGM)
- USA (DE/NY/CA/TX)
- EU (DE/FR/General)
- UK, Singapore
        """)
        
        st.markdown("---")
        
        # Creator
        st.markdown("""
        <div style="text-align: center;">
            <p style="font-size: 0.7rem; color: #94a3b8 !important; margin: 0;">Made by</p>
            <p style="font-size: 0.8rem; color: #f1f5f9 !important; margin: 0.1rem 0;"><strong>Kashika Wanchoo</strong></p>
            <p style="margin: 0;"><a href="mailto:kashikaaw@gmail.com" style="color: #60a5fa !important; font-size: 0.7rem;">kashikaaw@gmail.com</a></p>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content
    if not st.session_state.analysis_complete:
        render_upload_page(api_ready, primary_provider, all_providers)
    else:
        render_results_page()


def render_upload_page(api_ready, primary_provider, all_providers):
    """Upload page."""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>DocuMind Contract Analyzer</h1>
        <p>AI-powered analysis with smart jurisdiction detection</p>
        <span class="header-badge">Vision AI + Legal Framework Mapping</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Steps
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="step-item"><div class="step-number">1</div><div class="step-title">Upload</div><div class="step-desc">Any format</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="step-item"><div class="step-number">2</div><div class="step-title">Detect</div><div class="step-desc">Jurisdiction</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="step-item"><div class="step-number">3</div><div class="step-title">Analyze</div><div class="step-desc">AI Review</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="step-item"><div class="step-number">4</div><div class="step-title">Report</div><div class="step-desc">Insights</div></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    
    # Upload section
    st.markdown('<p class="section-header">Upload Contract</p>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Supported: PDF, PNG, JPG, TIFF (including scans)",
        type=['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp', 'webp']
    )
    
    if uploaded_file:
        # File info cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fname = uploaded_file.name
            display_name = fname[:25] + "..." if len(fname) > 25 else fname
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">FILE</div>
                <div class="metric-filename">{display_name}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            size_mb = uploaded_file.size / (1024 * 1024)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{size_mb:.2f}</div>
                <div class="metric-label">SIZE (MB)</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            file_type = uploaded_file.type.split('/')[-1].upper()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{file_type}</div>
                <div class="metric-label">FORMAT</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        
        # Options
        st.markdown('<p class="section-header">Options</p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            use_vision = st.checkbox("Use Vision AI", value=True, help="Better for scans")
        with col2:
            auto_detect = st.checkbox("Auto-detect jurisdiction", value=True)
        
        # Manual jurisdiction selection if auto-detect disabled
        if not auto_detect:
            st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
            st.markdown('<p class="section-header">Select Jurisdiction</p>', unsafe_allow_html=True)
            
            region = st.selectbox("Region", list(REGIONS.keys()))
            sub_options = REGIONS[region]
            sub_labels = [JURISDICTIONS[k]["name"] for k in sub_options]
            selected_idx = st.selectbox("Specific Jurisdiction", range(len(sub_options)), format_func=lambda i: sub_labels[i])
            manual_jurisdiction = sub_options[selected_idx]
            
            jur_data = JURISDICTIONS[manual_jurisdiction]
            st.markdown(f"""
            <div class="info-box-light">
                <p><strong>{jur_data['name']}</strong></p>
                <p><strong>Primary Law:</strong> {jur_data['primary_law']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.session_state.selected_jurisdiction = manual_jurisdiction
        
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        
        # Analyze button
        if api_ready:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Analyze Contract", use_container_width=True):
                    process_and_analyze(uploaded_file, primary_provider, all_providers, use_vision, auto_detect)
        else:
            st.warning("Please add API key to .env file (GROQ_API_KEY or GOOGLE_API_KEY)")
    
    else:
        # Features when no file
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        st.markdown('<p class="section-header">How It Works</p>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div class="content-card">
                <p><strong>Smart Detection</strong></p>
                <p>Upload your contract and we auto-detect the jurisdiction from addresses, governing law clauses, and other signals.</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div class="content-card">
                <p><strong>Legal Accuracy</strong></p>
                <p>Not just "USA" but Delaware vs California. Not just "UAE" but Mainland vs DIFC. Real legal distinctions.</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div class="content-card">
                <p><strong>Risk Analysis</strong></p>
                <p>Each clause scored 1-10 with reasoning, red flags, market benchmarks, and negotiation guidance.</p>
            </div>
            """, unsafe_allow_html=True)
    
    render_footer()


def process_and_analyze(uploaded_file, primary_provider, all_providers, use_vision, auto_detect):
    """Process document and analyze with rate limit handling."""
    
    progress = st.progress(0)
    status = st.empty()
    
    try:
        status.info("Reading document...")
        progress.progress(10)
        
        file_bytes = uploaded_file.read()
        filename = uploaded_file.name
        
        status.info("Extracting text...")
        progress.progress(25)
        
        vision_extractor = None
        if use_vision:
            try:
                vision_extractor = VisionExtractor(provider="gemini", api_key=os.getenv("GOOGLE_API_KEY"))
            except:
                pass
        
        processor = DocumentProcessor(vision_extractor=vision_extractor)
        processed_doc = processor.process(file_bytes=file_bytes, filename=filename)
        st.session_state.extracted_text = processed_doc.full_text
        
        progress.progress(40)
        
        # Jurisdiction detection
        if auto_detect and not st.session_state.selected_jurisdiction:
            status.info("Detecting jurisdiction...")
            detection = detect_jurisdiction(processed_doc.full_text)
            st.session_state.detected_jurisdiction = detection
            if detection.get("detected"):
                st.session_state.selected_jurisdiction = detection["top_match"]
        
        if not st.session_state.selected_jurisdiction:
            st.session_state.selected_jurisdiction = "india_central"
        
        jurisdiction_key = st.session_state.selected_jurisdiction
        
        progress.progress(50)
        
        # Analyze with fallback for rate limits
        status.info("Analyzing with AI...")
        progress.progress(60)
        
        analysis = None
        last_error = None
        
        # Try each available provider
        for provider in all_providers:
            try:
                api_key = os.getenv("GROQ_API_KEY") if provider == "groq" else os.getenv("GOOGLE_API_KEY")
                llm = ContractLLM(provider=provider, api_key=api_key)
                analyzer = ContractAnalyzer(llm=llm)
                analysis = analyzer.analyze(processed_doc.full_text)
                break  # Success, exit loop
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                if "rate limit" in error_str or "429" in error_str:
                    status.warning(f"{provider.upper()} rate limit hit. Trying alternative...")
                    continue
                else:
                    raise e
        
        if analysis is None:
            if last_error:
                # Show friendly rate limit message
                if "rate limit" in str(last_error).lower() or "429" in str(last_error):
                    status.error("All API providers have hit rate limits. Please try again in 30 minutes or add another API key.")
                    st.info("""
                    **Rate Limit Solutions:**
                    1. Wait 30 minutes and try again
                    2. Add Google API key (free): https://aistudio.google.com/app/apikey
                    3. Add Groq API key (free): https://console.groq.com
                    
                    Having both keys allows automatic fallback when one is exhausted.
                    """)
                    return
                else:
                    raise last_error
        
        progress.progress(90)
        
        # Store results
        st.session_state.processing_info = {
            "filename": processed_doc.filename,
            "type": processed_doc.document_type.value,
            "pages": processed_doc.total_pages,
            "confidence": processed_doc.average_confidence,
            "notes": processed_doc.processing_notes,
            "jurisdiction": jurisdiction_key
        }
        
        st.session_state.analysis_result = analysis
        st.session_state.analysis_complete = True
        
        status.success("Analysis complete!")
        progress.progress(100)
        
        st.rerun()
        
    except Exception as e:
        error_str = str(e)
        if "rate limit" in error_str.lower() or "429" in error_str:
            status.error("Rate limit reached. Please wait and try again.")
            st.info("""
            **What happened:** The free API has a daily token limit.
            
            **Solutions:**
            1. Wait 30 minutes and try again
            2. Add a second API key for automatic fallback
            3. Try a shorter document
            """)
        else:
            status.error(f"Error: {error_str}")
            st.exception(e)


def render_results_page():
    """Results page."""
    
    analysis = st.session_state.analysis_result
    info = st.session_state.processing_info
    jurisdiction_key = info.get('jurisdiction', 'india_central')
    jur_data = JURISDICTIONS.get(jurisdiction_key, {})
    detection = st.session_state.detected_jurisdiction
    
    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1>Analysis Report</h1>
        <p>{info['filename']} | {jur_data.get('name', '')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Detection info
    if detection and detection.get("detected"):
        signals = ", ".join(detection.get("signals", []))
        st.markdown(f"""
        <div class="detection-box">
            <p><strong>Jurisdiction Detected: {jur_data.get('name', '')}</strong></p>
            <p>Signals found: {signals}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{analysis.overall_risk_score}/10</div><div class="metric-label">Risk Score</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{len(analysis.clauses)}</div><div class="metric-label">Clauses</div></div>', unsafe_allow_html=True)
    with col3:
        high_risk = len([a for a in analysis.risk_assessments if a.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]])
        st.markdown(f'<div class="metric-card"><div class="metric-value">{high_risk}</div><div class="metric-label">High Risk</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{len(analysis.key_concerns)}</div><div class="metric-label">Red Flags</div></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    
    # Risk badge
    st.markdown(f'<div style="text-align: center;">{get_risk_html(analysis.overall_risk_level)}</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Summary", "Legal Framework", "Risks", "Negotiate", "Full Text"])
    
    with tab1:
        render_summary(analysis, jur_data)
    with tab2:
        render_legal_framework(jur_data)
    with tab3:
        render_risks(analysis)
    with tab4:
        render_negotiation(analysis)
    with tab5:
        render_text()
    
    # Export
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("Download JSON", json.dumps(analysis_to_dict(analysis), indent=2), f"analysis_{datetime.now().strftime('%Y%m%d')}.json", "application/json", use_container_width=True)
    with col2:
        st.download_button("Download Report", generate_report(analysis, jur_data), f"report_{datetime.now().strftime('%Y%m%d')}.md", "text/markdown", use_container_width=True)
    
    render_footer()


def render_summary(analysis, jur_data):
    st.markdown('<p class="section-header">Contract Overview</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="content-card">
            <p><strong>Type:</strong> {analysis.metadata.contract_type}</p>
            <p><strong>Parties:</strong> {', '.join(analysis.metadata.parties) if analysis.metadata.parties else 'Not identified'}</p>
            <p><strong>Effective:</strong> {analysis.metadata.effective_date or 'Not specified'}</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="content-card">
            <p><strong>Expires:</strong> {analysis.metadata.expiration_date or 'Not specified'}</p>
            <p><strong>Value:</strong> {analysis.metadata.total_value or 'Not specified'}</p>
            <p><strong>Governing Law:</strong> {analysis.metadata.governing_law or jur_data.get('primary_law', 'Not specified')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<p class="section-header">Executive Summary</p>', unsafe_allow_html=True)
    st.markdown(f'<div class="content-card"><p>{analysis.executive_summary}</p></div>', unsafe_allow_html=True)
    
    if analysis.key_concerns:
        st.markdown('<p class="section-header">Key Concerns</p>', unsafe_allow_html=True)
        for concern in analysis.key_concerns:
            st.markdown(f'<div class="red-flag"><p>{concern}</p></div>', unsafe_allow_html=True)


def render_legal_framework(jur_data):
    st.markdown(f'<p class="section-header">Applicable Law: {jur_data.get("name", "")}</p>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="content-card">
        <p><strong>Primary Law:</strong> {jur_data.get('primary_law', '')}</p>
        <p><strong>Official Language:</strong> {jur_data.get('official_language', '')}</p>
        <p><strong>Court System:</strong> {jur_data.get('court_system', '')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<p class="section-header">Additional Regulations</p>', unsafe_allow_html=True)
    laws_html = "".join([f"<li>{law}</li>" for law in jur_data.get('additional_laws', [])])
    st.markdown(f'<div class="content-card"><ul>{laws_html}</ul></div>', unsafe_allow_html=True)
    
    st.markdown('<p class="section-header">Key Considerations</p>', unsafe_allow_html=True)
    for item in jur_data.get('key_considerations', []):
        st.markdown(f'<div class="recommendation-box"><p>{item}</p></div>', unsafe_allow_html=True)


def render_risks(analysis):
    st.markdown('<p class="section-header">Risk Assessment</p>', unsafe_allow_html=True)
    
    for assessment in sorted(analysis.risk_assessments, key=lambda x: x.risk_score, reverse=True):
        with st.expander(f"{assessment.clause_type.value.replace('_', ' ').title()} - {assessment.risk_score}/10"):
            st.markdown(get_risk_html(assessment.risk_level), unsafe_allow_html=True)
            st.markdown("**Findings:**")
            for f in assessment.findings:
                st.markdown(f"- {f}")
            if assessment.red_flags:
                for flag in assessment.red_flags:
                    st.markdown(f'<div class="red-flag"><p>{flag}</p></div>', unsafe_allow_html=True)
            st.info(f"**Benchmark:** {assessment.market_comparison}")
            if assessment.recommendations:
                for rec in assessment.recommendations:
                    st.markdown(f'<div class="recommendation-box"><p>{rec}</p></div>', unsafe_allow_html=True)


def render_negotiation(analysis):
    st.markdown('<p class="section-header">Negotiation Points</p>', unsafe_allow_html=True)
    
    if not analysis.negotiation_points:
        st.info("No significant negotiation points identified.")
        return
    
    for i, point in enumerate(analysis.negotiation_points, 1):
        with st.expander(f"Priority {i}: {point['clause'].replace('_', ' ').title()}"):
            st.markdown(f"**Issue:** {point['issue']}")
            st.markdown(f"**Recommendation:** {point['recommendation']}")
            st.info(f"**Suggested Language:** {point['suggested_language']}")


def render_text():
    st.markdown('<p class="section-header">Extracted Text</p>', unsafe_allow_html=True)
    
    info = st.session_state.processing_info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Type", info['type'].replace('_', ' ').title())
    with col2:
        st.metric("Pages", info['pages'])
    with col3:
        st.metric("Confidence", f"{info['confidence']:.0%}")
    
    st.text_area("", st.session_state.extracted_text, height=300, label_visibility="collapsed")


def generate_report(analysis, jur_data):
    return f"""# Contract Analysis Report

**Generated:** {analysis.analysis_timestamp}
**Jurisdiction:** {jur_data.get('name', '')}
**Primary Law:** {jur_data.get('primary_law', '')}
**Risk Score:** {analysis.overall_risk_score}/10

## Executive Summary
{analysis.executive_summary}

## Key Concerns
{chr(10).join(['- ' + c for c in analysis.key_concerns])}

## Legal Framework
**Primary Law:** {jur_data.get('primary_law', '')}
**Additional:** {', '.join(jur_data.get('additional_laws', []))}

---
*Made by Kashika Wanchoo | kashikaaw@gmail.com*
"""


if __name__ == "__main__":
    main()
