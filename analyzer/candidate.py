"""Candidate analysis — JD/CV matching + interview prep."""

from llm_client import LLMClient
from utils.prompts import get_prompts


def analyze(client: LLMClient, jd_text: str, cv_text: str) -> str:
    """Run candidate-oriented JD/CV analysis and return the result."""
    system, user_template = get_prompts("Candidate")
    user_prompt = user_template.format(jd=jd_text, cv=cv_text)
    return client.chat(system, user_prompt)
