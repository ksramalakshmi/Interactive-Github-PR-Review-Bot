import json
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def call_llm(system_prompt, file, line, code):
    if file in ["EVALUATION_MODE", "CONVERSATION_MODE"]:
        # Special case for raw prompts
        prompt = code
    else:
        # Standard PR review prompt
        prompt = f"""
File: {file}
Line: {line}
Code:
{code}

Return either:
NO_ISSUES

OR JSON:
{{
  "severity": "low|medium|high",
  "comment": "short actionable feedback"
}}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )

    content = response.choices[0].message.content.strip()

    if content == "NO_ISSUES":
        return None

    print("RAW LLM OUTPUT:\n", repr(content))
    
    return json.loads(content)