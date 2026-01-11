from app.github import get_pr_diff, post_review_comment
from app.agents.registry import AGENTS
from app.diff_parser import extract_added_lines
from app.dedup import deduplicate_findings

def handle_pull_request(payload):
    owner = payload["repository"]["owner"]["login"]
    repo = payload["repository"]["name"]
    pr_number = payload["pull_request"]["number"]

    # Fetch full PR diff (important!)
    diff_text = get_pr_diff(owner, repo, pr_number)
    added_lines = extract_added_lines(diff_text)

    all_findings = []

    for change in added_lines:
        file = change["file"]
        line = change["line"]
        code = change["code"]

        for agent in AGENTS:
            try:
                result = agent.analyze(file=file, line=line, code=code)
            except Exception as e:
                result = {"comment": f"Agent error: {e}", "severity": "low"}

            if result:
                result["agent"] = agent.name
                result["file"] = file
                result["line"] = line
                all_findings.append(result)

    # Deduplicate findings before posting
    deduped_findings = deduplicate_findings(all_findings)

    # Post comments to GitHub
    for item in deduped_findings:
        comment_body = _format_comment(item)
        post_review_comment(owner, repo, pr_number,
                            path=item["file"], line_number=item["line"], body=comment_body)


def _format_comment(item):
    """Format a deduplicated finding for GitHub review comment."""
    header = f"⚠️ **{item['severity'].upper()} issue**"
    agents = ", ".join(item["agents"])

    body = f"{header}\n\n{item['comment']}\n\n**Agents:** {agents}"
    if item.get("suggestion"):
        body += f"\n\n**Suggestion:**\n{item['suggestion']}"
    return body