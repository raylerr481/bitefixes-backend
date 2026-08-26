# BiteFixes Backend

`bitefixes-backend` is the **specialized enterprise backend and intelligence system for BiteFixes.com**.

It powers BiteFixes CRM SaaS and its authorized business workflows. It is not the general Bitey IA Supracerebro.

## Bitey IA Empresarial

BiteFixes uses **Bitey IA Empresarial**, the contextual enterprise manifestation of Bitey IA. It maintains Bitey IA's architecture, capabilities and general intelligence while operating with authorized BiteFixes business context.

```text
BITEY IA
Supracerebro
     │
     ▼
BITEY IA EMPRESARIAL
     │
     ▼
BiteFixes Backend
     │
     ├── CRM
     ├── Customers
     ├── Tickets
     ├── Services
     ├── Company knowledge
     ├── Conversations/memory
     ├── Workflows
     └── authorized AI capabilities
```

The Bitey IA Empresarial context is used within authorized BiteFixes channels. It does not restrict or replace the general Bitey IA product.

## Channels

- `bitefixes-web` — BiteFixes.com website/frontend and contextual AI entry point.
- `bitefixes-app` — BiteFixes mobile channel.
- `bitey-ai` — WordPress enterprise integration channel.

The floating assistant on BiteFixes Web/App is **Bitey IA Empresarial** and uses the authorized BiteFixes CRM/business context.

## Core responsibilities

- FastAPI API and enterprise runtime.
- Supabase persistence.
- Company AI Profile and business context.
- Customer and conversation memory.
- Company knowledge and retrieval.
- Intelligent web research.
- Intent detection and service resolution.
- Tickets, customers, services and workflows.
- Authorized external AI collaboration.
- Tenant isolation and permissions.
- Observability and production deployment.

## Context boundary

BiteFixes context includes authorized company/site information, CRM records, customers, tickets, services, conversations, approved documents, knowledge and workflows.

This context is **scoped to BiteFixes**. Private customer/company data must never become unrestricted general Bitey IA memory or leak across tenants.

Authorized, privacy-safe/generalizable knowledge or capabilities may enrich the wider Bitey IA ecosystem without exposing private operational data.

## Relationship with Bitey IA

```text
Bitey IA
= general AI / Supracerebro

Bitey IA Empresarial
= same Bitey IA architecture/capabilities + authorized enterprise context

BiteFixes Backend
= authoritative BiteFixes CRM/business backend and enterprise intelligence layer
```

The systems relate and can enrich one another through explicit APIs/contracts, but BiteFixes does not replace or limit the general Bitey IA Supracerebro.

## Security

- Provider credentials remain server-side.
- Tenant and permission boundaries are mandatory.
- Client applications never hold authoritative business intelligence.
- External providers are collaborators, not the source of truth.
- Business-critical decisions remain controlled by the backend.
- Tests must cover API, security, memory, workflows and integrations.
