# Bitey Multi-Tenant Cognitive Architecture

## Mandatory product rule

Bitey is a **multi-company cognitive AI engine**. BiteFixes is only one tenant/reference implementation. No cognitive capability may be hard-coded to BiteFixes, its brand, its industry, or a specific device/model.

The same cognitive engine must be deployable for any company, with the company's own assistant name, identity, knowledge, services, rules, channels, language, currency, and customer data.

## Separation of concerns

### Cognitive Core

The reusable engine owns:

- conversation continuity
- active goal/problem state
- pending questions
- evidence extraction
- entity updates
- contradiction detection
- memory/state transitions
- new-problem detection
- ambiguity handling
- web/YouTube research orchestration
- next-action selection

The core must operate on generic concepts such as `company_context`, `active_goal`, `active_problem`, `entity`, `evidence`, and `pending_question`.

### Company Context

Each tenant supplies configuration such as:

```json
{
  "company_id": "tenant-id",
  "company_name": "Example Company",
  "assistant_name": "Example AI",
  "industry": "industry-name",
  "language": "pt-BR",
  "currency": "BRL",
  "services": [],
  "business_rules": {},
  "knowledge_sources": []
}
```

`assistant_name` is configuration, not a hard-coded constant. `Bitey` is the default/reference assistant name for BiteFixes, not a requirement of the engine.

## Tenant isolation

All customer, conversation, ticket, cognitive-state, evidence, memory, knowledge, and research data must be scoped by `company_id` (or an equivalent tenant identifier). Cross-tenant context must never enter a conversation unless explicitly authorized by a future cross-tenant administration feature.

Supabase policies/schema must preserve this isolation.

## Cognitive invariants

1. New evidence is interpreted against the active state.
2. A pending question has priority when the new message plausibly answers it.
3. Entity/model/version data must not replace an active problem.
4. A tutorial/web request is an auxiliary intent unless it clearly changes the goal/problem.
5. A new problem requires evidence of a distinct problem; device names/models alone are not problems.
6. Ambiguous isolated messages must not cause invented context.
7. Active goals persist through compatible follow-up information.
8. Company-specific vocabulary belongs in tenant configuration/knowledge, not in universal cognitive rules.
9. Tests must use multiple industries and entities to prevent device/company-specific hacks.

## Example

BiteFixes:

`screen broken -> model question -> Redmi 9A -> DIY video`

must produce:

`problem=screen_damage, entity.model=Redmi 9A, auxiliary_request=repair_tutorial`

A different tenant must use the same state transitions without importing BiteFixes knowledge.

## Commercialization target

The product should be treated as a reusable **Bitey Cognitive AI Platform**, where each company receives a branded/configured assistant while sharing the validated cognitive core. Tenant-specific behavior is configuration, knowledge, integrations, and authorized business rules—not forks of the cognitive engine.

## Testing requirement

Continuity tests must include at least two different industries/tenants and must verify tenant isolation, active-goal persistence, pending-question resolution, entity updates, new-problem detection, ambiguity, and auxiliary web/YouTube research requests.
