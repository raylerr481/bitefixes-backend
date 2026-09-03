# BiteFixes Backend

`bitefixes-backend` is the **specialized enterprise backend for BiteFixes.com** and the production foundation for the configurable BiteFixes AI-agent and SaaS platform.

The existing FastAPI + Supabase + Render architecture is preserved and extended incrementally. This repository is not replaced by a new backend.

## Product ownership and boundaries

**BiteFixes is the product/company platform.** The following capabilities belong to BiteFixes and must remain within the BiteFixes product boundary:

- BiteFixes CRM
- Customer, conversation, lead, opportunity, sale, service and ticket lifecycle
- Creation and configuration of AI agents for BiteFixes and its customers
- SaaS capabilities for offering those AI agents and business automations to other companies
- Customer channels and business integrations used by BiteFixes
- Bitey IA as the intelligence technology used by BiteFixes

**Bitey IA is technology developed/used by BiteFixes; it is not a separate CRM and does not absorb the BiteFixes CRM.** Bitey provides intelligence, reasoning, conversation and automation capabilities to the BiteFixes platform while the CRM remains a BiteFixes business system.

**Bitey System Bots Trading (Bitey SBT) is a separate product/project.** Its trading, market, portfolio and broker-related systems must not be mixed with the BiteFixes CRM, BiteFixes SaaS, customer data or operational workflows.

Neo4j and MongoDB are not part of the current architecture. Supabase remains the canonical data, memory and knowledge persistence platform for this backend.

## BiteFixes pilot model

BiteFixes.com remains a public business website. **Authentication is required only for the private Support Portal**, where authorized BiteFixes personnel manage customers, employees, conversations, tickets, services and sales.

Customers do not authenticate to the administrative Support Portal. They reach the business through the customer channels:

- WhatsApp
- Telegram
- Configurable web Bitey widget/globe

```text
                         BITEFIXES PLATFORM
                                │
             ┌──────────────────┼──────────────────┐
             │                  │                  │
          CRM              AI AGENTS             SaaS
             │                  │                  │
             └──────────────────┼──────────────────┘
                                │
                           Bitey IA
                     (intelligence technology)
                                │
                     ┌──────────┴──────────┐
                     │                     │
                Conversations          Automation
                     │                     │
                     └──────────┬──────────┘
                                │
                           Supabase
                                │
                              Render

Bitey SBT / Trading → SEPARATE PROJECT
```

## CRM is exclusively BiteFixes

The BiteFixes CRM is a first-class BiteFixes subsystem. It is not a generic CRM owned by Bitey IA and must not be merged with unrelated products.

Its lifecycle is:

```text
Customer
  ↓
Conversation
  ↓
Lead / Opportunity
  ↓
Sale
  ↓
Service
  ↓
Ticket / Resolution
  ↓
History + Memory
```

Bitey IA may interpret conversations, assist employees, recommend actions or automate authorized workflows, but CRM records and CRM business rules remain part of BiteFixes and are governed by this backend.

## AI-agent creation and SaaS

**AI-agent creation is a BiteFixes capability.** BiteFixes can use Bitey IA as its underlying intelligence technology to create/configure agents for different businesses.

The SaaS model is therefore:

```text
BiteFixes
   │
   ├── CRM
   ├── AI Agent Builder
   ├── Business Automations
   └── SaaS / Multi-tenant Services
            │
            ├── Tenant A → its agent + CRM data
            ├── Tenant B → its agent + CRM data
            └── Tenant N → its agent + CRM data
```

Each tenant must have strict data and authorization isolation. A tenant's CRM, conversations, customers, tickets and operational data must never be exposed to another tenant.

## Customer channels and Support Portal

```text
Public BiteFixes.com
       │
       ├── services / sales / contact
       │
       └── Support Portal (private)
                 │
                 └── authenticated staff
                       ├── owner
                       ├── admin
                       ├── technician
                       └── worker

Customer channels
   ├── WhatsApp ─┐
   ├── Telegram ─┼──> BiteFixes Conversation/AI Layer
   └── Web widget┘            │
                              ▼
                         BiteFixes CRM
                              │
                           Supabase
                              │
                           Render
```

## SaaS evolution

BiteFixes is the first real production tenant. The same BiteFixes platform is being made configurable for other companies without changing the core architecture.

Each tenant can eventually define its own:

- company/display name
- assistant/agent name
- logo and visual identity
- language and currency
- services and business knowledge
- authorized employees and roles
- enabled customer channels
- enabled automations and agent capabilities

The internal intelligence technology remains **Bitey IA**, while the customer-facing assistant name and Portal branding can be different for each tenant (white-label capable).

## Data boundary

The backend treats the authenticated employee context as authoritative for private Portal access. Customer records and operational data are scoped to the employee's company/tenant.

```text
Tenant A → customers, conversations, tickets, services, sales
Tenant B → customers, conversations, tickets, services, sales

Tenant A data MUST NOT be visible to Tenant B.
```

## Architecture

- FastAPI backend remains the authoritative BiteFixes business/API layer.
- Supabase remains the canonical persistence layer for BiteFixes data, memory and knowledge.
- Render remains the production runtime.
- Bitey IA remains the intelligence/conversation technology used by BiteFixes.
- BiteFixes CRM remains a BiteFixes subsystem.
- AI-agent creation and SaaS remain BiteFixes product capabilities.
- WhatsApp, Telegram and Web are customer ingress channels.
- The Support Portal is the private operational interface for company personnel.
- Tenant configuration is additive and backward-compatible with the BiteFixes pilot.
- Bitey SBT remains outside this architecture and must not share BiteFixes CRM/business workflows.

## API configuration metadata

`/info` and `/gateway/status` expose non-secret tenant presentation metadata and customer-channel configuration. Secrets and authoritative business data remain server-side.

Environment-backed presentation values include:

- `TENANT_KEY`
- `TENANT_DISPLAY_NAME`
- `TENANT_ASSISTANT_NAME`
- `TENANT_LOGO_URL`
- `TENANT_WHITE_LABEL`

These settings do not replace database authorization or tenant isolation.

## Security

- Provider credentials remain server-side.
- Public website pages do not require Portal authentication.
- Private Portal endpoints require an authenticated authorized employee.
- Owner/Admin permissions are required for employee-management views.
- Tenant/company boundaries are mandatory.
- Browser-supplied company identity is never authoritative.
- Customer/company private data must not leak across tenants.
- Business-critical decisions remain controlled by the backend.
- CRM data and BiteFixes SaaS data must not be mixed with Bitey SBT trading data.

## Related repositories

- `bitefixes-web` — public BiteFixes website/frontend and Web channel.
- `bitey-ai` — Bitey IA technology/integration layer used by BiteFixes.
- `bitefixes-app` — mobile channel; future customer/employee experiences can use the same authorized APIs.
- `bitey-system-bots-trading` — separate trading product; not part of BiteFixes CRM/SaaS.

The goal is to **evolve the existing BiteFixes product into a robust AI-agent and SaaS platform while keeping the BiteFixes CRM, Bitey IA technology, and separate products clearly bounded.**
