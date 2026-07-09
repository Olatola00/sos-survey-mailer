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
# CUSTOM CSS — Premium dark-mode UI
# ===========================================================================

CUSTOM_CSS = """
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Root ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── App background ── */
.stApp {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 60%, #0d1117 100%);
    color: #e6edf3;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #161b22; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }

/* ── Header / Title block ── */
.hero-block {
    background: linear-gradient(120deg, #0e4a8c 0%, #1266c9 50%, #0e4a8c 100%);
    border-radius: 16px;
    padding: 32px 40px;
    margin-bottom: 28px;
    box-shadow: 0 8px 32px rgba(0, 100, 220, 0.25);
    border: 1px solid rgba(255,255,255,0.08);
}
.hero-block h1 {
    margin: 0 0 6px 0;
    font-size: 1.9rem;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.5px;
}
.hero-block p {
    margin: 0;
    font-size: 0.95rem;
    color: rgba(255,255,255,0.75);
}

/* ── Section cards ── */
.section-card {
    background: rgba(22, 27, 34, 0.85);
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 28px 32px;
    margin-bottom: 24px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    backdrop-filter: blur(8px);
}
.section-title {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 1.1rem;
    font-weight: 600;
    color: #79c0ff;
    margin: 0 0 18px 0;
    padding-bottom: 12px;
    border-bottom: 1px solid #21262d;
}

/* ── Badge ── */
.badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.3px;
}
.badge-blue  { background: #1c3a5e; color: #79c0ff; border: 1px solid #2e5a8a; }
.badge-green { background: #1a3a28; color: #56d364; border: 1px solid #2a6040; }
.badge-amber { background: #3a2e1a; color: #e3b341; border: 1px solid #6a5020; }
.badge-red   { background: #3a1a1a; color: #f85149; border: 1px solid #6a2020; }

/* ── Auto-detect chips ── */
.detect-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #1c3a5e;
    color: #79c0ff;
    border: 1px solid #2e5a8a;
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 0.82rem;
    font-weight: 500;
    margin: 4px 4px 4px 0;
}

/* ── Info box ── */
.info-box {
    background: rgba(18, 102, 201, 0.12);
    border: 1px solid rgba(18, 102, 201, 0.4);
    border-left: 4px solid #1266c9;
    border-radius: 8px;
    padding: 14px 18px;
    color: #a5c9f5;
    font-size: 0.9rem;
    margin-top: 14px;
}
.info-box strong { color: #79c0ff; }

/* ── Progress container ── */
.progress-outer {
    background: #21262d;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 20px 24px;
    margin-top: 18px;
}

/* ── Streamlit widget overrides ── */
.stFileUploader > div {
    background: rgba(22, 27, 34, 0.6) !important;
    border: 2px dashed #30363d !important;
    border-radius: 10px !important;
    color: #8b949e !important;
}
.stFileUploader > div:hover {
    border-color: #1266c9 !important;
}
.stDataFrame { border-radius: 8px; overflow: hidden; }

div[data-testid="stSelectbox"] label,
div[data-testid="stFileUploadDropzone"] label {
    color: #c9d1d9 !important;
    font-weight: 500 !important;
}

/* ── Button overrides ── */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.2s ease !important;
    border: none !important;
    padding: 10px 22px !important;
    width: 100%;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(0,0,0,0.4) !important;
}

/* ── Divider ── */
hr { border-color: #21262d !important; margin: 28px 0 !important; }

/* ── Metric tiles ── */
.metric-row { display: flex; gap: 16px; flex-wrap: wrap; margin: 16px 0; }
.metric-tile {
    flex: 1;
    min-width: 140px;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 16px 20px;
    text-align: center;
}
.metric-tile .value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #79c0ff;
    line-height: 1;
    margin-bottom: 4px;
}
.metric-tile .label {
    font-size: 0.75rem;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}

/* ── Spinner override ── */
div[data-testid="stSpinner"] p { color: #79c0ff !important; }
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

                # Build HTML body
                html_body = HTML_TEMPLATE.format(
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
    # SECTION 1 — Data Ingestion & Column Mapping
    # ═════════════════════════════════════════════════════════════════════
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">
                <span>📂</span> Section 1 &mdash; Data Ingestion &amp; Column Mapping
            </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload your recipient CSV file",
        type=["csv"],
        help="Upload a comma-separated file containing at least one column "
             "with recipient email addresses.",
        key="csv_uploader",
    )

    st.markdown("</div>", unsafe_allow_html=True)  # close section-card

    # ── Guard: nothing to do until a file is uploaded ────────────────────
    if uploaded_file is None:
        st.markdown(
            """
            <div class="info-box" style="margin-top:8px;">
                👆 Upload a <strong>.csv</strong> file above to get started.
                The engine will automatically detect email and name columns.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()

    # ── Load CSV ──────────────────────────────────────────────────────────
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as exc:
        st.error(f"❌ Failed to parse CSV: {exc}")
        st.stop()

    if df.empty:
        st.error("❌ The uploaded CSV appears to be empty. Please upload a valid file.")
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
        "<div class='section-title'><span>⚙️</span> Section 2 &mdash; Campaign &amp; Batch Configuration</div>",
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
    # SECTION 3 — Execution Engine
    # ═════════════════════════════════════════════════════════════════════
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-title'><span>🚀</span> Section 3 &mdash; Execution Engine</div>",
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
            AfricaRVI Survey Distribution Engine &nbsp;·&nbsp;
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
