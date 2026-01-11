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

-- Enable Row Level Security (RLS)
alter table agents enable row level security;

-- Create a policy that allows read access to everyone (for now, or restrict as needed)
create policy "Enable read access for all users" on agents for select using (true);

-- Insert default agents
insert into agents (name, system_prompt, severity_threshold, enabled, file_patterns, evaluation_prompt, allowed_repos, excluded_repos) values
('Bug', 'You are a senior software engineer. Focus only on logic bugs, runtime errors, and edge cases. Ignore style and security. You MUST return only valid JSON. Do not include explanations, markdown, or extra text. If no issues are found, return an empty JSON object {}.', 'medium', true, array['*.py', '*.js', '*.ts'], 'Review the reported bug. Rate confidence (0-10) that this is a real semantic bug and not intentional behavior. Return JSON: {"score": 0-10, "reason": "..."}', null, null),
('Security', 'You are a security expert. Focus on potential security vulnerabilities. You MUST return only valid JSON. Do not include explanations, markdown, or extra text. If no issues are found, return an empty JSON object {}.', 'high', true, array['*.py', '*.js', '*.ts', '*.html', '*.css'], 'Review the security warning. Rate severity and validity (0-10). Is this a true vulnerability? Return JSON: {"score": 0-10, "reason": "..."}', null, null),
('Performance', 'You are a performance engineer. Focus on code efficiency and potential bottlenecks. You MUST return only valid JSON. Do not include explanations, markdown, or extra text. If no issues are found, return an empty JSON object {}.', 'medium', true, array['*.py', '*.js', '*.ts'], 'Rate the impact (0-10) of this performance suggestion. Return JSON: {"score": 0-10, "reason": "..."}', null, null),
('Style', 'You are a code style reviewer. Focus on PEP8 and readability. You MUST return only valid JSON. Do not include explanations, markdown, or extra text. If no issues are found, return an empty JSON object {}.', 'low', true, array['*.py'], 'Rate the helpfulness (0-10) of this style nitpick. Return JSON: {"score": 0-10, "reason": "..."}', null, null);
