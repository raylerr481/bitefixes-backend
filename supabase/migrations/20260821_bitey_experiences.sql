create table if not exists public.bitey_experiences (
    id uuid primary key default gen_random_uuid(),
    case_id text not null unique,
    problem text not null,
    symptoms jsonb not null default '[]'::jsonb,
    facts jsonb not null default '{}'::jsonb,
    action text,
    outcome text,
    success boolean,
    source text not null default 'case',
    confidence numeric(4,3) not null default 0 check (confidence >= 0 and confidence <= 1),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_bitey_experiences_problem
    on public.bitey_experiences(problem);

create index if not exists idx_bitey_experiences_success
    on public.bitey_experiences(problem, success);

alter table public.bitey_experiences enable row level security;

-- Backend access uses the Supabase service role. No public client policy is added.
