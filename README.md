# BiteFixes Backend

`bitefixes-backend` is the **specialized enterprise backend and intelligence system for BiteFixes.com**.

Its purpose is to operate BiteFixes business intelligence, customer context, company knowledge, services, tickets, workflows and authorized AI capabilities. It is a specialized BiteFixes system, not the general Bitey IA supracerebro.

## Product purpose

**BiteFixes Backend** = the authoritative operational intelligence and API layer for BiteFixes.com.

It provides the server-side environment for BiteFixes business data and workflows while exposing controlled APIs to authorized channels.

## Architecture

```text
BiteFixes.com
  ├─ BiteFixes Web
  ├─ BiteFixes App
  ├─ Bitey IA enterprise plugin/channel
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

## Relationship with Bitey IA

```text
Bitey IA
= independent general AI product
= Bitey Web supracerebro + Bitey IA App client

BiteFixes Backend
= specialized enterprise intelligence/backend for BiteFixes.com
```

Bitey IA may use BiteFixes capabilities through explicit, authorized APIs/contracts. BiteFixes-specific business rules, customers, services, tickets and workflows remain here.

BiteFixes data is never automatically exposed to the general Bitey IA product. Authorization, tenant boundaries and privacy controls remain mandatory.

## Relationship with channels

- `bitefixes-web` is the BiteFixes website/frontend.
- `bitefixes-app` is the BiteFixes mobile channel.
- `bitey-ai` is the Bitey IA enterprise WordPress channel.
- `bitey-web` is the general Bitey IA supracerebro and web application.
- `bitey-ia-app` is the general Bitey IA Android client.

Client applications do not contain authoritative business intelligence or provider credentials.

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
| `bitey-web` | **Bitey IA Web** | General Bitey IA supracerebro and Cloudflare web application |
| `bitey-ia-app` | **Bitey IA App** | General Bitey IA Android client |
| `bitey-ai` | **Bitey IA Enterprise WordPress Plugin** | Enterprise WordPress channel |
| `bitefixes-web` | **BiteFixes Web** | BiteFixes.com website/frontend |
| `bitefixes-backend` | **BiteFixes Backend** | This specialized enterprise intelligence/backend |
| `bitefixes-app` | **BiteFixes App** | BiteFixes mobile channel |

## Engineering rules

1. Preserve the working FastAPI/Supabase architecture.
2. Keep BiteFixes business logic here.
3. Never expose provider credentials to clients.
4. Enforce tenant and permission boundaries at the backend.
5. Keep channel contracts explicit and backward compatible where possible.
6. Do not make external AI providers the source of truth.
7. Do not copy the BiteFixes business brain into client applications or the general Bitey IA product.
8. Add tests for API, security, memory, workflows and integrations.
9. Validate production behavior with logs and observability.

## Production principle

Changes must preserve authorized BiteFixes channels and avoid breaking website, mobile, WordPress or other approved integrations.
