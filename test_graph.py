import os
import sys
from unittest.mock import patch, MagicMock

# Set dummy API key before imports to avoid OpenAI client init error
os.environ["OPENAI_API_KEY"] = "dummy_key"

# Now we can safely import
from app.graph import app_graph
from app.state import AgentState

def test_graph_execution():
    print("Starting Graph Verification...")
    
    # Mock data
    mock_diff = """diff --git a/test.py b/test.py
new file mode 100644
index 0000000..e69de29
--- /dev/null
+++ b/test.py
@@ -0,0 +1,5 @@
+def secure_function():
+    password = "hardcoded_secret" # This should trigger a security warning
+    print(password)
+"""
    
    mock_added_lines = [
        {"file": "test.py", "line": 2, "code": '    password = "hardcoded_secret" # This should trigger a security warning'}
    ]

    # Mock return values for call_llm (Must be dicts)
    mock_bug_finding = {"comment": "Potential bug found", "severity": "medium", "suggestion": "fix it"}
    mock_security_finding = {"comment": "Security issue: Hardcoded password", "severity": "high", "suggestion": "Use env var"}
    mock_active_agents = [
        {"name": "Security", "system_prompt": "sec prompt", "severity_threshold": "high", "file_patterns": ["*.py"], "evaluation_prompt": "eval prompt"},
    ]
    
    mock_sec_finding = {"comment": "Security Issue", "severity": "high"}
    mock_sec_eval = {"score": 8, "reason": "Real issue"}

    # Patch the external dependencies used in the graph nodes
    with patch("app.graph.get_pr_diff", return_value=mock_diff) as mock_get_diff, \
         patch("app.graph.post_review_comment") as mock_post_comment, \
         patch("app.graph.extract_added_lines", return_value=mock_added_lines), \
         patch("app.graph.get_active_agents", return_value=mock_active_agents) as mock_get_agents, \
         patch("app.agents.configurable.call_llm", side_effect=[mock_sec_finding, mock_sec_eval]) as mock_call_llm:
        
        initial_state = {
            "owner": "test_owner",
            "repo": "test_repo",
            "pr_number": 1,
            "diff_text": None,
            "added_lines": [],
            "findings": [],
            "deduped_findings": []
        }
        
        # Invoke the graph
        try:
            result = app_graph.invoke(initial_state)
            
            print("\nGraph execution completed.")
            print(f"Findings found: {len(result.get('findings', []))}")
            deduped = result.get('deduped_findings', [])
            print(f"Deduped findings: {len(deduped)}")
            
            # Verify get_pr_diff was called
            mock_get_diff.assert_called_once_with("test_owner", "test_repo", 1)
            mock_get_agents.assert_called_once_with("test_owner", "test_repo")
            
            if len(deduped) > 0:
                print("Issues found, verifying comment posting...")
                mock_post_comment.assert_called()
                print("SUCCESS: Comment posting triggered.")
                
                # Print the comment body of the first finding to verify formatting
                print("\nSample Comment Body:")
                # We can grab the args from the mock call
                # mock_post_comment might be called multiple times.
                args, kwargs = mock_post_comment.call_args_list[0]
                print(kwargs.get('body', 'No body found'))
                
            else:
                print("WARNING: No issues found. Check mock returns.")
                
        except Exception as e:
            print(f"Graph execution failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_graph_execution()
