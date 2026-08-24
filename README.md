# BiteFixes Backend

`bitefixes-backend` is the **specialized enterprise backend and AI system for BiteFixes.com**.

Its purpose is to operate BiteFixes business intelligence, customer context, company knowledge, services, tickets, workflows and authorized AI capabilities. It is a specialized system within the broader Bitey ecosystem, not the general Bitey AI application.

## Product purpose

**BiteFixes Backend** = the operational intelligence and API layer for BiteFixes.com.

It provides the authoritative server-side environment for BiteFixes business data and workflows while exposing controlled APIs to authorized channels.

## Architecture

```text
BiteFixes.com
  ├─ website / AI widget
  ├─ WhatsApp
  ├─ Telegram
  ├─ BiteFixes App
  └─ other authorized channels
          ↓
   BiteFixes Backend
          ↓
   BiteFixes enterprise intelligence
      ├─ Company AI Profile
      ├─ customer context + memory
      ├─ company knowledge
      ├─ intelligent web research
      ├─ intent / service / workflow engine
      ├─ tickets + customers
      ├─ external AI collaboration
      └─ tenant / permission controls
```

## Core responsibilities

- FastAPI API and enterprise runtime.
- Supabase persistence.
- Company AI Profile and business context.
- Customer and conversation memory.
- Company knowledge and retrieval.
- Intelligent web research.
- Intent detection and service resolution.
- Tickets, customers and operational workflows.
- Authorized external AI provider collaboration.
- Channel contracts for website, mobile and other approved interfaces.
- Security, tenant isolation and provider credential protection.
- Tests, observability and production deployment.

## Relationship with Bitey AI

```text
Bitey AI
= independent general AI product and intelligence layer

BiteFixes Backend
= specialized enterprise intelligence and operational backend for BiteFixes.com
```

Bitey AI may use BiteFixes capabilities through explicit, authorized APIs/contracts. BiteFixes-specific business rules, customers, services, tickets and workflows remain here.

BiteFixes data is never automatically exposed to the general Bitey AI product. Authorization, tenant boundaries and privacy controls remain mandatory.

## Relationship with client applications

- `bitefixes-app` is a mobile client/channel for BiteFixes.
- `bitey-ai-app` will be the independent mobile client/channel for general Bitey AI.
- `bitey-web` is the main web application for general Bitey AI.
- `bitey-ai` is the WordPress enterprise plugin/channel.

Clients do not contain the authoritative business intelligence or provider credentials.

## Enterprise context and tenant isolation

Company context can include authorized website information, onboarding data, approved documents, conversation history, customer information, services, operational knowledge and Company AI Profile settings.

All context must respect:

- authorization;
- privacy;
- retention policies;
- tenant isolation;
- least privilege;
- provider credential protection.

A research result does not automatically become permanent company knowledge.

## External AI providers

External AI models are collaborators selected by the backend. They do not become the identity or authority of BiteFixes. Provider selection, context authorization, business rules and operational decisions remain controlled by this backend.

## Ecosystem

| Repository | Product | Role |
|---|---|---|
| `bitey-web` | **Bitey AI Web** | General Bitey AI web application on Cloudflare |
| `bitey-ai-app` | **Bitey AI App** | General Bitey AI Android application |
| `bitey-ai` | **Bitey AI Enterprise WordPress Plugin** | Global WordPress enterprise channel |
| `bitefixes-backend` | **BiteFixes Backend** | Specialized BiteFixes enterprise intelligence/backend |
| `bitefixes-app` | **BiteFixes App** | BiteFixes mobile channel |

## Engineering rules

1. Preserve the working FastAPI/Supabase architecture.
2. Keep BiteFixes business logic here.
3. Never expose provider credentials to clients.
4. Enforce tenant and permission boundaries at the backend.
5. Keep channel contracts explicit and backward compatible where possible.
6. Do not make external AI providers the source of truth.
7. Do not copy the BiteFixes business brain into client applications or the general Bitey AI web application.
8. Add tests for API, security, memory, workflows and integrations.
9. Validate production behavior with logs and observability.

## Production principle

Changes must preserve authorized BiteFixes channels and avoid breaking the website widget, WhatsApp, Telegram or mobile contracts.
