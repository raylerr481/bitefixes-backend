# BiteFixes Backend — Bitey AI Engine

BiteFixes Backend is the FastAPI service that powers Bitey, the conversational AI and business intelligence engine behind BiteFixes. It connects the WordPress client, Supabase data, business workflows, web intelligence and optional AI providers through a controlled orchestration layer.

## What Bitey does

- Detects user intent and resolves services/capabilities.
- Maintains customer context, tickets and conversational history.
- Uses web intelligence with caching, source scoring and verification.
- Routes reasoning tasks to interchangeable AI providers.
- Supports local/open inference first, with optional cloud fallbacks.
- Prepares enterprise knowledge for RAG and vector retrieval.
- Keeps external AI advisory: Bitey Core remains authoritative for business data, permissions and actions.

## AI provider strategy

```text
                         +----------------------+
                         |      Bitey Core      |
                         | intent / CRM / rules |
                         +----------+-----------+
                                    |
                            AI Orchestrator
                                    |
          +-------------------------+--------------------------+
          |                         |                          |
       Ollama                   Gemini                      Groq
     local/open             optional free tier          optional free tier
          |                         |                          |
          +-------------------------+--------------------------+
                                    |
                           Hugging Face Hub
                         Meta Llama / other models
```

Providers are optional. Ollama is the local/open-source default and requires no cloud API key. Gemini, Groq and Hugging Face are enabled only when their credentials are present. The orchestrator automatically tries the next available provider if a provider fails.

## RAG and open-source ecosystem

Bitey is intentionally compatible with several layers rather than coupling the core to one framework:

- **LangChain:** optional integration/orchestration utilities.
- **LlamaIndex:** optional document and RAG pipelines.
- **Flowise / Langflow:** optional external visual workflow builders.
- **Ollama:** local model runtime.
- **Hugging Face Hub:** model discovery and inference providers.
- **Meta Llama:** supported through compatible runtimes/providers.
- **Qdrant / Chroma / FAISS:** optional vector retrieval backends.
- **Supabase/PostgreSQL:** system of record for Bitey business data.

The lightweight production requirements stay small. Install `requirements-ai.txt` only when RAG/framework features are actually enabled, avoiding unnecessary memory and build costs on small Render instances.

## Configuration

Copy `.env.example` into the deployment environment. Never commit API keys.

Important variables include:

- `AI_DEFAULT_PROVIDER=ollama`
- `GEMINI_API_KEY` / `GEMINI_MODEL`
- `GROQ_API_KEY` / `GROQ_MODEL`
- `HF_API_TOKEN` / `HF_MODEL`
- `OLLAMA_BASE_URL` / `OLLAMA_MODEL`
- `VECTOR_BACKEND`, `QDRANT_URL`, `QDRANT_API_KEY`

## Free/open-source principle

Bitey does not assume that a cloud API is permanently free. Free tiers are subject to provider quotas and policy changes. The architecture therefore treats cloud services as optional accelerators and keeps a local/open-source route through Ollama and open models.

## Companion plugin

The WordPress client is [`raylerr481/bitey-ai`](https://github.com/raylerr481/bitey-ai).

## Version

BiteFixes Backend 2.4.x — modular AI provider routing and open-source AI/RAG integration foundation.
