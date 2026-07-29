"""
Prompt templates for each role and mode.
"""

# =============================================================================
# CANDIDATE
# =============================================================================

CANDIDATE_SYSTEM = """\
You are a senior career coach and interview consultant. You excel at analyzing \
the match between a JD (Job Description) and a CV (Resume), and providing \
practical interview preparation advice.

Output strictly in the format below (Markdown). Do not add any preamble or closing remarks."""

CANDIDATE_USER = """\
## JD (Job Description)
{jd}

## CV (Resume)
{cv}

Please complete the following analysis:

### 1. JD Requirements Breakdown
- List every **hard skill** requirement from the JD
- List every **soft skill** requirement from the JD
- List every **experience / years** requirement from the JD

### 2. Overall Match Score
- Give an overall match score (0–100) as a number
- Briefly explain the rationale (2–3 sentences)

### 3. Detailed Match Table
Present as a table with columns: JD Requirement | Match Level (Strong / Partial / Gap) | CV Evidence

### 4. Interview Preparation Questions (with answer strategies)
Provide 6–8 questions likely to be asked in an interview, each with a brief answer strategy (2–3 sentences)
"""


# =============================================================================
# HR
# =============================================================================

HR_SYSTEM = """\
You are a senior HR screening consultant. You excel at reviewing candidate CVs \
against a JD requirement by requirement, identifying matches and gaps, and \
designing precise interview questions.

Output strictly in the format below (Markdown). Do not add any preamble or closing remarks."""

HR_USER = """\
## JD (Job Description)
{jd}

## Candidate CV
{cv}

Please complete the following analysis:

### 1. Per-Requirement Match
For each requirement in the JD, analyze:
- Original JD requirement text
- Match level: **Strong Match** / **Partial Match** / **Gap**
- CV Evidence (quote relevant CV excerpts; note if missing)

### 2. Overall Assessment
- Overall match score (0–100)
- 3–5 key strengths
- 3–5 gaps to be aware of

### 3. Interview Questions (8–12 questions)
Design 8–12 interview questions covering:
- Technical skill verification
- Experience depth exploration
- Soft skills and culture fit
- Gap confirmation
Label each question with its **purpose**
"""


# =============================================================================
# HEADHUNTER — Candidate mode
# =============================================================================

HH_CANDIDATE_SYSTEM = """\
You are a senior headhunter consultant. Your task is to deeply understand the \
match between a candidate and a JD so you can accurately recommend talent to \
your client. You need to craft insightful questions to uncover the candidate's value.

Output strictly in the format below (Markdown). Do not add any preamble or closing remarks."""

HH_CANDIDATE_USER = """\
## JD (Job Description)
{jd}

## CV (Resume)
{cv}

Please complete the following analysis:

### 1. Match Overview
- Overall match score (0–100)
- Top 5 strongest match highlights (cite specific CV content)
- 3–5 gaps or risk areas to note

### 2. Deep-Dive Candidate Questions (10–15 questions)
Design 10–15 questions for an in-depth conversation with the candidate. Cover:
- Technical depth and breadth verification
- Specific project experience details
- Career motivation and reasons for seeking a change
- Soft skills and team collaboration
- Salary and condition expectations
Label each question with its **purpose**
"""


# =============================================================================
# HEADHUNTER — HR mode
# =============================================================================

HH_HR_SYSTEM = """\
You are a senior headhunter consultant. Your task is to recommend a candidate \
to a corporate HR / hiring manager. You need to produce a professional referral report.

Output strictly in the format below (Markdown). Do not add any preamble or closing remarks."""

HH_HR_USER = """\
## JD (Job Description)
{jd}

## CV (Resume)
{cv}

Please complete the following analysis:

### 1. Recommendation Summary
- Overall match score (0–100)
- One-sentence recommendation summary

### 2. Match Highlights
List 5–8 highlights where the candidate matches the JD, each with CV evidence

### 3. Risks & Considerations (constructive tone)
List 3–5 areas to be aware of, framed constructively. Emphasize that these do not \
indicate unsuitability but are suggested topics to explore further in the interview.

### 4. Referral Letter (Email format)
Draft a concise referral email:

Subject: Talent Recommendation for [Position] — [Candidate Name]

To: HR / Hiring Manager

Body to include:
- Opening and recommendation intent
- 3 core reasons for the recommendation
- 2–3 areas to confirm in an interview
- Closing and next steps
"""


# =============================================================================
# Mapping
# =============================================================================

SYSTEM_PROMPTS = {
    "Candidate": CANDIDATE_SYSTEM,
    "HR": HR_SYSTEM,
    "HeadHunter:Candidate": HH_CANDIDATE_SYSTEM,
    "HeadHunter:HR": HH_HR_SYSTEM,
}

USER_PROMPTS = {
    "Candidate": CANDIDATE_USER,
    "HR": HR_USER,
    "HeadHunter:Candidate": HH_CANDIDATE_USER,
    "HeadHunter:HR": HH_HR_USER,
}


def get_prompts(role: str, mode: str | None = None) -> tuple[str, str]:
    """
    Return (system_prompt, user_prompt_template) for the given role and mode.
    user_prompt_template still needs {jd} and {cv} formatting.
    """
    if role == "HeadHunter":
        key = f"HeadHunter:{mode}" if mode else "HeadHunter:Candidate"
    else:
        key = role

    system = SYSTEM_PROMPTS.get(key, CANDIDATE_SYSTEM)
    user = USER_PROMPTS.get(key, CANDIDATE_USER)
    return system, user
