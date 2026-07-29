"""
JD/CV Analysis App — Streamlit UI
Multi-role (Candidate / HR / HeadHunter) with LLM-powered analysis.
Includes encryption at rest, PII masking, and data retention controls.
"""

import os
import tempfile

import streamlit as st

from config import get_llm_settings, set_llm_settings
from llm_client import LLMClient, LLMClientError, PROVIDER_DEFAULTS, VALID_PROVIDERS
from db import init_db, save_analysis, load_history, delete_record, purge_old_records
from privacy import (
    estimate_pii_risk,
    list_pii_matches,
    mask_pii,
    secure_delete,
    write_temp_file,
)
from utils.reader import read_file
from analyzer import analyze_candidate, analyze_hr, analyze_headhunter

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="JD/CV Analysis Tool",
    page_icon="📋",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Session defaults — privacy
# ---------------------------------------------------------------------------

if "privacy_initialized" not in st.session_state:
    st.session_state["pii_mask_enabled"] = True
    st.session_state["retention_days"] = 30
    st.session_state["store_history"] = True
    st.session_state["privacy_initialized"] = True

# ---------------------------------------------------------------------------
# Sidebar — LLM settings
# ---------------------------------------------------------------------------

st.sidebar.title("⚙️ LLM Settings")

# Load saved settings on first run
if "llm_loaded" not in st.session_state:
    saved = get_llm_settings()
    st.session_state["llm_provider"] = saved["provider"]
    st.session_state["llm_base_url"] = saved["base_url"]
    st.session_state["llm_api_key"] = saved["api_key"]
    st.session_state["llm_model"] = saved["model"]
    st.session_state["llm_loaded"] = True

# Auto-switch defaults when provider changes
prev_provider = st.session_state.get("_prev_provider", "")
current_provider = st.session_state["llm_provider"]
if current_provider != prev_provider:
    defaults = PROVIDER_DEFAULTS.get(current_provider, {})
    if defaults.get("base_url"):
        st.session_state["llm_base_url"] = defaults["base_url"]
    if defaults.get("model"):
        st.session_state["llm_model"] = defaults["model"]
    st.session_state["_prev_provider"] = current_provider

PROVIDER_LABELS = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "deepseek": "DeepSeek",
    "qwen": "Qwen (Tongyi)",
    "glm": "GLM (Zhipu)",
    "kimi": "Kimi (Moonshot)",
}

default_idx = VALID_PROVIDERS.index(current_provider) if current_provider in VALID_PROVIDERS else 0
st.sidebar.selectbox(
    "Provider",
    VALID_PROVIDERS,
    index=default_idx,
    format_func=lambda x: PROVIDER_LABELS.get(x, x),
    key="llm_provider",
)

st.sidebar.text_input("Base URL", key="llm_base_url")

st.sidebar.text_input("API Key", type="password", key="llm_api_key")

st.sidebar.text_input("Model", key="llm_model")

# Save / Load buttons
col_save1, col_save2 = st.sidebar.columns([1, 1])
with col_save1:
    if st.button("💾 Save Settings", use_container_width=True):
        set_llm_settings(
            provider=st.session_state["llm_provider"],
            base_url=st.session_state["llm_base_url"],
            api_key=st.session_state["llm_api_key"],
            model=st.session_state["llm_model"],
        )
        st.sidebar.success("Saved (API key encrypted)")
with col_save2:
    if st.button("📂 Load Settings", use_container_width=True):
        saved = get_llm_settings()
        st.session_state["llm_provider"] = saved["provider"]
        st.session_state["llm_base_url"] = saved["base_url"]
        st.session_state["llm_api_key"] = saved["api_key"]
        st.session_state["llm_model"] = saved["model"]
        st.sidebar.info("Loaded from settings.ini")
        st.rerun()

# ---------------------------------------------------------------------------
# Sidebar — Privacy & data protection
# ---------------------------------------------------------------------------

st.sidebar.divider()
st.sidebar.title("🔒 Privacy & Data Protection")

st.sidebar.checkbox(
    "Mask PII before sending to LLM",
    value=True,
    key="pii_mask_enabled",
    help=(
        "Detects and masks names, emails, phone numbers, addresses, and ID numbers "
        "in the JD/CV text before sending to the LLM API. The LLM never sees the "
        "original personal identifiers. Recommended: ON."
    ),
)

st.sidebar.checkbox(
    "Store analysis in local history",
    value=True,
    key="store_history",
    help=(
        "When enabled, analysis results are saved to the local encrypted SQLite "
        "database for later review. When disabled, results are shown but never "
        "written to disk. Recommended: OFF for highly sensitive CVs."
    ),
)

retention = st.sidebar.number_input(
    "Auto-delete records older than (days)",
    min_value=1,
    max_value=365,
    value=30,
    key="retention_days",
    help="Records older than this are purged on app startup. Set lower for tighter security.",
)

st.sidebar.caption(
    "📁 All stored data is encrypted at rest (Fernet). "
    "The encryption key is in `.data_key` — keep this file safe."
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_client() -> LLMClient | None:
    """Build an LLMClient from session_state settings, or return None if incomplete."""
    key = st.session_state.get("llm_api_key", "").strip()
    if not key:
        st.warning("Please enter your API Key in the sidebar")
        return None
    return LLMClient(
        provider=st.session_state.get("llm_provider", "openai"),
        base_url=st.session_state.get("llm_base_url", ""),
        api_key=key,
        model=st.session_state.get("llm_model", "gpt-4o"),
    )


def _run_analysis(role: str, jd_text: str, cv_text: str, mode: str | None = None) -> str:
    """Dispatch analysis to the correct analyzer module."""
    client = _build_client()
    if client is None:
        st.stop()

    # PII masking — use pre-computed masked text if available
    if st.session_state.get("pii_mask_enabled", True):
        jd_text = st.session_state.get("jd_masked", jd_text)
        cv_text = st.session_state.get("cv_masked", cv_text)

    with st.spinner(f"🤖 Analyzing as {role}, please wait…"):
        if role == "Candidate":
            return analyze_candidate(client, jd_text, cv_text)
        elif role == "HR":
            return analyze_hr(client, jd_text, cv_text)
        else:  # HeadHunter
            return analyze_headhunter(client, jd_text, cv_text, mode)


# ---------------------------------------------------------------------------
# Initialize DB & run retention purge
# ---------------------------------------------------------------------------

init_db()
purged = purge_old_records(st.session_state.get("retention_days", 30))
if purged:
    st.toast(f"🧹 Auto-purged {purged} old record(s) (>{st.session_state['retention_days']} days)", icon="🧹")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_analysis, tab_history = st.tabs(["📊 Analysis", "📚 History"])

# ===========================================================================
# TAB 1: Analysis
# ===========================================================================

with tab_analysis:
    st.title("📋 JD / CV Analysis Tool")

    # --- Privacy notice ---
    with st.expander("🔒 Privacy Notice — Please Read", expanded=True):
        st.markdown(
            """
            ⚠️ **Data handling summary:**
            - Uploaded files are written to a **temporary file** and deleted immediately after text extraction.
            - If **Mask PII** is enabled (sidebar), personal identifiers are replaced with placeholders
              before sending to the LLM API.
            - If **Store history** is enabled, results are **encrypted** before writing to the local SQLite database.
            - Your API key is **encrypted** in `settings.ini`.
            - **Data sent to the LLM provider** (OpenAI / Anthropic) is subject to their privacy policy.
              Do NOT upload highly sensitive data unless you trust the provider.
            - For maximum privacy: disable history storage and enable PII masking.
            """
        )

    # --- Role selector ---
    role = st.selectbox(
        "Select Role",
        ["Candidate", "HR", "HeadHunter"],
        format_func=lambda r: {
            "Candidate": "🧑‍💼 Candidate",
            "HR": "🏢 HR",
            "HeadHunter": "🎯 HeadHunter",
        }[r],
    )

    # HeadHunter extra mode toggle
    hh_mode = None
    if role == "HeadHunter":
        hh_mode = st.radio(
            "HeadHunter Mode",
            ["Candidate", "HR"],
            format_func=lambda m: {
                "Candidate": "🧑 Candidate mode — Deep-dive questions to understand the candidate",
                "HR": "🏢 HR mode — Recommendation, highlights, risks, and referral letter",
            }[m],
            horizontal=True,
        )

    # --- File upload ---
    col1, col2 = st.columns(2)
    with col1:
        jd_file = st.file_uploader(
            "📄 Upload JD (Job Description)",
            type=["pdf", "docx", "txt"],
            key="jd",
        )
    with col2:
        cv_file = st.file_uploader(
            "📄 Upload CV (Resume)",
            type=["pdf", "docx", "txt"],
            key="cv",
        )

    # Read uploaded files (temp files cleaned up immediately after read)
    jd_text: str = ""
    cv_text: str = ""

    if jd_file is not None:
        tmp_path = ""
        try:
            tmp_path = write_temp_file(jd_file.name, jd_file.read())
            jd_text = read_file(tmp_path)
            st.success(f"✅ JD loaded ({len(jd_text)} characters)")
        except Exception as e:
            st.error(f"❌ Failed to read JD: {e}")
        finally:
            if tmp_path:
                secure_delete(tmp_path)

    if cv_file is not None:
        tmp_path = ""
        try:
            tmp_path = write_temp_file(cv_file.name, cv_file.read())
            cv_text = read_file(tmp_path)
            st.success(f"✅ CV loaded ({len(cv_text)} characters)")
        except Exception as e:
            st.error(f"❌ Failed to read CV: {e}")
        finally:
            if tmp_path:
                secure_delete(tmp_path)

    # --- PII Review (shown when both files are loaded and masking is on) ---
    if (
        jd_text
        and cv_text
        and st.session_state.get("pii_mask_enabled", True)
    ):
        # Pre-compute masked versions and store in session state
        jd_masked, jd_matches = mask_pii(jd_text)
        cv_masked, cv_matches = mask_pii(cv_text)
        st.session_state["jd_masked"] = jd_masked
        st.session_state["cv_masked"] = cv_masked
        all_matches = jd_matches + cv_matches

        if all_matches:
            with st.expander(
                f"🔍 PII Review — {len(all_matches)} item(s) will be masked before sending",
                expanded=True,
            ):
                st.markdown(
                    "The following personal identifiers were detected and **will be masked** "
                    "before the text is sent to the LLM. The LLM will see placeholders like "
                    "`[NAME]`, `[EMAIL]`, `[PHONE]` instead of the real values."
                )
                # Summary table
                rows = []
                for m in all_matches:
                    source = "JD" if m in jd_matches else "CV"
                    rows.append({
                        "Source": source,
                        "Line": m.line_no,
                        "Type": m.label,
                        "Original": m.original[:60] + ("…" if len(m.original) > 60 else ""),
                        "Replaced by": m.masked,
                    })
                st.dataframe(
                    rows,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Source": st.column_config.Column(width="small"),
                        "Line": st.column_config.Column(width="small"),
                        "Type": st.column_config.Column(width="small"),
                        "Original": st.column_config.Column(width="medium"),
                        "Replaced by": st.column_config.Column(width="small"),
                    },
                )
                st.caption(
                    "✅ Review complete — the LLM will receive masked text only. "
                    "The original text is still shown in the preview below and saved "
                    "locally (if history is enabled)."
                )
        else:
            # Clear any stale masked versions when no PII found
            st.session_state["jd_masked"] = jd_text
            st.session_state["cv_masked"] = cv_text
            st.info("🔍 No PII detected — text will be sent as-is.", icon="✅")
    elif jd_text and cv_text:
        # Masking is off — send raw text
        st.session_state["jd_masked"] = jd_text
        st.session_state["cv_masked"] = cv_text

    # --- Text preview expanders ---
    if jd_text:
        with st.expander("🔍 Preview JD"):
            st.text_area("JD", jd_text, height=200, disabled=True, label_visibility="collapsed")
    if cv_text:
        with st.expander("🔍 Preview CV"):
            st.text_area("CV", cv_text, height=200, disabled=True, label_visibility="collapsed")

    # --- Analyze button ---
    if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
        if not jd_text or not cv_text:
            st.warning("Please upload both JD and CV files")
        else:
            try:
                store = st.session_state.get("store_history", True)
                result = _run_analysis(role, jd_text, cv_text, hh_mode)

                if store:
                    save_analysis(
                        role=role,
                        jd_text=jd_text,
                        cv_text=cv_text,
                        result=result,
                        mode=hh_mode if role == "HeadHunter" else None,
                    )
                    st.success("✅ Analysis complete — encrypted & saved to local history")
                else:
                    st.success("✅ Analysis complete — NOT saved (history disabled)")
                    st.caption("💡 Results are shown below but not written to disk.")

                st.markdown("---")
                st.markdown(result)

            except LLMClientError as e:
                st.error(f"❌ LLM call failed: {e}")
            except Exception as e:
                st.error(f"❌ Error: {e}")

# ===========================================================================
# TAB 2: History
# ===========================================================================

with tab_history:
    st.title("📚 Analysis History")

    if not st.session_state.get("store_history", True):
        st.warning(
            "⚠️ History storage is currently **disabled** in the sidebar privacy settings. "
            "Enable it to save future analyses."
        )

    if st.button("🔄 Refresh"):
        st.rerun()

    records = load_history(limit=50)

    if not records:
        st.info("No analysis history yet. Run an analysis first.")
    else:
        for rec in records:
            role_label = rec["role"]
            mode_label = f" ({rec['mode']})" if rec.get("mode") else ""
            ts = rec["created_at"][:19].replace("T", " ")
            label = f"#{rec['id']} | {role_label}{mode_label} | {ts}"

            with st.expander(label):
                col_a, col_b = st.columns([5, 1])
                with col_a:
                    st.markdown(f"**Role:** {role_label}{mode_label}")
                    st.markdown(f"**Time:** {rec['created_at']}")

                    with st.expander("📄 JD Content"):
                        st.text_area(
                            "JD",
                            rec["jd_text"],
                            height=150,
                            disabled=True,
                            label_visibility="collapsed",
                            key=f"jd_hist_{rec['id']}",
                        )

                    with st.expander("📄 CV Content"):
                        st.text_area(
                            "CV",
                            rec["cv_text"],
                            height=150,
                            disabled=True,
                            label_visibility="collapsed",
                            key=f"cv_hist_{rec['id']}",
                        )

                    st.markdown("### Analysis Result")
                    st.markdown(rec["result"])
                with col_b:
                    if st.button("🗑️ Delete", key=f"del_{rec['id']}"):
                        delete_record(rec["id"])
                        st.toast("Record deleted", icon="🗑️")
                        st.rerun()

    # Bulk clear
    if len(records) > 1:
        if st.button("🗑️ Clear All History", type="secondary"):
            for rec in records:
                delete_record(rec["id"])
            st.toast("All records deleted", icon="🗑️")
            st.rerun()
