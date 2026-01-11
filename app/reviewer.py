from app.github import get_pr_files, post_review_comment, get_pr_diff
from app.agents.registry import AGENTS
from app.diff_parser import extract_added_lines


def handle_pull_request(payload):
    owner = payload["repository"]["owner"]["login"]
    repo = payload["repository"]["name"]
    pr_number = payload["pull_request"]["number"]

    files = get_pr_files(owner, repo, pr_number)
    comments = []

    for f in files:
        if not f.get("patch"):
            continue

        diff_text = get_pr_diff(owner, repo, pr_number)
        added_lines = extract_added_lines(diff_text)

        for change in added_lines:
            for agent in AGENTS:
                result = agent.analyze(
                    file=change["file"],
                    line=change["line"],
                    code=change["code"]
                )

                if result:
                    comments.append({
                        "path": change["file"],
                        "line": change["line"],
                        "side": "RIGHT",
                        "body": f"[{agent.name}] {result['comment']}"
                    })

    if comments:
        post_review_comment(owner, repo, pr_number, comments)