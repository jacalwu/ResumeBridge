"""HeadHunter analysis — Candidate mode or HR recommendation mode."""

from llm_client import LLMClient
from utils.prompts import get_prompts


def analyze(
    client: LLMClient,
    jd_text: str,
    cv_text: str,
    mode: str,
    personality_modifier: str = "",
) -> str:
    """
    Run headhunter-oriented JD/CV analysis.

    mode: 'Candidate' → deep-dive questions for the candidate
          'HR'        → recommendation report for the hiring company

    Args:
        client: LLM client instance.
        jd_text: Job description text.
        cv_text: CV/resume text.
        mode: 'Candidate' or 'HR'.
        personality_modifier: Optional system prompt modifier for feedback style.
    """
    system, user_template = get_prompts("HeadHunter", mode)
    if personality_modifier:
        system = f"{system}\n\n{personality_modifier}"
    user_prompt = user_template.format(jd=jd_text, cv=cv_text)
    return client.chat(system, user_prompt)
