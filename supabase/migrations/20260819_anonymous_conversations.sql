-- Bitey conversational identity: do not create a customer merely because a visitor says hello.
-- Apply this migration before enabling anonymous-first conversations.

alter table if exists public.conversations
    alter column customer_id drop not null;

alter table if exists public.messages
    alter column customer_id drop not null;

create table if not exists public.conversation_sessions (
    id uuid primary key default gen_random_uuid(),
    company_id bigint not null,
    conversation_id bigint references public.conversations(id) on delete cascade,
    channel text not null default 'website',
    external_conversation_id text,
    name text,
    last_name text,
    phone text,
    email text,
    preferred_contact_channel text,
    language text,
    collected_fields jsonb not null default '{}'::jsonb,
    status text not null default 'anonymous',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists conversation_sessions_company_idx
    on public.conversation_sessions(company_id);
create index if not exists conversation_sessions_external_idx
    on public.conversation_sessions(company_id, channel, external_conversation_id);

comment on table public.conversation_sessions is
    'Transient/progressive Bitey identity context. A customer is created only when business workflow requires identification.';
