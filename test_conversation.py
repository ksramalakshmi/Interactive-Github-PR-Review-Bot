import unittest
from unittest.mock import patch, MagicMock
import os
os.environ["OPENAI_API_KEY"] = "dummy" # Mock env for import
from app.conversation import handle_conversation

class TestConversation(unittest.TestCase):
    def test_reply_to_user(self):
        # Mock Payload: A user replying "Why?" to a bot comment
        payload = {
            "action": "created",
            "repository": {
                "owner": {"login": "test_owner"},
                "name": "test_repo"
            },
            "pull_request": {
                "number": 10
            },
            "sender": {
                "type": "User",
                "login": "test_user"
            },
            "comment": {
                "id": 12345,
                "in_reply_to_id": 99999, # Reply to bot
                "body": "Why is this a bug?",
                "diff_hunk": "def foo():\n+    return True"
            }
        }
        
        # Mock LLM Response
        mock_llm_response = {"reply": "Because it returns True always."}
        
        # Mock Supabase
        mock_supabase = MagicMock()
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        # Mock Current User (Bot Identity) - DIFFERENT from sender
        mock_bot_identity = {"login": "my-bot-user"}
        
        with patch("app.conversation.call_llm", return_value=mock_llm_response) as mock_llm, \
             patch("app.conversation.reply_to_comment") as mock_reply, \
             patch("app.conversation.supabase", mock_supabase), \
             patch("app.github.get_current_user", return_value=mock_bot_identity):
             
             handle_conversation(payload)
             
             # Verify Checked Idempotency
             mock_supabase.table.assert_any_call("processed_comments")
             
             # Verify Reply Posted
             mock_reply.assert_called_once()
             print("SUCCESS: Conversation reply triggered.")

    def test_ignore_own_comment(self):
        # Payload where sender IS the bot
        payload = {
            "action": "created",
            "sender": {"login": "my-bot-user", "type": "User"}, # Even if type is User
            "comment": {"id": 123, "in_reply_to_id": 1}
        }
        
        mock_bot_identity = {"login": "my-bot-user"}
        
        with patch("app.conversation.call_llm") as mock_llm, \
             patch("app.github.get_current_user", return_value=mock_bot_identity), \
             patch("app.conversation.supabase"):
            
            handle_conversation(payload)
            mock_llm.assert_not_called()
            print("SUCCESS: Own comment ignored.")

    def test_duplicate_ignore(self):
        # Payload that is already processed
        payload = {
            "action": "created",
            "repository": {"owner": {"login": "o"}, "name": "r"},
            "pull_request": {"number": 1},
            "sender": {"type": "User"},
            "comment": {"id": 123, "in_reply_to_id": 1}
        }
        
        mock_supabase = MagicMock()
        # Mock exists
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{"comment_id": 123}]
        
        with patch("app.conversation.call_llm") as mock_llm, \
             patch("app.conversation.supabase", mock_supabase):
            
            handle_conversation(payload)
            
            mock_llm.assert_not_called()
            print("SUCCESS: Duplicate comment ignored.")

    def test_ignore_bot_comment(self):
        # Payload from a bot (should ignore)
        payload = {
            "action": "created",
            "sender": {"type": "Bot"},
            "comment": {}
        }
        
        with patch("app.conversation.call_llm") as mock_llm:
            handle_conversation(payload)
            mock_llm.assert_not_called()
            print("SUCCESS: Bot comment ignored.")

if __name__ == "__main__":
    unittest.main()
