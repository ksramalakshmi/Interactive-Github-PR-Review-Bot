from fastapi import FastAPI, Request, Header, HTTPException
import hmac
import hashlib
import os
from app.reviewer import handle_pull_request

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

    if x_github_event == "pull_request":
        action = payload.get("action")
        if action in {"opened", "synchronize"}:
            handle_pull_request(payload)

    return {"status": "ok"}