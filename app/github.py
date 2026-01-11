import requests
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_pr_files(owner, repo, pr_number):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    res = requests.get(url, headers=HEADERS)
    res.raise_for_status()
    return res.json()

def post_review_comment(owner, repo, pr_number, comments):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    payload = {
        "event": "COMMENT",
        "comments": comments
    }
    res = requests.post(url, headers=HEADERS, json=payload)
    res.raise_for_status()

def get_pr_diff(owner, repo, pr_number):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = {
        **HEADERS,
        "Accept": "application/vnd.github.v3.diff"
    }
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    return res.text