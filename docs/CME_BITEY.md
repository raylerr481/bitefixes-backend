# CME Bitey — Cognitive Multi-tenant Engine

## Identity

CME Bitey is Bitey's own multi-tenant cognitive context layer. It is an internal product architecture and is not affiliated with CME Group.

**Core rule:** Bitey is not an AI hard-coded for BiteFixes. BiteFixes is one tenant/reference implementation. The same cognitive engine must operate for any company, industry, language, brand, and assistant name.

## Tenant configuration

Each request receives a `CompanyContext` containing:

- `company_id`
- `company_name`
- `assistant_name`
- `industry`
- `language`
- `currency`
- `services`
- `business_rules`
- `knowledge_namespace`

The cognitive engine must not embed company-specific branches for Redmi, CCTV, BiteFixes, or any other customer example.

## Isolation

Customer, conversation, cognitive state, evidence, and knowledge retrieval must remain tenant-scoped by `company_id`/`knowledge_namespace`.

A company can customize identity without forking the cognitive engine:

```text
BiteFixes  -> Bitey
DentalPlus -> Denti
FactoryCo  -> FactoryAI
```

## Research policy

When a user asks for a tutorial, guide, video, walkthrough, or DIY instructions, the research capability must use the active cognitive context and search broadly. YouTube is one source, not a restriction. The engine should consider open web, specialist sources, official documentation/manuals, and YouTube, then rank results by contextual relevance and source-quality hints.

The research capability must work across industries and tenants. `company_name` and `industry` may shape context, but the core must not contain hard-coded company-specific search rules.

## Product boundary

CME Bitey provides context/identity/tenant isolation. The shared Bitey Cognitive Engine provides reasoning/state/evidence/continuity. Business configuration supplies the company-specific knowledge and presentation.
