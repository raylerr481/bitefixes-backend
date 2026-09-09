# BiteFixes Backend

`bitefixes-backend` is the **enterprise backend owned by BiteFixes**. It is the production foundation for BiteFixes CRM, BiteFixes SaaS, AI-agent implementation/creation and **Bitey IA Empresarial**, the contextual AI implementation used by each business.

## Ownership and boundaries

**BiteFixes owns:**
- BiteFixes CRM and its customer/conversation/lead/opportunity/sale/service/ticket lifecycle.
- AI-agent creation, configuration and implementation.
- BiteFixes SaaS and multi-tenant enterprise services.
- Customer channels and business automations.
- Bitey IA Empresarial implementations.

**Bitey IA Empresarial** is the contextual enterprise implementation of Bitey IA inside BiteFixes. Each business can have its own company context, memory, knowledge, rules, authorized data, tools, channels and assistant identity. It may use authorized CRM capabilities, but it does not own or absorb the CRM.

**Bitey IA Web** (`raylerr481/bitey-web`) is the separate **general/integral Bitey IA**: a general-purpose AI architecture, conceptually comparable to a general assistant such as ChatGPT. It can coordinate models, research, tools and specialized modules through explicit contracts. It does not own BiteFixes CRM, BiteFixes SaaS or enterprise agent implementations.

**Bitey IA WordPress plugin** (`raylerr481/bitey-ai`) is the WordPress integration/channel layer that provides the Web widget/globe. It is not the Bitey IA Web brain.

**Bitey SBT** is a separate trading project and must not be mixed with BiteFixes CRM, SaaS or enterprise customer data.

## Data architecture

**Supabase/Postgres is the canonical persistence platform for BiteFixes. Neo4j and MongoDB are excluded from the current architecture.**

```text
BiteFixes
 ├── CRM / SaaS / enterprise data
 ├── Bitey IA Empresarial
 └── WhatsApp / Telegram / Web globe
                ↓
         FastAPI Backend
                ↓
         Supabase/Postgres
```

## CRM boundary

The CRM is a first-class BiteFixes subsystem. Bitey IA Empresarial can interpret conversations, assist personnel, recommend actions and execute authorized automations, while CRM records and business rules remain governed by this backend.

## Multi-tenancy

```text
BiteFixes
 ├── Tenant A → contextual Bitey IA + CRM
 ├── Tenant B → contextual Bitey IA + CRM
 └── Tenant N → contextual Bitey IA + CRM
```

Tenant isolation is mandatory for customers, conversations, memory, knowledge, tickets, services, employees and operational data.

## Architecture principles

- FastAPI is the authoritative BiteFixes business/API layer.
- Supabase/Postgres is the canonical data, memory and knowledge persistence layer.
- BiteFixes owns CRM, SaaS and AI-agent implementation.
- Bitey IA Empresarial is contextual to each tenant.
- Bitey IA Web is general/integral and remains a separate product/repository boundary.
- `bitey-ai` is the WordPress plugin/integration layer.
- Provider credentials remain server-side.
- Cross-tenant access is prohibited.
- Bitey SBT remains isolated.
- No Gemini API is required.

## Infrastructure and cost policy

This project follows a **free-first, no-surprise-cost architecture**.

- Prefer free services, open-source software, or free tiers with no automatic billing risk.
- Do not introduce a service that requires a payment card merely to start or that can create unexpected entry/egress, API, traffic, storage, or execution charges.
- **Railway is explicitly excluded** from BiteFixes/Bitey infrastructure.
- Cloudflare is permitted when its free usage is sufficient and any later cost occurs only after a clearly defined usage threshold; no paid plan or automatic billing may be enabled without explicit approval.
- Before adding any provider, verify its pricing, billing behavior, limits, card requirements, and overage behavior.
- If a service can generate costs without an explicit user decision first, choose a safer alternative.
- This policy is documentation-only and does not change existing runtime configuration or working integrations.

## Related repositories

- `bitefixes-web` — public BiteFixes website and Web customer channel.
- `bitey-ai` — WordPress plugin for the Bitey Web widget.
- `bitey-web` — general/integral Bitey IA cognitive architecture.
- `bitefixes-app` — BiteFixes mobile channel.
- `bitey-system-bots-trading` — separate trading product.

**Invariant:** BiteFixes owns the enterprise product. Bitey IA Empresarial is its contextual AI implementation. Bitey IA Web remains the general/integral AI. CRM and SaaS never migrate into the general Bitey IA repository.
