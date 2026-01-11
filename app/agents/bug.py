# app/agents/bug.py
from app.agents.base import ReviewAgent
from app.llm import call_llm

class BugAgent(ReviewAgent):
    name = "Bug"
    system_prompt = """
You are a senior software engineer.
Focus only on logic bugs, runtime errors, and edge cases.
Ignore style and security.

You MUST return only valid JSON.
Do not include explanations, markdown, or extra text.
If no issues are found, return an empty JSON object {}.
"""

    def analyze(self, file, line, code):
        return call_llm(self.system_prompt, file, line, code)