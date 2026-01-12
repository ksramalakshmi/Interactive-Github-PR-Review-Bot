-- Create the agents table
create table agents (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  system_prompt text not null,
  severity_threshold text check (severity_threshold in ('low', 'medium', 'high')),
  enabled boolean default true,
  file_patterns text[],
  allowed_repos text[],
  excluded_repos text[],
  evaluation_prompt text,
  config jsonb default '{}'::jsonb,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create review_logs table
create table review_logs (
    id uuid default gen_random_uuid() primary key,
    agent_name text not null,
    repo_name text,
    pr_number int,
    file_path text,
    line_number int,
    severity text,
    outcome text,
    
    -- Metrics
    score int,
    relevance int,
    accuracy int,
    actionability int,
    clarity int,
    
    -- Content
    code_snippet text,
    finding_text text,
    
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable Row Level Security (RLS)
alter table agents enable row level security;
alter table review_logs enable row level security;

-- Create policies
create policy "Enable read access for all users" on agents for select using (true);
create policy "Enable read access for all users" on review_logs for select using (true);
create policy "Enable insert access for all users" on review_logs for insert with check (true);

-- Insert default agents with DETAILED Evaluation Prompts
insert into agents (name, system_prompt, severity_threshold, enabled, file_patterns, evaluation_prompt, allowed_repos, excluded_repos) values
('Bug', 'You are a senior software engineer. Focus only on logic bugs, runtime errors, and edge cases. Ignore style and security. You MUST return only valid JSON. Do not include explanations, markdown, or extra text. If no issues are found, return an empty JSON object {}.', 'medium', true, array['*.py', '*.js', '*.ts'], 'Review the reported bug. Evaluate on 4 metrics (0-10): Relevance (Does it matter?), Accuracy (Is it correct?), Actionability (Can it be fixed?), Clarity (Is it clear?). Return JSON: {"score": 0-10, "relevance": 0-10, "accuracy": 0-10, "actionability": 0-10, "clarity": 0-10}', null, null),
('Security', 'You are a security expert. Focus on potential security vulnerabilities. You MUST return only valid JSON. Do not include explanations, markdown, or extra text. If no issues are found, return an empty JSON object {}.', 'high', true, array['*.py', '*.js', '*.ts', '*.html', '*.css'], 'Review the security warning. Evaluate on 4 metrics (0-10): Relevance (Real threat?), Accuracy (Technically correct?), Actionability (Fixable?), Clarity (Clear?). Return JSON: {"score": 0-10, "relevance": 0-10, "accuracy": 0-10, "actionability": 0-10, "clarity": 0-10}', null, null),
('Performance', 'You are a performance engineer. Focus on code efficiency and potential bottlenecks. You MUST return only valid JSON. Do not include explanations, markdown, or extra text. If no issues are found, return an empty JSON object {}.', 'medium', true, array['*.py', '*.js', '*.ts'], 'Rate performance suggestion (0-10). Evaluate: Relevance (Impact?), Accuracy (Correct?), Actionability (Fixable?), Clarity. Return JSON: {"score": 0-10, "relevance": 0-10, "accuracy": 0-10, "actionability": 0-10, "clarity": 0-10}', null, null),
('Style', 'You are a code style reviewer. Focus on PEP8 and readability. You MUST return only valid JSON. Do not include explanations, markdown, or extra text. If no issues are found, return an empty JSON object {}.', 'low', true, array['*.py'], 'Rate style nitpick (0-10). Evaluate: Relevance (Standard violation?), Accuracy, Actionability, Clarity. Return JSON: {"score": 0-10, "relevance": 0-10, "accuracy": 0-10, "actionability": 0-10, "clarity": 0-10}', null, null);
