"""
Academic Survey Email Distribution Engine
==========================================
Powered by Amazon SES SMTP | Built with Streamlit
Author-facing single-file application — app.py

Deployment notes
----------------
* Place credentials in .streamlit/secrets.toml (see template).
* Install dependencies:  pip install -r requirements.txt
* Launch:                streamlit run app.py
"""

# ---------------------------------------------------------------------------
# Standard-library imports
# ---------------------------------------------------------------------------
import re
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ---------------------------------------------------------------------------
# Third-party imports
# ---------------------------------------------------------------------------
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from rapidfuzz import fuzz, process

# ===========================================================================
# PAGE CONFIGURATION
# ===========================================================================
st.set_page_config(
    page_title="SOS Survey",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ===========================================================================
# GLOBAL CONSTANTS
# ===========================================================================

EMAIL_SUBJECT = (
    "Invitation to Participate in a Research Survey — "
    "Research Productivity and Determining Factors"
)

HTML_TEMPLATE = """\
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333333;">
    <p>Dear {name},</p>
    <p>We trust this email finds you well.</p>
    <p>We are contacting you because you were listed as the corresponding author
    for a Scopus-indexed paper published between 2019-2023. We would like to invite
    you to participate in a short, formal survey for a research thesis titled
    <strong>&ldquo;Research Productivity and Determining Factors.&rdquo;</strong></p>
    <p>This study aims to provide an in-depth exploration of the individual and
    institutional characteristics of Scholars and Academics in Nigerian institutions,
    and how these factors independently and collectively influence academic productivity
    and visibility.</p>
    <p><strong>Why participate?</strong><br>
    If you decide to participate, you will only be asked to provide basic demographic
    information about yourself and your institution. The entire process takes just
    3 to 5 minutes.</p>
    <p>Rest assured, all information collected is securely hosted, treated with full
    confidentiality, and will be aggregated solely for academic analysis.</p>
    <p>We truly appreciate your time and consideration in enhancing the understanding
    of research productivity in our institutions.</p>

    <p style="margin: 25px 0;">
        <a href="https://tally.so/r/wMv4Xy?email={email}"
           style="background-color: #007bff; color: white; padding: 12px 25px;
                  text-decoration: none; border-radius: 5px;
                  display: inline-block; font-weight: bold;">
            Participate in the Study
        </a>
    </p>

    <p>Best regards,</p>
    <p><strong>Toluwase Asubiaro</strong><br>
    African Research Visibility Initiative, Calgary, Canada |
    toluwase.asubiaro@africarvi.org<br>
    Department of Information Science, University of South Africa |
    tasubiar@uwo.ca</p>
    <p><em>and</em></p>
    <p><strong>Oladotun Oguntola</strong><br>
    Department of Data and Information Science, University of Ibadan |
    +2348167681837</p>
    <hr style="border: 0; border-top: 1px solid #eeeeee; margin-top: 30px;">
    <p style="font-size: 11px; color: #666666;">Participation is strictly voluntary.
    If you prefer not to participate or receive further communications regarding this
    study, kindly reply with &ldquo;not interested&rdquo; and your email will be
    permanently removed from our outreach list.</p>
</body>
</html>
"""

# Email regex used for sample-based column detection
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

BATCH_OPTIONS = [10, 100, 1000, 5000, 10_000, "Full Dataset"]

# ===========================================================================
# CUSTOM CSS — Modern SaaS UI (Tally.so / Qualtrics inspired)
# ===========================================================================

CUSTOM_CSS = """
<style>
/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   GOOGLE FONTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   DESIGN TOKENS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
:root {
    --bg-page:        #F4F6FA;
    --bg-card:        #FFFFFF;
    --bg-card-alt:    #F8F9FC;
    --border:         #E5E8EF;
    --border-focus:   #4F46E5;

    --primary:        #4F46E5;   /* indigo — Tally-style */
    --primary-hover:  #4338CA;
    --primary-light:  #EEF2FF;
    --primary-text:   #4F46E5;

    --success:        #059669;
    --success-light:  #ECFDF5;
    --warning:        #D97706;
    --warning-light:  #FFFBEB;
    --danger:         #DC2626;
    --danger-light:   #FEF2F2;

    --text-primary:   #111827;
    --text-secondary: #6B7280;
    --text-muted:     #9CA3AF;

    --radius-sm:   6px;
    --radius-md:   10px;
    --radius-lg:   14px;
    --radius-xl:   18px;

    --shadow-xs:   0 1px 2px rgba(0,0,0,.05);
    --shadow-sm:   0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.06);
    --shadow-md:   0 4px 6px rgba(0,0,0,.07), 0 2px 4px rgba(0,0,0,.06);
    --shadow-lg:   0 10px 15px rgba(0,0,0,.07), 0 4px 6px rgba(0,0,0,.05);
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   GLOBAL RESET & BASE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    -webkit-font-smoothing: antialiased;
    color: var(--text-primary);
}

/* Page background */
.stApp {
    background-color: var(--bg-page) !important;
}

/* Hide Streamlit's default top decoration bar */
[data-testid="stDecoration"] { display: none !important; }

/* Remove default header padding */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 4rem !important;
    max-width: 900px !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg-page); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: #CBD5E1; }

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   HERO / TOP BANNER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
.hero-block {
    background: linear-gradient(135deg, #4F46E5 0%, #6366F1 50%, #818CF8 100%);
    border-radius: var(--radius-xl);
    padding: 36px 44px;
    margin-bottom: 28px;
    box-shadow: 0 8px 30px rgba(79,70,229,0.30);
    position: relative;
    overflow: hidden;
}
.hero-block::before {
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 220px; height: 220px;
    border-radius: 50%;
    background: rgba(255,255,255,0.07);
    pointer-events: none;
}
.hero-block::after {
    content: '';
    position: absolute;
    bottom: -60px; left: -20px;
    width: 180px; height: 180px;
    border-radius: 50%;
    background: rgba(255,255,255,0.05);
    pointer-events: none;
}
.hero-block h1 {
    margin: 0 0 8px 0;
    font-size: 1.85rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.6px;
    line-height: 1.2;
}
.hero-block p {
    margin: 0;
    font-size: 0.92rem;
    color: rgba(255,255,255,0.80);
    font-weight: 400;
    letter-spacing: 0.1px;
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   SECTION CARDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
.section-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 28px 32px;
    margin-bottom: 20px;
    box-shadow: var(--shadow-sm);
    transition: box-shadow 0.2s ease;
}
.section-card:hover {
    box-shadow: var(--shadow-md);
}
.section-title {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.78rem;
    font-weight: 700;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.9px;
    margin: 0 0 20px 0;
    padding-bottom: 14px;
    border-bottom: 1px solid var(--border);
}
.section-title span {
    font-size: 1rem;
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   AUTO-DETECT CHIPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
.detect-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--primary-light);
    color: var(--primary-text);
    border: 1px solid #C7D2FE;
    border-radius: 99px;
    padding: 5px 14px;
    font-size: 0.8rem;
    font-weight: 500;
    margin: 4px 6px 4px 0;
    letter-spacing: 0.1px;
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   INFO / ALERT BOX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
.info-box {
    background: var(--primary-light);
    border: 1px solid #C7D2FE;
    border-left: 4px solid var(--primary);
    border-radius: var(--radius-md);
    padding: 14px 18px;
    color: #3730A3;
    font-size: 0.88rem;
    margin-top: 14px;
    line-height: 1.5;
}
.info-box strong { color: var(--primary); }

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   METRIC TILES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
.metric-row { display: flex; gap: 14px; flex-wrap: wrap; margin: 16px 0; }
.metric-tile {
    flex: 1;
    min-width: 130px;
    background: var(--bg-card-alt);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 18px 20px;
    text-align: center;
    transition: box-shadow 0.15s ease;
}
.metric-tile:hover { box-shadow: var(--shadow-sm); }
.metric-tile .value {
    font-size: 1.7rem;
    font-weight: 800;
    color: var(--primary);
    line-height: 1;
    margin-bottom: 5px;
    letter-spacing: -0.5px;
}
.metric-tile .label {
    font-size: 0.72rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    font-weight: 600;
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   BADGES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 99px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.3px;
}
.badge-blue  { background: var(--primary-light); color: var(--primary); border: 1px solid #C7D2FE; }
.badge-green { background: var(--success-light); color: var(--success); border: 1px solid #A7F3D0; }
.badge-amber { background: var(--warning-light); color: var(--warning); border: 1px solid #FDE68A; }
.badge-red   { background: var(--danger-light);  color: var(--danger);  border: 1px solid #FECACA; }

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   STREAMLIT WIDGET OVERRIDES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/* ── Labels ── */
div[data-testid="stSelectbox"] label,
div[data-testid="stTextArea"] label,
div[data-testid="stFileUploadDropzone"] label {
    color: var(--text-primary) !important;
    font-size: 0.875rem !important;
    font-weight: 600 !important;
    margin-bottom: 4px !important;
}

/* ── Selectbox ── */
div[data-testid="stSelectbox"] > div > div {
    background: #fff !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-xs) !important;
    font-size: 0.875rem !important;
    color: var(--text-primary) !important;
    transition: border-color 0.15s ease !important;
}
div[data-testid="stSelectbox"] > div > div:focus-within {
    border-color: var(--border-focus) !important;
    box-shadow: 0 0 0 3px rgba(79,70,229,0.12) !important;
}

/* ── Text area ── */
textarea {
    background: #fff !important;
    border: 1.5px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    font-size: 0.84rem !important;
    font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace !important;
    color: var(--text-primary) !important;
    transition: border-color 0.15s ease !important;
    line-height: 1.6 !important;
}
textarea:focus {
    border-color: var(--border-focus) !important;
    box-shadow: 0 0 0 3px rgba(79,70,229,0.10) !important;
    outline: none !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: #fff !important;
    border: 2px dashed var(--border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 8px !important;
    transition: border-color 0.2s ease, background 0.2s ease !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--primary) !important;
    background: var(--primary-light) !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] span {
    color: var(--text-secondary) !important;
    font-size: 0.875rem !important;
}

/* ── Dataframe ── */
.stDataFrame {
    border-radius: var(--radius-md) !important;
    overflow: hidden !important;
    border: 1px solid var(--border) !important;
    box-shadow: var(--shadow-xs) !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: var(--bg-card-alt) !important;
    border-radius: var(--radius-md) !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid var(--border) !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: var(--radius-sm) !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    color: var(--text-secondary) !important;
    padding: 7px 18px !important;
    transition: all 0.15s ease !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: #fff !important;
    color: var(--primary) !important;
    font-weight: 600 !important;
    box-shadow: var(--shadow-xs) !important;
}

/* ── Progress bar ── */
[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, var(--primary), #818CF8) !important;
    border-radius: 99px !important;
}
[data-testid="stProgressBar"] > div {
    background: var(--border) !important;
    border-radius: 99px !important;
}

/* ── Buttons ── */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    border-radius: var(--radius-md) !important;
    padding: 10px 22px !important;
    transition: all 0.18s ease !important;
    cursor: pointer !important;
    letter-spacing: 0.1px !important;
    width: 100%;
}
/* Primary button */
.stButton > button[kind="primary"] {
    background: var(--primary) !important;
    color: #fff !important;
    border: none !important;
    box-shadow: 0 2px 8px rgba(79,70,229,0.30) !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--primary-hover) !important;
    box-shadow: 0 4px 16px rgba(79,70,229,0.40) !important;
    transform: translateY(-1px) !important;
}
/* Secondary button */
.stButton > button[kind="secondary"] {
    background: #fff !important;
    color: var(--primary) !important;
    border: 1.5px solid var(--primary) !important;
}
.stButton > button[kind="secondary"]:hover {
    background: var(--primary-light) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 2px 10px rgba(79,70,229,0.15) !important;
}
.stButton > button:active {
    transform: translateY(0px) !important;
}

/* ── Alerts / info ── */
[data-testid="stAlert"] {
    border-radius: var(--radius-md) !important;
    font-size: 0.875rem !important;
}

/* ── st.info override ── */
div[data-testid="stNotification"] {
    border-radius: var(--radius-md) !important;
    font-size: 0.875rem !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    background: var(--bg-card) !important;
    box-shadow: none !important;
}
[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    color: var(--text-primary) !important;
}

/* ── Divider ── */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 28px 0 !important;
}

/* ── Spinner ── */
div[data-testid="stSpinner"] p {
    color: var(--primary) !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   STREAMLIT SIDEBAR / MENU CLEANUP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
[data-testid="stSidebarNav"] { display: none; }
header[data-testid="stHeader"] {
    background: rgba(244,246,250,0.85) !important;
    backdrop-filter: blur(8px) !important;
    border-bottom: 1px solid var(--border) !important;
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   COMPONENT IFRAME (email preview)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
iframe {
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--border) !important;
}

/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   PROGRESS OUTER (legacy)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
.progress-outer {
    background: var(--bg-card-alt);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 20px 24px;
    margin-top: 18px;
}
</style>
"""

# ===========================================================================
# HELPER FUNCTIONS
# ===========================================================================


def _validate_secrets() -> dict:
    """
    Validate that all required SMTP secrets are present.

    Returns a dict with the secrets if valid, otherwise calls st.stop()
    after displaying a prominent error message.
    """
    required_keys = [
        "SMTP_SERVER",
        "SMTP_PORT",
        "SMTP_USER",
        "SMTP_PASSWORD",
        "SENDER_EMAIL",
    ]
    missing = [k for k in required_keys if k not in st.secrets]

    if missing:
        st.markdown(
            """
            <div style="
                background: #3a1a1a;
                border: 2px solid #f85149;
                border-radius: 12px;
                padding: 28px 32px;
                margin-top: 40px;
            ">
                <h3 style="color: #f85149; margin: 0 0 12px 0;">
                    ⛔ SMTP Configuration Missing
                </h3>
                <p style="color: #ccc; margin: 0 0 12px 0;">
                    This application requires Amazon SES SMTP credentials stored in
                    <code style="background:#222;padding:2px 6px;border-radius:4px;">
                    .streamlit/secrets.toml</code>.
                </p>
                <p style="color: #f0a0a0; margin: 0 0 8px 0;">
                    <strong>Missing keys:</strong>
                </p>
                <ul style="color: #f0a0a0; margin: 0 0 16px 16px;">
            """
            + "".join(f"<li><code>{k}</code></li>" for k in missing)
            + """
                </ul>
                <p style="color: #999; font-size: 0.85rem; margin: 0;">
                    Please contact the system administrator to configure the secrets
                    file and restart the application.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()

    return {k: st.secrets[k] for k in required_keys}


def _fuzzy_detect_column(
    columns: list[str],
    keywords: list[str],
    threshold: int = 70,
) -> str | None:
    """
    Use rapidfuzz to find the best-matching column name for a set of keywords.

    Parameters
    ----------
    columns   : list of DataFrame column names
    keywords  : target keywords to match against (e.g. ['mail', 'email'])
    threshold : minimum similarity score (0-100) to accept a match

    Returns the best-matching column name or None if nothing meets the threshold.
    """
    best_col: str | None = None
    best_score: float = 0.0

    for col in columns:
        col_lower = col.lower()
        for kw in keywords:
            # partial_ratio handles 'email_address' matching 'mail'
            score = fuzz.partial_ratio(kw, col_lower)
            if score > best_score:
                best_score = score
                best_col = col

    return best_col if best_score >= threshold else None


def _sample_based_email_detect(df: pd.DataFrame, n_samples: int = 10) -> str | None:
    """
    Scan the first n_samples rows of each column and return the column
    whose values most frequently match the email regex.
    Falls back when fuzzy name detection is inconclusive.
    """
    best_col: str | None = None
    best_hit_rate: float = 0.0

    for col in df.columns:
        sample = df[col].dropna().astype(str).head(n_samples)
        if len(sample) == 0:
            continue
        hits = sample.apply(lambda v: bool(EMAIL_RE.match(v.strip()))).sum()
        hit_rate = hits / len(sample)
        if hit_rate > best_hit_rate:
            best_hit_rate = hit_rate
            best_col = col

    # Require at least 50 % of samples to look like emails
    return best_col if best_hit_rate >= 0.5 else None


def _auto_detect_columns(df: pd.DataFrame) -> tuple[str | None, str | None]:
    """
    Auto-detect the email column and the name (personalization) column.

    Strategy (email):
        1. Fuzzy-match column name against email-related keywords.
        2. Fallback: sample-based regex scan.

    Strategy (name):
        1. Fuzzy-match column name against name-related keywords.
        2. If nothing qualifies, return None (personalization is optional).

    Returns (email_col, name_col).
    """
    cols = list(df.columns)

    email_col = _fuzzy_detect_column(
        cols, ["email", "mail", "e-mail", "contact", "email_address"]
    )
    if email_col is None:
        email_col = _sample_based_email_detect(df)

    name_col = _fuzzy_detect_column(
        cols, ["name", "author", "full_name", "firstname", "surname", "researcher"]
    )

    return email_col, name_col


def _build_email_message(
    sender: str,
    recipient_email: str,
    recipient_name: str,
    subject: str,
    html_body: str,
) -> MIMEMultipart:
    """Compose a MIME email with an HTML body."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    return msg


def _execute_send_loop(
    smtp_cfg: dict,
    rows: pd.DataFrame,
    email_col: str,
    name_col: str | None,
    label: str,
) -> None:
    """
    Core sending loop.

    Iterates over `rows`, builds and sends one email per record.
    Displays a live progress bar and status text. Errors are caught
    per-message and surfaced via st.error without aborting the whole run.

    Parameters
    ----------
    smtp_cfg   : dict with SMTP_SERVER, SMTP_PORT, SMTP_USER,
                 SMTP_PASSWORD, SENDER_EMAIL
    rows       : DataFrame slice to process
    email_col  : column that holds the recipient address
    name_col   : column that holds the recipient name (may be None)
    label      : human label shown in status messages (e.g. "Test Batch")
    """
    total = len(rows)
    if total == 0:
        st.warning("No rows to process. Please upload a CSV and try again.")
        return

    sent_ok = 0
    sent_fail = 0
    fail_log: list[str] = []

    progress_bar = st.progress(0.0, text=f"Connecting to Amazon SES …")
    status_line = st.empty()
    error_box = st.empty()

    try:
        with smtplib.SMTP(smtp_cfg["SMTP_SERVER"], int(smtp_cfg["SMTP_PORT"])) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_cfg["SMTP_USER"], smtp_cfg["SMTP_PASSWORD"])

            for idx, (_, row) in enumerate(rows.iterrows(), start=1):
                recipient_email = str(row[email_col]).strip()

                # Basic sanity check before attempting send
                if not EMAIL_RE.match(recipient_email):
                    sent_fail += 1
                    fail_log.append(
                        f"Row {idx}: Invalid address → '{recipient_email}'"
                    )
                    progress_bar.progress(
                        idx / total,
                        text=f"[{label}] Processing {idx}/{total} …",
                    )
                    status_line.markdown(
                        f"⚠️ Skipped row {idx} — invalid address: `{recipient_email}`"
                    )
                    time.sleep(0.1)
                    continue

                # Resolve recipient name
                if name_col and name_col in row.index and pd.notna(row[name_col]):
                    recipient_name = str(row[name_col]).strip() or "Researcher"
                else:
                    recipient_name = "Researcher"

                # Build HTML body — reads from live session state so any
                # edits made in the Template Builder are reflected here.
                html_body = st.session_state.html_template.format(
                    name=recipient_name,
                    email=recipient_email,
                )

                try:
                    msg = _build_email_message(
                        sender=smtp_cfg["SENDER_EMAIL"],
                        recipient_email=recipient_email,
                        recipient_name=recipient_name,
                        subject=EMAIL_SUBJECT,
                        html_body=html_body,
                    )
                    server.sendmail(
                        smtp_cfg["SENDER_EMAIL"],
                        recipient_email,
                        msg.as_string(),
                    )
                    sent_ok += 1

                except smtplib.SMTPException as exc:
                    sent_fail += 1
                    fail_log.append(f"Row {idx} ({recipient_email}): {exc}")

                # ── Live UI updates ──────────────────────────────────
                progress_fraction = idx / total
                progress_bar.progress(
                    progress_fraction,
                    text=(
                        f"[{label}] Sent {sent_ok} of {total} emails "
                        f"({sent_fail} failed) …"
                    ),
                )
                status_line.markdown(
                    f"📨 **Sent {sent_ok} of {total}** &nbsp;|&nbsp; "
                    f"❌ Failed: {sent_fail} &nbsp;|&nbsp; "
                    f"📋 Current: `{recipient_email}`"
                )

                # ── SES throttle safeguard (~10 emails/sec) ──────────
                time.sleep(0.1)

    except Exception as exc:  # noqa: BLE001
        st.error(
            f"🔴 **Connection error during {label}:** {exc}\n\n"
            "Please verify your SMTP credentials in `.streamlit/secrets.toml` "
            "and ensure the SES account is out of sandbox mode."
        )
        return

    # ── Final summary ─────────────────────────────────────────────────────
    progress_bar.progress(1.0, text=f"✅ {label} complete!")
    status_line.empty()

    if sent_ok > 0 and sent_fail == 0:
        st.success(
            f"✅ **{label} finished successfully!** "
            f"**{sent_ok}** email(s) delivered with no errors."
        )
    elif sent_ok > 0:
        st.warning(
            f"⚠️ **{label} finished with some errors.** "
            f"Delivered: **{sent_ok}** | Failed: **{sent_fail}**"
        )
    else:
        st.error(
            f"❌ **{label} failed.** All {sent_fail} attempt(s) encountered errors."
        )

    if fail_log:
        with st.expander(f"📋 View {len(fail_log)} failure(s)", expanded=False):
            for entry in fail_log:
                st.markdown(f"- {entry}")


# ===========================================================================
# APPLICATION ENTRY POINT
# ===========================================================================


def main() -> None:
    # ── Seed session state with default HTML template (runs once) ────────
    if "html_template" not in st.session_state:
        st.session_state.html_template = HTML_TEMPLATE

    # ── Inject custom CSS ────────────────────────────────────────────────
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # ── Hero banner ───────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="hero-block">
            <h1>📧 SOS Survey</h1>
            <p>
                Secure, high-volume academic survey email dispatcher &nbsp;·&nbsp;
                Powered by Amazon SES
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Validate secrets (halts app if missing) ───────────────────────────
    smtp_cfg = _validate_secrets()

    # ═════════════════════════════════════════════════════════════════════
    # SECTION 1 — Email Template Builder (always visible, no CSV required)
    # ═════════════════════════════════════════════════════════════════════
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-title'><span>✉️</span> Section 1 &mdash; Email Template Builder</div>",
        unsafe_allow_html=True,
    )

    tab_preview, tab_edit = st.tabs(["👁️ Visual Preview", "📝 Edit HTML Code"])

    with tab_edit:
        st.info(
            "✏️ **Edit the raw HTML below.** The placeholders `{name}` and `{email}` "
            "are injected dynamically for each recipient — **do not remove them**. "
            "All other HTML can be freely modified. Changes persist until the page "
            "is closed or refreshed."
        )
        st.text_area(
            label="HTML Source",
            key="html_template",
            height=450,
            help="Edit the email body. Keep {name} and {email} placeholders intact.",
            label_visibility="collapsed",
        )

    with tab_preview:
        try:
            preview_html = st.session_state.html_template.format(
                name="[Recipient Name]",
                email="test@example.com",
            )
        except (KeyError, ValueError):
            preview_html = (
                "<p style='color:red;font-family:Arial'>"
                "⚠️ Template error: check that <code>{name}</code> and "
                "<code>{email}</code> placeholders are present and properly formatted."
                "</p>"
            )
        components.html(preview_html, height=450, scrolling=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ═════════════════════════════════════════════════════════════════════
    # SECTION 2 — Data Ingestion & Column Mapping
    # ═════════════════════════════════════════════════════════════════════
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">
                <span>📂</span> Section 2 &mdash; Data Ingestion &amp; Column Mapping
            </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload your recipient file (.csv, .xlsx, .xls)",
        type=["csv", "xlsx", "xls"],
        help="Upload a CSV or Excel file containing at least one column "
             "with recipient email addresses.",
        key="csv_uploader",
    )

    st.markdown("</div>", unsafe_allow_html=True)  # close section-card

    # ── Guard: nothing to do until a file is uploaded ────────────────────
    if uploaded_file is None:
        st.markdown(
            """
            <div class="info-box" style="margin-top:8px;">
                👆 Upload a <strong>.csv</strong> or <strong>.xlsx / .xls</strong>
                file above to continue. The engine will automatically detect
                email and name columns.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()

    # ── Load file (CSV or Excel) ─────────────────────────────────────────
    try:
        if uploaded_file.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as exc:
        st.error(f"❌ Failed to parse file: {exc}")
        st.stop()

    if df.empty:
        st.error("❌ The uploaded file appears to be empty. Please upload a valid file.")
        st.stop()

    total_rows = len(df)
    columns_list = list(df.columns)

    # ── Auto-detection ────────────────────────────────────────────────────
    detected_email_col, detected_name_col = _auto_detect_columns(df)

    # ── Display detection chips ───────────────────────────────────────────
    st.markdown(
        "<div class='section-card'>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='section-title'><span>🔍</span> Auto-Detection Results</div>",
        unsafe_allow_html=True,
    )

    chip_email = (
        f"<div class='detect-chip'>✉️ Email column: <strong>{detected_email_col}</strong></div>"
        if detected_email_col
        else "<div class='detect-chip' style='background:#3a1a1a;color:#f85149;border-color:#6a2020;'>⚠️ Email column: <strong>not detected</strong></div>"
    )
    chip_name = (
        f"<div class='detect-chip'>🧑 Name column: <strong>{detected_name_col}</strong></div>"
        if detected_name_col
        else (
            "<div class='detect-chip' style='background:#3a2e1a;color:#e3b341;"
            "border-color:#6a5020;'>&#8212; Name column: <strong>not detected</strong>"
            " (will use &#39;Researcher&#39;)</div>"
        )
    )

    st.markdown(chip_email + chip_name, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Column selectors ─────────────────────────────────────────────────
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-title'><span>🎛️</span> Verify or Override Column Mapping</div>",
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns(2)

    with col_left:
        email_default_idx = (
            columns_list.index(detected_email_col)
            if detected_email_col in columns_list
            else 0
        )
        selected_email_col = st.selectbox(
            "📧 Recipient Email Column",
            options=columns_list,
            index=email_default_idx,
            key="email_col_select",
            help="Select the column that contains the email address of each recipient.",
        )

    with col_right:
        name_options = ["— None (use 'Researcher' as fallback) —"] + columns_list
        name_default_idx = (
            columns_list.index(detected_name_col) + 1
            if detected_name_col and detected_name_col in columns_list
            else 0
        )
        selected_name_raw = st.selectbox(
            "🧑 Recipient Name Column (optional)",
            options=name_options,
            index=name_default_idx,
            key="name_col_select",
            help="Select the column used to personalise the greeting. "
                 "Leave as '— None —' to use 'Researcher' for all recipients.",
        )
        selected_name_col: str | None = (
            None if selected_name_raw.startswith("—") else selected_name_raw
        )

    # ── Dataset preview + metrics ─────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(
            f"""
            <div class="metric-tile">
                <div class="value">{total_rows:,}</div>
                <div class="label">Total Rows</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f"""
            <div class="metric-tile">
                <div class="value">{len(columns_list)}</div>
                <div class="label">Columns</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m3:
        valid_emails = (
            df[selected_email_col]
            .dropna()
            .astype(str)
            .apply(lambda v: bool(EMAIL_RE.match(v.strip())))
            .sum()
        )
        st.markdown(
            f"""
            <div class="metric-tile">
                <div class="value">{valid_emails:,}</div>
                <div class="label">Valid Addresses</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#8b949e;font-size:0.85rem;margin:0 0 8px 0;'>"
        "📋 <strong>Data Preview</strong> — first 5 rows</p>",
        unsafe_allow_html=True,
    )
    st.dataframe(df.head(5), use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ═════════════════════════════════════════════════════════════════════
    # SECTION 2 — Campaign & Smart Batching
    # ═════════════════════════════════════════════════════════════════════
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-title'><span>⚙️</span> Section 3 &mdash; Campaign &amp; Batch Configuration</div>",
        unsafe_allow_html=True,
    )

    # Determine default batch size selection
    if total_rows > 5000:
        default_batch_label = 5000
    else:
        default_batch_label = "Full Dataset"

    default_batch_idx = BATCH_OPTIONS.index(default_batch_label)

    selected_batch = st.selectbox(
        "📦 Batch Size",
        options=BATCH_OPTIONS,
        index=default_batch_idx,
        key="batch_size_select",
        help=(
            "Choose how many records to process in this run. "
            "'Full Dataset' processes every row in the uploaded file."
        ),
        format_func=lambda x: f"{x:,} records" if isinstance(x, int) else str(x),
    )

    # Resolve numeric batch size
    if selected_batch == "Full Dataset":
        batch_size = total_rows
    else:
        batch_size = int(selected_batch)

    actual_batch = min(batch_size, total_rows)

    st.markdown(
        f"""
        <div class="info-box">
            📌 The engine will process <strong>rows 1 through {actual_batch:,}</strong>
            out of <strong>{total_rows:,}</strong> total records in your dataset.
            &nbsp; Estimated time at 10 emails/sec:
            <strong>~{actual_batch / 10 / 60:.1f} minutes</strong>.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)

    # ═════════════════════════════════════════════════════════════════════
    # SECTION 4 — Execution Engine
    # ═════════════════════════════════════════════════════════════════════
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-title'><span>🚀</span> Section 4 &mdash; Execution Engine</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <p style="color:#8b949e;font-size:0.88rem;margin:0 0 18px 0;">
            Run a <strong>Test Batch</strong> (first 2 rows) to verify formatting
            before committing to a full send. When ready, use
            <strong>Execute Full Batch Send</strong>.
        </p>
        """,
        unsafe_allow_html=True,
    )

    btn_col_a, btn_col_b = st.columns(2)

    with btn_col_a:
        test_clicked = st.button(
            "🚀 Run Test Batch (First 2 Rows Only)",
            key="btn_test",
            use_container_width=True,
            type="secondary",
            help="Send to exactly the first 2 rows only — ideal for format checking.",
        )

    with btn_col_b:
        full_clicked = st.button(
            "🔥 Execute Full Batch Send",
            key="btn_full",
            use_container_width=True,
            type="primary",
            help=f"Send to the configured batch of {actual_batch:,} recipients.",
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # ═════════════════════════════════════════════════════════════════════
    # EXECUTION HANDLING
    # ═════════════════════════════════════════════════════════════════════

    if test_clicked:
        test_rows = df.head(2)
        st.markdown("---")
        st.markdown(
            """
            <div class='section-card' style='border-color:#1266c9;'>
                <div class='section-title'>
                    <span>🔬</span> Test Batch — Sending to first 2 recipients
                </div>
            """,
            unsafe_allow_html=True,
        )
        _execute_send_loop(
            smtp_cfg=smtp_cfg,
            rows=test_rows,
            email_col=selected_email_col,
            name_col=selected_name_col,
            label="Test Batch",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    if full_clicked:
        full_rows = df.head(actual_batch)
        st.markdown("---")
        st.markdown(
            f"""
            <div class='section-card' style='border-color:#e3b341;'>
                <div class='section-title'>
                    <span>🔥</span> Full Batch — Sending to {actual_batch:,} recipients
                </div>
            """,
            unsafe_allow_html=True,
        )
        _execute_send_loop(
            smtp_cfg=smtp_cfg,
            rows=full_rows,
            email_col=selected_email_col,
            name_col=selected_name_col,
            label=f"Full Batch ({actual_batch:,})",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────────────────
    st.markdown(
        """
        <hr>
        <p style="text-align:center;color:#484f58;font-size:0.78rem;margin:0;">
            Secured via Amazon SES SMTP &nbsp;·&nbsp;
            All transmissions are TLS-encrypted
        </p>
        """,
        unsafe_allow_html=True,
    )


# ===========================================================================
# ENTRY
# ===========================================================================
if __name__ == "__main__":
    main()
