# BiteFixes Backend / Bitey Core

FastAPI backend and intelligence core for **Bitey AI**. BiteFixes is the first real company context in which Bitey is being developed and measured, while the platform is designed to evolve into a multi-tenant SaaS for branded enterprise AI assistants.

## Architectural principle: channel, intelligence, evolution

Bitey has three deliberately separated concerns:

1. **Bitey Channel** — the communication path: WordPress/web, WhatsApp, voice/phone, app, API and future authorized channels. A channel transports identity, messages and permitted attachments; it is not the intelligence core.
2. **Bitey IA** — Bitey's own evolving intelligence. It interprets company context, conversation context and authorized knowledge and produces useful business-grounded responses. External AI providers are collaborators/cognitive infrastructure, not the definition of Bitey.
3. **Bitey Evolution** — the longitudinal learning and evaluation layer. Responses must not be blocked by intermediate evaluations. Evaluations can run asynchronously and record how Bitey changes over time.

```text
Authorized Channel
      ↓
Identity + conversation/session
      ↓
Bitey Backend
      ↓
Company AI Profile + authorized context
      ↓
Bitey IA reasoning / external AI collaboration
      ↓
Immediate response to user
      │
      └──────────────→ asynchronous evaluation
                              ↓
                       evolution history
                              ↓
                    future Bitey improvements
```

## Enterprise context acquisition

Bitey may use authorized context available through the corresponding channel and company resources, including:

- company web pages and approved web evidence;
- onboarding/company-provided text;
- messages received through supported channels;
- authorized attachments and documents;
- conversation history;
- channel identity and permitted customer identity signals;
- company services, capabilities and operational knowledge;
- other explicitly authorized sources.

Context acquisition must respect tenant isolation, permissions, privacy and source authorization. Context is evidence for reasoning; it is not an instruction to expose secrets or private data.

## Bitey IA response model

The response path should remain direct:

```text
message
  ↓
resolve company + channel + conversation
  ↓
assemble relevant authorized context
  ↓
Bitey IA / external cognitive provider
  ↓
response
```

There must be **no mandatory evaluator, score gate or approval chain between the user message and the response** merely to measure quality. Quality evaluation belongs to the observability/evolution path unless a specific safety or authorization control is required.

The intelligence should preserve conversational continuity. If the user already established `device = mobile phone` and `problem = broken screen`, the next turn must use those facts instead of repeatedly asking for them.

## Longitudinal evolution and evaluation markers

Every meaningful evaluation event should be timestamped and associated with the relevant company, conversation/channel where permitted, Bitey version/build and evaluation criteria. The goal is to measure evolution rather than merely store isolated scores.

Recommended marker dimensions include:

- `context_grounding` — how well the response reflects authorized company/context evidence;
- `conversation_continuity` — whether previously established facts are retained and used;
- `business_alignment` — alignment with the company's real services and capabilities;
- `service_alignment` — whether the response identifies/advances the appropriate service or need;
- `factuality` — unsupported claims or contradictions;
- `helpfulness` — usefulness to the user;
- `safety_authorization` — appropriate handling of permissions and private information;
- `language_quality` — language and communication quality;
- `external_ai_collaboration` — quality of collaboration with external cognitive providers when used.

A longitudinal record should retain at least:

```text
marker_id
occurred_at
company_id
channel
conversation_id
bitey_version / build_id
context_snapshot_or_reference
evaluator_id / evaluator_type
criteria
scores
strengths
weaknesses
missing_context
result
change_reference
```

Scores must not be treated as permanent truth. They are measurements tied to a specific version, context and evaluation method.

## Evolution cycle

```text
real interaction
    ↓
response
    ↓
post-response observation/evaluation
    ↓
record marker
    ↓
compare against previous versions
    ↓
identify regression / improvement
    ↓
implement controlled change
    ↓
validate
    ↓
new version/build marker
```

Periodic reviews should compare a stable evaluation set and recent real-world samples. The comparison must answer: what improved, what regressed, why, and which change produced the difference.

## External AI relationship

External models can provide reasoning, multimodal capabilities, research or evaluation. They do not become the business identity of Bitey. Over time, Bitey IA should increasingly develop its own reusable capabilities and collaborate with external models where this improves outcomes.

Evaluation by external IAs is useful for measuring Bitey's evolution, but evaluation must remain observable/asynchronous and must not become an unnecessary response gate.

## Core platform capabilities

- FastAPI API and Bitey Core runtime.
- Supabase persistence for companies, profiles, conversations, messages, customers, tickets, services, knowledge and evolution data.
- AI provider routing and collaboration.
- RAG/vector-store architecture with tenant isolation.
- Web Intelligence and source verification.
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

## Deployment

Render is the current backend deployment platform. Production configuration uses Render secrets/environment variables. Changes should be validated through automated tests and end-to-end channel tests before promotion.

## Project relationship

- `bitefixes-backend` — Bitey Core, business context, intelligence orchestration and evolution observability.
- `bitey-ai` — WordPress/web channel.
- `bitey-search-core` — web/search intelligence service.
- Future SaaS/mobile/channel repositories — additional communication paths using the same intelligence core.

## Status

Active development toward **Bitey Platform v1 and an evolving Bitey IA**. This repository is the authoritative place for the backend architecture and longitudinal evolution model.
