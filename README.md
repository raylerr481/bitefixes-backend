# BiteFixes Backend

`bitefixes-backend` is the **specialized enterprise AI and business backend owned by BiteFixes**. It is the production foundation for BiteFixes CRM, BiteFixes SaaS, AI-agent implementation/creation and **Bitey IA Empresarial**, the contextual AI implementation used by each business.

## Ecosystem architecture

The Bitey ecosystem has a clear separation of cognitive and enterprise responsibilities:

- **`raylerr481/bitey-web` — Bitey IA Web:** the **central cognitive brain** of Bitey IA. It provides the general/integral intelligence layer and coordinates general reasoning, memory access, planning, tools, models, evaluation, policies and specialized capabilities.
- **`raylerr481/bitefixes-backend` — Bitey IA Empresarial:** the **specialized BiteFixes enterprise AI/business backend**. It owns the BiteFixes business/API domain, CRM/SaaS integration and contextual enterprise operations.
- **`bitefixes-backed` — Supabase/Postgres:** the **single shared canonical memory/data persistence instance** for this architecture.

```text
                    BITEY IA ECOSYSTEM
                             │
              ┌──────────────┴──────────────┐
              │                             │
     Bitey IA Web / GitHub          BiteFixes Backend / GitHub
     CENTRAL COGNITIVE BRAIN        SPECIALIZED ENTERPRISE AI
              │                             │
              └──────────────┬──────────────┘
                             │
                    shared contracts
                             │
                             ▼
                 Supabase/Postgres
                   `bitefixes-backed`
                SINGLE MEMORY/DATA LAYER
```

The separation is by **software responsibility and API contract**, not by creating duplicate memory databases.

## Ownership and boundaries

**BiteFixes owns:**
- BiteFixes CRM and its customer/conversation/lead/opportunity/sale/service/ticket lifecycle.
- AI-agent creation, configuration and implementation.
- BiteFixes SaaS and multi-tenant enterprise services.
- Customer channels and business automations.
- Bitey IA Empresarial implementations.

**Bitey IA Empresarial** is the contextual enterprise implementation of Bitey IA inside BiteFixes. Each business can have its own company context, memory, knowledge, rules, authorized data, tools, channels and assistant identity. It may use authorized CRM capabilities, but it does not own or absorb the general Bitey IA cognitive layer.

**Bitey IA Web** (`raylerr481/bitey-web`) is the separate **central/general Bitey IA brain**. It can coordinate models, research, tools and specialized modules through explicit contracts. It does not replace BiteFixes CRM, SaaS or enterprise business ownership.

**Bitey IA WordPress plugin** (`raylerr481/bitey-ai`) is the WordPress integration/channel layer that provides the Web widget/globe. It is not the Bitey IA Web brain.

**Bitey SBT** is a separate trading project and must not be mixed with BiteFixes CRM, SaaS or enterprise customer data.

## Shared data and memory architecture

**`bitefixes-backed` is the single canonical Supabase/Postgres instance for Bitey IA Web and BiteFixes Backend.**

It is the shared persistence foundation for canonical memory and data. Repositories remain separated at the application and API layers, while tenant/domain isolation is enforced in the data layer.

```text
Bitey IA Web ───────────────┐
                            │
                            ▼
                  `bitefixes-backed`
                  Supabase/Postgres
                            ▲
                            │
BiteFixes Backend ──────────┘
```

A new Bitey/BiteFixes module must not create a parallel Supabase memory instance merely to duplicate ecosystem state.

Neo4j and MongoDB are excluded from the current architecture.

## CRM boundary

The CRM is a first-class BiteFixes subsystem. Bitey IA Empresarial can interpret conversations, assist personnel, recommend actions and execute authorized automations, while CRM records and business rules remain governed by this backend.

The central Bitey IA brain may coordinate with BiteFixes Backend through explicit contracts, but general cognitive responsibilities and BiteFixes business responsibilities remain distinct.

## Multi-tenancy

```text
BiteFixes
 ├── Tenant A → contextual Bitey IA + CRM
 ├── Tenant B → contextual Bitey IA + CRM
 └── Tenant N → contextual Bitey IA + CRM
```

Tenant isolation is mandatory for customers, conversations, memory, knowledge, tickets, services, employees and operational data.

## Architecture principles

- `bitey-web` is the central/general Bitey IA cognitive brain.
- FastAPI is the authoritative BiteFixes business/API layer.
- BiteFixes Backend provides the specialized enterprise AI implementation.
- **`bitefixes-backed` is the single canonical shared Supabase/Postgres memory/data layer.**
- BiteFixes owns CRM, SaaS and AI-agent implementation.
- Bitey IA Empresarial is contextual to each tenant.
- Bitey IA Web remains a separate general cognitive repository boundary.
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
- `bitey-web` — central/general Bitey IA cognitive brain.
- `bitefixes-app` — BiteFixes mobile channel.
- `bitey-system-bots-trading` — separate trading product.

**Invariant:** Bitey IA Web is the central cognitive brain. BiteFixes Backend is the specialized enterprise AI/business backend. Both use the single shared Supabase memory/data instance `bitefixes-backed`. BiteFixes CRM and SaaS remain governed by the specialized enterprise backend and are not migrated into the general Bitey IA repository.
