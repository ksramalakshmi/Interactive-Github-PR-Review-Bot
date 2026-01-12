from app.github import reply_to_comment
from app.llm import call_llm
from app.supabase_client import supabase

def handle_conversation(payload):
    """
    Handles pull_request_review_comment events.
    check if it's a reply to the bot, and if so, generate a response.
    """
    try:
        action = payload.get("action")
        comment = payload.get("comment", {})
        
        if action != "created":
            return
            
        sender = payload.get("sender", {})
        login = sender.get("login", "").lower()
        
        # 1. Standard Bot Checks
        if sender.get("type") == "Bot" or "[bot]" in login or login == "github-actions": 
            print(f"Ignoring bot comment from {login}")
            return

        # 2. Self-Identity Check (fetch who we are authenticated as)
        try:
            from app.github import get_current_user
            me = get_current_user()
            my_login = me.get("login", "").lower()
            if login == my_login:
                print(f"Ignoring own comment from {login}")
                return
        except Exception as e:
            print(f"Error fetching current user: {e}")

        # Check if it is a reply (has in_reply_to_id)
        parent_id = comment.get("in_reply_to_id")
        if not parent_id:
            return

        # Idempotency Check
        try:
            # Check if we already processed this comment
            existing = supabase.table("processed_comments").select("comment_id").eq("comment_id", comment["id"]).execute()
            if existing.data:
                print(f"Skipping duplicate processing for comment {comment['id']}")
                return
        except Exception as e:
            print(f"Error checking idempotency: {e}")

        # 2. Extract Context
        owner = payload["repository"]["owner"]["login"]
        repo = payload["repository"]["name"]
        pr_number = payload["pull_request"]["number"]
        
        diff_hunk = comment.get("diff_hunk")
        user_body = comment.get("body")

        # 3. Construct Prompt
        system_prompt = "You are a helpful coding assistant. You previously reviewed this code. The user is asking a follow-up question. Answer clearly and concisely."
        
        conversation_prompt = f"""
Code Context:
{diff_hunk}

User Question:
{user_body}

Answer the user.
You MUST return valid JSON with a single key "reply" containing your markdown formatted answer.
Example: {{ "reply": "This is a bug because..." }}
"""

        # 4. Generate Reply
        response = call_llm(system_prompt, "CONVERSATION_MODE", 0, conversation_prompt)

        """
        if content == "NO_ISSUES": return None
        return json.loads(content)
        """
        
        if isinstance(response, dict) and "reply" in response:
            reply_text = response["reply"]
            
            # 5. Post Reply
            reply_to_comment(owner, repo, pr_number, comment["id"], reply_text)
            print(f"Replied to comment {comment['id']}")
            
            # Mark as processed
            try:
                supabase.table("processed_comments").insert({"comment_id": comment["id"]}).execute()
            except Exception as e:
                print(f"Error marking comment as processed: {e}")
            
    except Exception as e:
        print(f"Error handling conversation: {e}")
