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

## Getting Started

### Step 1 — Install Python 3.12

ResumeBridge needs Python. Pick your platform below — you only need to do this once.

**Windows**
1. Download the installer: [python.org/downloads](https://www.python.org/downloads/) — click the yellow **Download Python 3.12** button
2. Run the downloaded `.exe` file
3. **IMPORTANT:** check the box **"Add Python to PATH"** at the bottom of the installer, then click **Install Now**
4. Once done, restart your computer

**macOS**
1. Download the installer: [python.org/downloads](https://www.python.org/downloads/) — click the yellow **Download Python 3.12** button
2. Open the downloaded `.pkg` file and follow the steps (click Continue → Continue → Install)
3. Or if you have [Homebrew](https://brew.sh) installed, open Terminal and run:
   ```
   brew install python@3.12
   ```

**Linux (Ubuntu / Debian)**
```
sudo apt update && sudo apt install python3.12 python3.12-venv -y
```

### Step 2 — Get an API Key

ResumeBridge connects to an AI provider. Pick one and sign up for a free API key:

| Provider | Sign-up | Free tier |
|----------|---------|-----------|
| DeepSeek | [platform.deepseek.com](https://platform.deepseek.com) | Yes |
| OpenAI | [platform.openai.com](https://platform.openai.com) | Requires credit |
| Anthropic | [console.anthropic.com](https://console.anthropic.com) | Requires credit |
| Qwen | [dashscope.aliyun.com](https://dashscope.aliyun.com) | Yes (100K tokens/day) |
| GLM | [open.bigmodel.cn](https://open.bigmodel.cn) | Yes |
| Kimi | [platform.moonshot.cn](https://platform.moonshot.cn) | Yes |

### Step 3 — Launch the App

Open **Terminal** (macOS/Linux) or **Command Prompt** (Windows), then:

```bash
# Clone the project
git clone https://github.com/jacalwu/ResumeBridge.git
cd ResumeBridge/jd_cv_app

# Run it
# macOS / Linux:
chmod +x run_app.sh && ./run_app.sh

# Windows:
run_app.bat
```

The script sets up everything automatically. When you see a URL starting with `http://localhost:8501`, open it in your browser.

**No terminal?** Alternatively, you can:
1. Open the `jd_cv_app` folder in your file explorer
2. Double-click `run_app.bat` (Windows) or `run_app.sh` (macOS/Linux)

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
