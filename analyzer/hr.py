"""HR analysis — per-requirement matching + 8–12 interview questions."""

from llm_client import LLMClient
from utils.prompts import get_prompts


def analyze(
    client: LLMClient,
    jd_text: str,
    cv_text: str,
    personality_modifier: str = "",
) -> str:
    """Run HR-oriented JD/CV analysis and return the result.

    Args:
        client: LLM client instance.
        jd_text: Job description text.
        cv_text: CV/resume text.
        personality_modifier: Optional system prompt modifier for feedback style.
    """
    system, user_template = get_prompts("HR")
    if personality_modifier:
        system = f"{system}\n\n{personality_modifier}"
    user_prompt = user_template.format(jd=jd_text, cv=cv_text)
    return client.chat(system, user_prompt)
