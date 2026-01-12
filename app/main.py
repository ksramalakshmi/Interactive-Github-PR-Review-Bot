from fastapi import FastAPI, Request, Header, HTTPException
import hmac
import hashlib
import os
from app.graph import app_graph

from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

GITHUB_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET").encode()

def verify_signature(payload: bytes, signature: str):
    mac = hmac.new(GITHUB_SECRET, payload, hashlib.sha256)
    expected = "sha256=" + mac.hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

@app.post("/webhook")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None),
    x_github_event: str = Header(None)
):
    body = await request.body()
    verify_signature(body, x_hub_signature_256)

    payload = await request.json()
    
    # LOG DEBUG: Print every event type received
    print(f"DEBUG: Received Webhook Event: {x_github_event}")

    if x_github_event == "pull_request":
        action = payload.get("action")
        if action in {"opened", "synchronize"}:
            owner = payload["repository"]["owner"]["login"]
            repo = payload["repository"]["name"]
            pr_number = payload["pull_request"]["number"]
            
            initial_state = {
                "owner": owner,
                "repo": repo,
                "pr_number": pr_number,
                "diff_text": None,
                "added_lines": [],
                "findings": [],
                "deduped_findings": []
            }
            app_graph.invoke(initial_state)

    elif x_github_event == "pull_request_review_comment":
        from app.conversation import handle_conversation
        handle_conversation(payload)

    return {"status": "ok"}