from app.github import reply_to_comment
from app.llm import call_llm
from app.supabase_client import supabase

def handle_conversation(payload):
    """
    Handles pull_request_review_comment events.
    check if it's a reply to the bot, and if so, generate a response.
    """
    try:
        # 1. Basic Validation
        action = payload.get("action")
        comment = payload.get("comment", {})
        
        # We only care about created comments
        if action != "created":
            return
            
        # Check if the sender is a bot to avoid loops
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
            # Fallback: strict bot check above might have failed if we are a 'User' type bot.
            # But better to fail safe if we can't identify ourselves?
            # Proceeding cautiously.

        # Check if it is a reply (has in_reply_to_id)
        parent_id = comment.get("in_reply_to_id")
        if not parent_id:
            return # Top-level comment, ignore for now

        # Idempotency Check
        try:
            # Check if we already processed this comment
            existing = supabase.table("processed_comments").select("comment_id").eq("comment_id", comment["id"]).execute()
            if existing.data:
                print(f"Skipping duplicate processing for comment {comment['id']}")
                return
        except Exception as e:
            print(f"Error checking idempotency: {e}")
            # Proceed cautiously or return? Proceeding might cause dups, but safe failure mode depends on pref.
            # Let's proceed but log.

        # 2. Extract Context
        owner = payload["repository"]["owner"]["login"]
        repo = payload["repository"]["name"]
        pr_number = payload["pull_request"]["number"]
        
        diff_hunk = comment.get("diff_hunk")
        user_body = comment.get("body")
        
        #Ideally we would fetch the parent comment body here to know what the bot said.
        # But for MVP, we can rely on the diff_hunk and the user question.
        # If we really need the parent comment, we can use the GitHub API to fetch 'parent_id'.
        # Let's assume the user context is enough for "Why is this a bug?" given the diff.
        
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
        # We reuse call_llm with CONVERSATION_MODE to pass raw prompt.
        # Use line=0 as dummy.
        response = call_llm(system_prompt, "CONVERSATION_MODE", 0, conversation_prompt)
        
        # Handle response (call_llm returns JSON by default for code reviews, but for raw mode it returns what? 
        # Wait, app.llm.call_llm attempts json.loads(content).
        # We need to ensure call_llm can return raw string if json parse fails or if we want raw string.
        # Currently llm.py forces JSON.
        # I should verify llm.py behavior for non-JSON output. 
        """
        if content == "NO_ISSUES": return None
        return json.loads(content)
        """
        # ERROR: ConfigurableAgent expects JSON, but Conversation expects text.
        # I need to handle this in llm.py or force JSON here.
        # Let's force JSON here: { "reply": "..." }
        
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
