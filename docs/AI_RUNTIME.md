# Bitey Core AI Runtime

Bitey Core is the authoritative application brain. GitHub stores the source; Render runs the backend; Supabase stores tenant data and business knowledge; vector stores provide retrieval; model providers are replaceable advisory engines.

## Provider order

The runtime is intentionally local/free-first:

1. Ollama (local, when explicitly enabled)
2. Groq free tier (when available/configured)
3. OpenRouter free models (when available/configured)
4. Gemini free tier (when available/configured)

Free availability, quotas and model eligibility are controlled by each provider and can change. Bitey must never promise unlimited free inference.

## Authority boundary

External models may:

- provide semantic suggestions;
- answer general questions;
- assist with language and extraction;
- provide independent advisory answers.

External models may not directly:

- create or modify customers;
- set prices;
- approve payments;
- expose another tenant's data;
- execute business tools;
- change permissions;
- become the source of truth.

Bitey Core + authorized tenant data remain authoritative.

## Data boundary

Payment-card data, CVV/CVC, secrets and credentials must not be placed in model prompts, memory, RAG indexes or application logs. Context passed to providers must be minimized and governed by the existing AI policy layer.

## Environment variables

```text
OLLAMA_ENABLED=false
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=llama3.2:3b

GROQ_ENABLED=true
GROQ_API_KEY=
GROQ_MODEL=llama-3.1-8b-instant

OPENROUTER_ENABLED=true
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openrouter/free

GEMINI_ENABLED=true
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash
```

Never commit real credentials. Configure secrets only in the deployment environment.
