"""HR analysis — per-requirement matching + 8–12 interview questions."""

from llm_client import LLMClient
from utils.prompts import get_prompts


def analyze(client: LLMClient, jd_text: str, cv_text: str) -> str:
    """Run HR-oriented JD/CV analysis and return the result."""
    system, user_template = get_prompts("HR")
    user_prompt = user_template.format(jd=jd_text, cv=cv_text)
    return client.chat(system, user_prompt)
