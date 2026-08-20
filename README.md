# BiteFixes Backend / Bitey Core

FastAPI backend and intelligence core for **Bitey AI**, designed to serve BiteFixes first and evolve into a multi-tenant SaaS platform for companies using branded AI assistants across web, WordPress, APIs and messaging channels.

## Role in the platform

```text
Bitey SaaS / Universal Widget / WordPress / Channels
                         |
                  Bitey Cloud API
                         |
                  BiteFixes Backend
                         |
        +----------------+----------------+
        |                |                |
      Memory            RAG          AI Router
        |                |                |
     Supabase      FAISS/Qdrant/Chroma   |
                                         |
                         +---------------+----------------+
                         |        |        |        |
                       Groq    Gemini      HF      Ollama
```

The backend is the authoritative layer for business context, tenant isolation, workflows, tool permissions, observability and AI orchestration. Provider models are replaceable infrastructure, not the business core.

## Core capabilities

- FastAPI API and Bitey Core runtime.
- Supabase persistence for customers, conversations, messages, tickets, services and knowledge.
- AI provider routing with optional Groq, Gemini, Hugging Face and Ollama integrations.
- RAG/vector-store architecture using FAISS, Qdrant and Chroma adapters.
- Web Intelligence and source verification.
- Customer memory and operational context.
- Intent detection, service resolution and business workflows.
- Ticket and customer management.
- Incident recording and remediation foundations.
- Provider health and AI infrastructure diagnostics.
- GitHub Actions automated tests.
- Render deployment target.

## AI strategy

Bitey should select the best available provider for the task instead of coupling the application to a single model vendor.

Typical strategy:

1. Use a fast/low-cost provider for simple requests.
2. Use RAG when company knowledge is required.
3. Use Web Intelligence when current external information is required.
4. Use stronger/multimodal providers when the task requires them.
5. Fail over safely when a provider is unavailable or rate-limited.
6. Fall back to deterministic Bitey Core behavior when external AI is unavailable.

OpenAI can be supported as an **optional official API provider** when an `OPENAI_API_KEY` is supplied. A ChatGPT subscription is not treated as an API credential.

## Vector and knowledge layer

The vector layer is designed to be replaceable:

- **FAISS** — local/high-speed vector search and development.
- **Qdrant** — persistent/scalable production vector search.
- **Chroma** — alternative local/development vector store.

All production retrieval must enforce tenant isolation. A vector query must never be allowed to retrieve another company's private knowledge.

## Multi-tenant / white-label architecture

Bitey is intended to support multiple companies on the same platform. Each tenant can have a branded assistant with its own:

- assistant name;
- display name;
- language;
- personality/tone;
- logo/avatar;
- knowledge base;
- customers and conversations;
- workflows and permissions;
- enabled AI providers/channels.

Example:

```text
Bitey Cloud
  ├── BiteFixes → Bitey
  ├── Company A → Nexa
  └── Company B → Luna
```

The tenant boundary must be preserved in database queries, vector retrieval, memory, logs, tools and provider context.

## Incident and self-healing architecture

Operational failures should be recorded instead of disappearing into application logs.

```text
Error
  ↓
Incident
  ↓
Fingerprint / classify
  ↓
Safe automatic remediation?
  ├─ yes → repair → test → resolve
  └─ no  → alert → human approval
```

Examples of safe remediation candidates include provider failover, retry, cache invalidation and vector-index rebuilding. High-risk business mutations require authorization and verification.

## API principles

The backend is the shared intelligence API for:

- Bitey SaaS web application;
- WordPress plugin;
- universal website widget;
- custom applications through SDK/API;
- future WhatsApp and other channel connectors.

Clients must not receive provider secrets. Provider credentials remain server-side in environment/secrets management.

## Development

Typical local setup:

```bash
python -m venv .venv
# activate the environment
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Optional AI/RAG dependencies are maintained separately where appropriate so the core can remain usable without every provider installed.

## Configuration

Use environment variables/secrets for:

- Supabase URL and service credentials;
- Groq API key;
- Gemini API key;
- Hugging Face token/provider configuration;
- Ollama endpoint;
- Qdrant URL/API key where applicable;
- optional OpenAI API key;
- application authentication and security secrets.

Never commit real credentials.

## Testing and production readiness

The project includes automated test workflows. Production promotion should require successful validation of:

- application startup;
- Supabase connectivity;
- authentication/authorization;
- tenant isolation;
- AI provider health/fallback;
- embeddings and vector retrieval;
- RAG quality;
- Web Intelligence;
- incident creation;
- remediation/rollback behavior;
- WordPress → backend → AI end-to-end flow.

Failures should be registered in the incident/test observability layer and repaired before promotion when possible.

## Deployment

Render is the current deployment platform for the backend. Production configuration should use Render environment variables/secrets and separate staging/production validation.

## Project relationship

- `bitefixes-backend` — Bitey Core/backend/intelligence layer.
- `bitey-ai` — WordPress plugin and website channel.
- `bitey-search-core` — web/search intelligence service.
- Future `Bitey Cloud Web` — independent ChatGPT-like SaaS interface.

BiteFixes is the first real company/tenant implementation; the architecture is intentionally being generalized for other businesses.

## Status

Active development toward **Bitey Cloud Platform v1**. This README describes the target architecture; individual integrations must still pass their real environment and end-to-end tests before being considered production-ready.

## License

See the repository license and project terms before redistribution or commercial deployment.