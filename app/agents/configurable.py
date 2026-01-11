import fnmatch
from typing import List, Optional
from app.agents.base import ReviewAgent
from app.llm import call_llm

class ConfigurableAgent(ReviewAgent):
    def __init__(self, name: str, system_prompt: str, severity_threshold: str = "medium", file_patterns: Optional[List[str]] = None, evaluation_prompt: Optional[str] = None):
        self.name = name
        self.system_prompt = system_prompt
        self.severity_threshold = severity_threshold
        self.file_patterns = file_patterns
        self.evaluation_prompt = evaluation_prompt

    def should_analyze(self, file_path: str) -> bool:
        if not self.file_patterns:
            return True
        
        for pattern in self.file_patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False
    
    def _severity_to_int(self, severity: str) -> int:
        levels = {"low": 1, "medium": 2, "high": 3}
        return levels.get(severity.lower(), 1) # Default to low if unknown

    def analyze(self, file, line, code):
        if not self.should_analyze(file):
            return None

        # 1. Primary Analysis
        result = call_llm(self.system_prompt, file, line, code)
        
        # If no finding or error, return as is
        if not result or not isinstance(result, dict) or not result.get("comment"):
            return result

        # 2. Strict Severity Filtering
        finding_severity = result.get("severity", "low")
        if self._severity_to_int(finding_severity) < self._severity_to_int(self.severity_threshold):
            print(f"[{self.name}] Finding dropped. Severity '{finding_severity}' below threshold '{self.severity_threshold}'")
            return None

        # 3. Secondary Evaluation (if configured)
        if self.evaluation_prompt:
            try:
                finding_context = f"File: {file}\nLine: {line}\nCode: {code}\n\nProposed Finding:\n{result.get('comment')}"
                eval_result = call_llm(self.evaluation_prompt, "EVALUATION_MODE", 0, finding_context)
                
                if isinstance(eval_result, dict):
                    score = eval_result.get("score", 0)
                    
                    if self.severity_threshold == "high" and score < 5:
                        print(f"[{self.name}] Finding dropped. Severity: {self.severity_threshold}, Score: {score}")
                        return None
                    
                    result["evaluation_score"] = score
                    
            except Exception as e:
                print(f"[{self.name}] Evaluation failed: {e}. Proceeding with original finding.")

        return result
