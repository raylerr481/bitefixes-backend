# Bitey 2.0 — Canonical Architecture

## Authority model

Bitey Core is authoritative. External AI providers are advisory and may enrich semantic understanding only. They cannot directly create customers, tickets, quotes, execute workflows, call enterprise tools, or mutate Supabase business data.

## Runtime path

`Channel/Plugin → API → Bitey Core → tenant context → language → customer/conversation → memory → intent/semantic resolution → knowledge → decision engine → workflow/tools → response → persistence`

## Enterprise context

`Company → Business Profile → Domains → Capabilities → AI Scope → Knowledge → Intent → Need → Requirements → Solution → Action → Agents/Tools → Workflows`

The commercial license controls AI scope/capabilities, not the application's legitimate access to its own operational data.

## AI provider policy

Providers are disabled by default. When enabled through Render secrets, `AIProvider` is a gateway. OpenRouter/free routing may be used first when configured; OpenAI is an optional provider. Secrets never belong in WordPress or Supabase client code.

## Tenant isolation

Every operational read/write must carry `company_id` and be enforced server-side. RLS/database policies remain the final data boundary.

## Learning policy

AI suggestions are candidates. Only validated/approved semantic knowledge is promoted to the canonical knowledge layer. This prevents hallucinations or malformed user input from silently corrupting the semantic dictionary.

## Plugin boundary

The WordPress plugin is a lightweight presentation/transport connector. It handles UI, language preference, browser conversation state and AJAX transport. Bitey Backend owns reasoning, memory, workflows, business rules and persistence.

## Canonical chat contract

Request: `company_id, message, phone, customer_name, channel, conversation_id, language_preference`.

Response: `response, customer_id, customer_name, conversation_id, language, language_source, intent, confidence, service/workflow/ticket metadata`.
