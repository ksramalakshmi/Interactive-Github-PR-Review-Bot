from app.agents.base import ReviewAgent
from app.llm import call_llm

class PerformanceAgent(ReviewAgent):
    name = "Performance"
    system_prompt = """
You are a performance engineer.
Focus on inefficiencies, unnecessary work, and scaling issues.

You MUST return only valid JSON.
Do not include explanations, markdown, or extra text.
If no issues are found, return an empty JSON object {}.
"""

    def analyze(self, file, line, code):
        return call_llm(self.system_prompt, file, line, code)