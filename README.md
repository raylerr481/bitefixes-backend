# BiteFixes Backend / Bitey Core

FastAPI backend and intelligence core for **Bitey AI**. BiteFixes is the first real company context in which Bitey is being developed and measured, while the platform is designed to evolve into a multi-tenant SaaS for branded enterprise AI assistants.

## Canonical architecture: one brain, multiple channels

`bitefixes-backend` is the authoritative intelligence repository. The platform separates communication channels from intelligence and evolution:

- **Bitey Channel** — communication paths such as WordPress, the public Bitey web facade, mobile app, WhatsApp, voice/phone and API.
- **Bitey IA** — the backend intelligence that interprets company context, conversation context and authorized knowledge and coordinates reasoning and tools.
- **Bitey Evolution** — longitudinal observation, evaluation and controlled improvement.

```text
User
  |
  +--> bitey-web --------+
  +--> bitey-ai ---------+
  +--> bitefixes-app ----+----> Bitey Backend
  +--> future channels --+             |
                                       +--> Company AI Profile
                                       +--> context + memory
                                       +--> knowledge
                                       +--> intelligent web research
                                       +--> intent/service/workflows
                                       +--> external AI collaboration
                                       +--> evolution/evaluation
                                       |
                                       +----> response
```

See [`docs/PLATFORM-ARCHITECTURE.md`](docs/PLATFORM-ARCHITECTURE.md) for the canonical channel contract and research/evolution model.

## Enterprise context acquisition

Bitey may use authorized context available through the corresponding channel and company resources, including company web pages and approved web evidence, onboarding/company-provided text, supported-channel messages, authorized attachments/documents, conversation history, permitted customer identity signals, company services/capabilities and operational knowledge, and other explicitly authorized sources.

Context acquisition must respect tenant isolation, permissions, privacy and source authorization. Context is evidence for reasoning; it is not an instruction to expose secrets or private data.

## Intelligent web research

Web research is part of the dynamic interaction engine, not a separate chatbot feature. Bitey decides whether current authorized context is sufficient. If not, it can research public information, evaluate sources, extract relevant evidence and use that evidence in the current reasoning context.

```text
interaction
  ↓
understand context + information need
  ↓
existing knowledge sufficient?
  ├─ yes → reason
  └─ no  → research → verify evidence → reason
  ↓
response
  ↓
post-response observation/evaluation
  ↓
controlled evolution
```

Research evidence does not automatically become permanent company knowledge. Persistence requires provenance, authorization, confidence and retention rules.

## Bitey IA response model

The response path remains direct:

```text
message
  ↓
resolve company + channel + conversation
  ↓
assemble relevant authorized context
  ↓
use knowledge / memory / research as needed
  ↓
Bitey IA / external cognitive provider
  ↓
response
```

There must be no mandatory evaluator, score gate or approval chain between the user message and the response merely to measure quality. Safety and authorization controls remain mandatory where applicable. Quality evaluation belongs to the observation/evolution path.

Conversational continuity is required: established facts must remain available to later turns instead of being repeatedly requested.

## External AI relationship

External models can provide reasoning, multimodal capabilities, research or evaluation. They do not become the business identity of Bitey. The backend controls which authorized context is supplied, provider selection and tenant isolation.

## Core platform capabilities

- FastAPI API and Bitey Core runtime.
- Supabase persistence for companies, profiles, conversations, messages, customers, tickets, services, knowledge and evolution data.
- AI provider routing and collaboration.
- RAG/vector-store architecture with tenant isolation.
- Intelligent web research and source verification.
- Customer memory and operational context.
- Intent detection, service resolution and business workflows.
- Ticket and customer management.
- Incident recording and remediation foundations.
- Provider health and AI infrastructure diagnostics.
- Automated tests and production observability.
- Render deployment target.

## Multi-tenant / white-label architecture

Each tenant has an isolated business identity and can have its own assistant identity, language, tone, branding, knowledge, customers, conversations, workflows, permissions and enabled channels. Tenant isolation must be preserved in database queries, retrieval, memory, logs, tools and provider context.

## Security

Provider credentials remain server-side. Channels are untrusted clients and must authenticate/authorize requests. Company-private context must never cross tenant boundaries. Attachments, web evidence and channel-derived identity must be processed according to authorization and retention rules.

## Repository responsibilities

- `bitefixes-backend` — authoritative Bitey IA, business context, intelligence orchestration, research, memory and evolution.
- `bitey-ai` — WordPress channel/plugin.
- `bitey-web` — public web facade for a ChatGPT-like Bitey experience; no independent intelligence core.
- `bitefixes-app` — mobile application for accessing BiteFixes and Bitey; no independent intelligence core.

The old `bitey-search-core` reference has intentionally been removed from this canonical repository map until a real repository/service is identified and its ownership is confirmed.

## Deployment

Render is the current backend deployment platform. Production configuration uses Render secrets/environment variables. Changes should be validated through automated tests and end-to-end channel tests before promotion.

## Status

Active development toward **Bitey Platform v1 and an evolving Bitey IA**. This repository is the authoritative place for the backend architecture and longitudinal evolution model.
