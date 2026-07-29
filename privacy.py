"""
Privacy & data protection module.

Protections:
  - Encryption at rest (Fernet) for database fields and settings
  - Smart PII detection + masking before LLM calls
  - Secure temp file cleanup
  - Data retention auto-purge

PII masking strategy:
  Layer 1 — Label-based: detect "Name:", "Email:", "Phone:" etc. and mask the value.
  Layer 2 — Format-based: regex for emails, phones, IDs with strict patterns.
  Layer 3 — CV header heuristic: first ~6 lines of a CV almost always contain
            the candidate's name. We detect the name line and mask it.

Key management:
  A local key file (`.data_key`) is auto-generated on first run and stored
  with restricted permissions. If it's deleted, all encrypted data becomes
  unreadable — the user gets a fresh start.
"""

import os
import re
import secrets
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet

# ---------------------------------------------------------------------------
# Key management
# ---------------------------------------------------------------------------

KEY_FILE = Path(__file__).parent / ".data_key"


def _get_or_create_key() -> bytes:
    """Return the local encryption key, creating it if needed."""
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()
    key = Fernet.generate_key()
    KEY_FILE.write_bytes(key)
    try:
        os.chmod(KEY_FILE, 0o600)
    except OSError:
        pass  # Windows doesn't fully support chmod
    return key


def _get_fernet() -> Fernet:
    return Fernet(_get_or_create_key())


# ---------------------------------------------------------------------------
# Public API — encrypt / decrypt
# ---------------------------------------------------------------------------

def encrypt(text: str) -> str:
    """Encrypt a plaintext string → base64-encoded ciphertext."""
    return _get_fernet().encrypt(text.encode("utf-8")).decode("utf-8")


def decrypt(token: str) -> str:
    """Decrypt a base64 token → original plaintext. Returns '[DECRYPT_FAILED]' on error."""
    try:
        return _get_fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except Exception:
        return "[DECRYPT_FAILED]"


def safe_decrypt(token: str) -> str:
    """Decrypt if the token looks encrypted, otherwise return as-is."""
    if token.startswith("gAAAAA"):
        return decrypt(token)
    return token


# ---------------------------------------------------------------------------
# PII data structure
# ---------------------------------------------------------------------------

@dataclass
class PiiMatch:
    """One detected PII item."""
    line_no: int
    label: str          # e.g. "Email", "Phone", "Name (header)"
    original: str       # the text that was matched
    masked: str         # what it will be replaced with


# ===========================================================================
# LAYER 1 — Label-based detection (high confidence)
# ===========================================================================
# These match lines like "Name: John Doe" or "電話：0912-345-678"
# The label is captured, then the VALUE after it is masked.
# We use case-insensitive matching and support both English/Chinese labels.

_LABEL_PATTERNS: list[tuple[str, str, str]] = [
    # (regex, PII category label, mask placeholder)
    #
    # --- Name ---
    (r'(?im)^(?:Name|Full\s*Name|姓名|名字|Candidate|Applicant)[\s:：=]+\s*(.+)$', 'Name', '[NAME]'),
    #
    # --- Email ---
    (r'(?im)^(?:Email|E-mail|電子郵件|郵箱|信箱|邮箱)[\s:：=]+\s*(.+)$', 'Email', '[EMAIL]'),
    #
    # --- Phone ---
    (r'(?im)^(?:Phone|Tel|Telephone|Mobile|Cell|聯絡電話|電話|手机|手機|聯繫電話)[\s:：=]+\s*(.+)$', 'Phone', '[PHONE]'),
    #
    # --- Address ---
    (r'(?im)^(?:Address|Addr|地址|住址|通訊地址)[\s:：=]+\s*(.+)$', 'Address', '[ADDRESS]'),
    #
    # --- DOB / Age ---
    (r'(?im)^(?:DOB|Date\s*of\s*Birth|Birth\s*Date|Birthday|出生日期|生日|Age|年齡|年紀)[\s:：=]+\s*(.+)$', 'DOB', '[DOB]'),
    #
    # --- National ID / Passport ---
    (r'(?im)^(?:National\s*ID|ID\s*Number|Passport|護照號碼|身分證|身份證|身份证|統一編號)[\s:：=]+\s*(.+)$', 'ID', '[ID_DOC]'),
    #
    # --- LinkedIn / social ---
    (r'(?im)^(?:LinkedIn|GitHub|Twitter|Facebook|Website|Blog|個人網站)[\s:：=]+\s*(.+)$', 'SocialLink', '[SOCIAL_LINK]'),
    #
    # --- Nationality ---
    (r'(?im)^(?:Nationality|國籍|国籍)[\s:：=]+\s*(.+)$', 'Nationality', '[NATIONALITY]'),
    #
    # --- Driver License ---
    (r'(?im)^(?:Driver\s*License|Driving\s*Licence|駕照|驾照)[\s:：=]+\s*(.+)$', 'License', '[LICENSE]'),
]

# ===========================================================================
# LAYER 2 — Format-based detection (medium confidence)
# ===========================================================================
# Pure regex patterns that match PII by format alone. These are applied
# AFTER label-based so we don't double-mask.

_FORMAT_PATTERNS: list[tuple[str, str]] = [
    # Email — very reliable format
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', '[EMAIL]'),
    # International phone: +country (1-3 digits) then 7-15 digits with separators
    (r'\B\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b', '[PHONE]'),
    # Taiwan mobile: 09xx-xxx-xxx or 09xxxxxxxx
    (r'\b09\d{2}[-.\s]?\d{3}[-.\s]?\d{3}\b', '[PHONE]'),
    # US/Canada: (xxx) xxx-xxxx or xxx-xxx-xxxx
    (r'\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]\d{4}\b', '[PHONE]'),
    # Taiwan national ID: 1 letter + 9 digits
    (r'\b[A-Z][12]\d{8}\b', '[ID_DOC]'),
    # China national ID: 18 digits (6 area + 8 birth + 3 seq + 1 check)
    (r'\b[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b', '[ID_DOC]'),
    # Passport number: 1-2 letters + 6-9 digits
    (r'\b[A-Z]{1,2}\d{6,9}\b', '[ID_DOC]'),
    # URLs with personal info (LinkedIn, GitHub, personal sites)
    (r'\bhttps?://(?:www\.)?linkedin\.com/in/[\w-]+/?\b', '[SOCIAL_LINK]'),
    (r'\bhttps?://(?:www\.)?github\.com/[\w-]+/?\b', '[SOCIAL_LINK]'),
]


def _mask_labeled_lines(text: str) -> tuple[str, list[PiiMatch]]:
    """Layer 1: Find label:value lines and mask the value portion."""
    matches: list[PiiMatch] = []
    lines = text.split("\n")
    result_lines = lines[:]

    for _, label, placeholder in _LABEL_PATTERNS:
        for i, line in enumerate(lines):
            m = re.match(_, line)
            if m and m.group(1):
                value = m.group(1).strip()
                # Skip if already masked
                if value.startswith("[") and value.endswith("]"):
                    continue
                # Replace the value part, keep the label
                result_lines[i] = line[:m.start(1)] + placeholder + line[m.end(1):]
                matches.append(PiiMatch(
                    line_no=i + 1,
                    label=label,
                    original=value,
                    masked=placeholder,
                ))

    return "\n".join(result_lines), matches


def _mask_format_patterns(text: str, skip_lines: set[int]) -> tuple[str, list[PiiMatch]]:
    """Layer 2: Format-based regex matching. skip_lines are already masked."""
    matches: list[PiiMatch] = []
    lines = text.split("\n")
    result_lines: list[str] = []

    for i, line in enumerate(lines):
        modified = line
        if i not in skip_lines:
            for pattern, placeholder in _FORMAT_PATTERNS:
                if re.search(pattern, modified):
                    m = re.search(pattern, modified)
                    if m:
                        matches.append(PiiMatch(
                            line_no=i + 1,
                            label=placeholder.strip("[]"),
                            original=m.group(0),
                            masked=placeholder,
                        ))
                    modified = re.sub(pattern, placeholder, modified)
        result_lines.append(modified)

    return "\n".join(result_lines), matches


def _mask_cv_header_name(text: str) -> tuple[str, list[PiiMatch]]:
    """
    Layer 3: CV header heuristic.
    In most CVs, the first non-empty line is the person's name,
    or the name appears in the first 6 lines in a larger font / standalone.
    We detect standalone name lines (2-3 capitalized words, no punctuation)
    in the header area and mask them.
    """
    matches: list[PiiMatch] = []
    lines = text.split("\n")
    result_lines = lines[:]

    # Find the first non-empty lines (header zone)
    header_end = 0
    non_empty = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped:
            non_empty += 1
            header_end = i + 1
        if non_empty >= 8:
            break

    # Already-masked labels from Layer 1 (to avoid re-masking)
    already_labeled_lines: set[int] = set()

    for i in range(min(header_end, len(lines))):
        line = lines[i].strip()
        if not line:
            continue

        # Check if this line was already processed by label-based detection
        for label_pat, _, _ in _LABEL_PATTERNS:
            if re.match(label_pat, line):
                already_labeled_lines.add(i)
                break

    # Detect standalone name lines in the header zone
    # Pattern: 2-4 words, each starting with uppercase or Chinese char,
    # no common header keywords, minimal punctuation
    _HEADER_KEYWORDS = re.compile(
        r'(?i)curriculum\s*vitae|resume|cv|profile|portfolio|'
        r'objective|summary|experience|education|skill|contact|'
        r'phone|email|address|linkedin|github|http'
    )

    _NAME_LINE = re.compile(
        r'^([A-Z一-鿿][a-z一-鿿]*[\s·.．]){1,3}[A-Z一-鿿][a-z一-鿿]*$'
    )

    for i in range(min(header_end, len(lines))):
        line = lines[i].strip()
        if not line or i in already_labeled_lines:
            continue
        if _HEADER_KEYWORDS.search(line):
            continue
        if _NAME_LINE.match(line) and 3 < len(line) < 60:
            result_lines[i] = "[NAME]"
            matches.append(PiiMatch(
                line_no=i + 1,
                label="Name (header)",
                original=line,
                masked="[NAME]",
            ))
            break  # Only mask the first name line found

    return "\n".join(result_lines), matches


# ===========================================================================
# Unified masking API
# ===========================================================================

def mask_pii(text: str) -> tuple[str, list[PiiMatch]]:
    """
    Run all three layers of PII detection and return (masked_text, matches).
    Layers:
      1. Label-based (e.g. "Name: John Doe" → "Name: [NAME]")
      2. Format-based (e.g. "john@example.com" → "[EMAIL]")
      3. CV header heuristic (standalone name line at top)
    """
    # Layer 1
    text, l1_matches = _mask_labeled_lines(text)
    skip_lines = {m.line_no - 1 for m in l1_matches}

    # Layer 2 (skip lines already handled in layer 1)
    text, l2_matches = _mask_format_patterns(text, skip_lines)

    # Layer 3
    text, l3_matches = _mask_cv_header_name(text)

    return text, l1_matches + l2_matches + l3_matches


def estimate_pii_risk(text: str) -> tuple[int, list[str]]:
    """
    Quick scan — count PII matches found. Returns (count, [types]).
    Used for the risk warning badge in the UI.
    """
    _, matches = mask_pii(text)
    if not matches:
        return 0, []
    types: list[str] = []
    for m in matches:
        if m.label not in types:
            types.append(m.label)
    return len(matches), types


def list_pii_matches(text: str) -> list[PiiMatch]:
    """Return all detected PII items with line numbers for review."""
    _, matches = mask_pii(text)
    return matches


# ---------------------------------------------------------------------------
# Temp file helpers
# ---------------------------------------------------------------------------

def write_temp_file(filename: str, content: bytes) -> str:
    """Write bytes to a secure temp file. Returns the path."""
    tmp = tempfile.NamedTemporaryFile(
        prefix="jdcv_",
        suffix="_" + filename,
        delete=False,
    )
    tmp.write(content)
    tmp.close()
    return tmp.name


def secure_delete(filepath: str) -> None:
    """Overwrite then delete a temp file."""
    try:
        size = os.path.getsize(filepath)
        with open(filepath, "wb") as f:
            f.write(secrets.token_bytes(min(size, 4096)))
        os.remove(filepath)
    except OSError:
        pass
