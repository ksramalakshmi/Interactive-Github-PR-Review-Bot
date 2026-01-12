from langgraph.graph import StateGraph, END
from app.state import AgentState
from app.github import get_pr_diff, post_review_comment
from app.supabase_client import get_active_agents
from app.agents.configurable import ConfigurableAgent
from app.diff_parser import extract_added_lines
from app.dedup import deduplicate_findings

def fetch_diff_node(state: AgentState):
    owner = state["owner"]
    repo = state["repo"]
    pr_number = state["pr_number"]
    
    diff_text = get_pr_diff(owner, repo, pr_number)
    added_lines = extract_added_lines(diff_text)
    
    return {"diff_text": diff_text, "added_lines": added_lines}

def analyze_node(state: AgentState):
    added_lines = state["added_lines"]
    all_findings = []
    
    for change in added_lines:
        file = change["file"]
        line = change["line"]
        code = change["code"]
        
    # Fetch agents dynamically
    active_agent_data = get_active_agents(state["owner"], state["repo"])
    
    # Instantiate agents
    agents = []
    if active_agent_data:
        agents = [
            ConfigurableAgent(
                name=a["name"], 
                system_prompt=a["system_prompt"],
                severity_threshold=a["severity_threshold"],
                file_patterns=a.get("file_patterns"),
                evaluation_prompt=a.get("evaluation_prompt")
            ) 
            for a in active_agent_data
        ]

    if active_agent_data is None:
        from app.agents.registry import AGENTS
        agents = AGENTS
        
    for change in added_lines:
        file = change["file"]
        line = change["line"]
        code = change["code"]
        
        for agent in agents:
            try:
                # Pass PR context for logging
                pr_details = {"repo": f"{state['owner']}/{state['repo']}", "pr_number": state["pr_number"]}
                result = agent.analyze(file=file, line=line, code=code, pr_details=pr_details)
            except Exception as e:
                result = {"comment": f"Agent error: {e}", "severity": "low"}
            
            if result:
                result["agent"] = agent.name
                result["file"] = file
                result["line"] = line
                all_findings.append(result)
                
    return {"findings": all_findings}

def deduplicate_node(state: AgentState):
    findings = state["findings"]
    deduped = deduplicate_findings(findings)
    return {"deduped_findings": deduped}

def post_comment_node(state: AgentState):
    owner = state["owner"]
    repo = state["repo"]
    pr_number = state["pr_number"]
    deduped_findings = state["deduped_findings"]
    
    for item in deduped_findings:
        comment_body = _format_comment(item)
        post_review_comment(owner, repo, pr_number, 
                            path=item["file"], line_number=item["line"], body=comment_body)
    
    return {}

def _format_comment(item):
    """Format a deduplicated finding for GitHub review comment."""
    header = f"⚠️ **{item['severity'].upper()} issue**"
    agents = ", ".join(item["agents"])

    body = f"{header}\n\n{item['comment']}\n\n**Agents:** {agents}"
    if item.get("suggestion"):
        body += f"\n\n**Suggestion:**\n{item['suggestion']}"
    return body

workflow = StateGraph(AgentState)

workflow.add_node("fetch_diff", fetch_diff_node)
workflow.add_node("analyze", analyze_node)
workflow.add_node("deduplicate", deduplicate_node)
workflow.add_node("post_comment", post_comment_node)

workflow.set_entry_point("fetch_diff")
workflow.add_edge("fetch_diff", "analyze")
workflow.add_edge("analyze", "deduplicate")
workflow.add_edge("deduplicate", "post_comment")
workflow.add_edge("post_comment", END)

app_graph = workflow.compile()
