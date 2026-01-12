-- Create review_logs table
create table review_logs (
    id uuid default gen_random_uuid() primary key,
    agent_name text not null,
    repo_name text,
    pr_number int,
    file_path text,
    line_number int,
    severity text,
    outcome text, -- posted, filtered_severity, filtered_score, error
    
    -- Metrics (0-10)
    score int, -- Overall
    relevance int,
    accuracy int,
    actionability int,
    clarity int,
    
    -- Content
    code_snippet text,
    finding_text text,
    
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS
alter table review_logs enable row level security;
create policy "Enable read access for all users" on review_logs for select using (true);
create policy "Enable insert access for all users" on review_logs for insert with check (true);

-- Update default agents with DETAILED evaluation prompts
update agents set evaluation_prompt = 'Review the reported bug. Evaluate on 4 metrics (0-10): Relevance (Does it matter?), Accuracy (Is it correct?), Actionability (Can it be fixed?), Clarity (Is it clear?). Return JSON: {"score": 0-10, "relevance": 0-10, "accuracy": 0-10, "actionability": 0-10, "clarity": 0-10}' where name = 'Bug';

update agents set evaluation_prompt = 'Review the security warning. Evaluate on 4 metrics (0-10): Relevance (Real threat?), Accuracy (Technically correct?), Actionability (Fixable?), Clarity (Clear?). Return JSON: {"score": 0-10, "relevance": 0-10, "accuracy": 0-10, "actionability": 0-10, "clarity": 0-10}' where name = 'Security';

update agents set evaluation_prompt = 'Rate performance suggestion (0-10). Evaluate: Relevance (Impact?), Accuracy (Correct?), Actionability (Fixable?), Clarity. Return JSON: {"score": 0-10, "relevance": 0-10, "accuracy": 0-10, "actionability": 0-10, "clarity": 0-10}' where name = 'Performance';

update agents set evaluation_prompt = 'Rate style nitpick (0-10). Evaluate: Relevance (Standard violation?), Accuracy, Actionability, Clarity. Return JSON: {"score": 0-10, "relevance": 0-10, "accuracy": 0-10, "actionability": 0-10, "clarity": 0-10}' where name = 'Style';
