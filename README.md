# BiteFixes Backend

`bitefixes-backend` is the **FastAPI backend and specialized enterprise AI brain for BiteFixes.com**.

It serves BiteFixes.com and its authorized channels. It remains independent from the general Bitey IA web application.

## Product identity

**BiteFixes Backend** = specialized enterprise brain for BiteFixes.com.

It is not the general Bitey IA brain and must not be merged with `bitey-web` simply because both projects use similar AI architecture.

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
   BiteFixes enterprise brain
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
- External AI provider collaboration.
- Authorized channel contracts.
- Security, tenant isolation and provider credential protection.
- Tests, observability and production deployment.

## Relationship with Bitey IA

```text
Bitey IA (`bitey-web`)
= general web AI experience / reusable intelligence foundation

BiteFixes Backend (`bitefixes-backend`)
= specialized enterprise brain for BiteFixes.com
```

BiteFixes-specific business rules, services, tickets, customers and workflows stay here. They should not be copied into the general Bitey IA project.

Bitey IA may consume authorized enterprise capabilities through explicit APIs/contracts. The existence of a shared ecosystem does not grant automatic access to private BiteFixes data.

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
| `bitey-web` | **Bitey IA** | General web AI experience + intelligence foundation |
| `bitey-ai` | **Bitey AI Enterprise WordPress Plugin** | Global WordPress enterprise channel |
| `bitefixes-backend` | **BiteFixes Backend** | Specialized BiteFixes enterprise brain |
| `bitefixes-app` | **BiteFixes App** | Mobile BiteFixes channel |

## Engineering rules

1. Preserve the working FastAPI/Supabase architecture.
2. Keep BiteFixes business logic here.
3. Never expose provider credentials to clients.
4. Enforce tenant and permission boundaries at the backend.
5. Keep channel contracts explicit and backward compatible where possible.
6. Do not make external AI providers the source of truth.
7. Do not copy this business brain into `bitey-web` or a WordPress plugin.
8. Add tests for API, security, memory, workflows and integrations.
9. Validate production behavior with logs and observability.

## Production principle

Changes must preserve the existing authorized BiteFixes channels and avoid breaking the website widget, WhatsApp, Telegram or mobile contracts.
