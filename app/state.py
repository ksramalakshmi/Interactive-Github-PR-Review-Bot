from typing import TypedDict, List, Any, Optional

class AgentState(TypedDict):
    owner: str
    repo: str
    pr_number: int
    diff_text: Optional[str]
    added_lines: List[dict]
    findings: List[dict]
    deduped_findings: List[dict]
