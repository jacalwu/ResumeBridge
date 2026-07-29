# ResumeBridge

**AI-powered JD/CV matching for candidates, HR, and headhunters. PII is masked locally before any text reaches the LLM.**

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Why I Built This

Job hunting and hiring are exhausting. Candidates spend hours tailoring resumes. HR sifts through hundreds of CVs. Headhunters juggle both sides. AI can help — but most tools send your private data to the cloud without a second thought.

ResumeBridge exists to **make everyone's life easier**:

- Candidates get instant, honest feedback on how their CV stacks up.
- HR gets structured, evidence-based matching instead of gut feelings.
- Headhunters get deep insights to pitch the right person to the right role.

All of it happens on your machine, with personal data stripped before it ever reaches an LLM.

---

## What It Does

ResumeBridge analyzes the match between a Job Description and a CV through three lenses:

| Role | What You Get |
|------|-------------|
| 🧑‍💼 **Candidate** | JD breakdown, 0–100 match score, Strong/Partial/Gap table, 6–8 interview questions with answer strategies |
| 🏢 **HR** | Per-requirement matching with CV evidence, overall assessment, 8–12 targeted interview questions |
| 🎯 **HeadHunter** | Candidate mode: 10–15 deep-dive questions. HR mode: recommendation summary, highlights, risks, referral letter draft |

---

## 🔒 Privacy

- **PII masking** — names, emails, phone numbers, addresses, and ID numbers are detected and replaced with placeholders **before** any text is sent to the LLM API
- **Encryption at rest** — analysis history and API key are encrypted (Fernet) on disk
- **Local-first** — the app runs on your machine; only masked text leaves it
- **Configurable retention** — auto-purge old records on startup
- **History-off mode** — results can be shown without ever being written to disk

---

## Quick Start

```bash
# macOS / Linux
chmod +x run_app.sh && ./run_app.sh

# Windows
run_app.bat
```

The script creates a virtual environment, installs dependencies, and launches Streamlit at `http://localhost:8501`.

### Manual Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

---

## Project Structure

```
jd_cv_app/
├── app.py                  # Streamlit UI
├── llm_client.py           # LLM abstraction (OpenAI + Anthropic)
├── db.py                   # SQLite layer (encrypted fields)
├── config.py               # Settings persistence (encrypted API key)
├── privacy.py              # PII masking, encryption, secure temp files
├── analyzer/
│   ├── candidate.py        # Candidate analysis
│   ├── hr.py               # HR analysis
│   └── headhunter.py       # HeadHunter analysis
├── utils/
│   ├── reader.py           # PDF / DOCX / TXT parser
│   └── prompts.py          # LLM prompt templates
├── requirements.txt
├── run_app.bat             # Windows launcher
├── run_app.sh              # macOS / Linux launcher
└── README.md
```

---

## Requirements

- Python ≥ 3.10
- Streamlit ≥ 1.28
- [pdfplumber](https://github.com/jsvine/pdfplumber), [python-docx](https://github.com/python-openxml/python-docx)
- [cryptography](https://cryptography.io)

---

## License

MIT — see [LICENSE](LICENSE). Use it, improve it, just keep the attribution.

---

## Contributing

Issues and pull requests are welcome. For significant changes, open an issue first to discuss what you'd like to change.
