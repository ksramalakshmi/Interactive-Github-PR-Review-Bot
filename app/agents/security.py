from app.agents.base import ReviewAgent
from app.llm import call_llm

class SecurityAgent(ReviewAgent):
    name = "Security"
    system_prompt = """
You are an application security expert.
Focus on secrets, injections, auth issues, and data leaks.
Ignore formatting and performance.

You MUST return only valid JSON.
Do not include explanations, markdown, or extra text.
If no issues are found, return an empty JSON object {}.
"""

    def analyze(self, file, line, code):
        return call_llm(self.system_prompt, file, line, code)