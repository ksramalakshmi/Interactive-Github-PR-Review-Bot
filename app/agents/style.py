# app/agents/style.py
from app.agents.base import ReviewAgent
from app.llm import call_llm

class StyleAgent(ReviewAgent):
    name = "Style"
    system_prompt = """
You are a Python style reviewer.
Focus only on readability and best practices.
Ignore bugs and security.

You MUST return only valid JSON.
Do not include explanations, markdown, or extra text.
If no issues are found, return an empty JSON object {}.
"""

    def analyze(self, file, line, code):
        return call_llm(self.system_prompt, file, line, code)