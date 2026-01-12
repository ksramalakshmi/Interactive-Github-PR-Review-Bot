import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Warning: Supabase credentials not found in environment variables.")
    supabase: Client = None
else:
    supabase: Client = create_client(url, key)

def get_active_agents(owner: str = None, repo: str = None):
    """
    Fetch active agents from Supabase.
    Optionally filter by owner/repo if we implement repo-specific config later.
    """
    if not supabase:
        print("Supabase client not initialized. Returning empty list.")
        return []

    try:
        response = supabase.table("agents").select("*").eq("enabled", True).execute()
        agents = response.data
        
        if not owner or not repo:
            return agents
            
        filtered_agents = []
        current_repo = f"{owner}/{repo}"
        
        for agent in agents:
            allowed = agent.get("allowed_repos")
            excluded = agent.get("excluded_repos")
            
            # Check Exclusion
            if excluded and current_repo in excluded:
                continue
                
            # Check Allowance
            if allowed and current_repo not in allowed:
                continue
                
            filtered_agents.append(agent)
            
        return filtered_agents
    except Exception as e:
        print(f"Error fetching agents from Supabase: {e}")
        return None

def log_finding_outcome(finding_data: dict):
    """
    Logs the outcome of an agent's finding to Supabase.
    finding_data should contain:
    - agent_name, repo_name, pr_number, file_path, line_number
    - severity, outcome
    - score, relevance, accuracy, actionability, clarity (metrics)
    - code_snippet, finding_text (content)
    """
    try:
        # Check if client is initialized
        if not supabase:
            return
            
        supabase.table("review_logs").insert(finding_data).execute()
        print(f"Logged finding for {finding_data.get('agent_name')} (Outcome: {finding_data.get('outcome')})")
    except Exception as e:
        print(f"Error logging finding to Supabase: {e}")
