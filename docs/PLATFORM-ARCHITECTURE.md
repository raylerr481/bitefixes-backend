# Bitey Platform Architecture

## Single brain, multiple channels

Bitey has one authoritative intelligence core: `bitefixes-backend`.

The other Bitey repositories are channels/interfaces and must not create a second independent brain:

- `bitey-ai` — WordPress channel/plugin.
- `bitey-web` — public web facade for a ChatGPT-like Bitey experience.
- `bitefixes-app` — mobile application for accessing BiteFixes and Bitey.
- `bitefixes-backend` — Bitey IA, business context, orchestration, memory, research, knowledge, workflows and evolution.

```text
User
  |
  +--> bitey-web --------+
  +--> bitey-ai ---------+
  +--> bitefixes-app ----+----> bitefixes-backend
                         |             |
                         |             +--> Company AI Profile
                         |             +--> conversation/customer context
                         |             +--> knowledge and memory
                         |             +--> intelligent web research
                         |             +--> intent/service/workflow decisions
                         |             +--> external AI collaboration
                         |             +--> evolution/evaluation
                         |
                         +<---- response
```

## Web research is part of interaction intelligence

Research is not an isolated search button. The backend decides dynamically whether available company/conversation knowledge is sufficient. When it is not, authorized research can gather public evidence, evaluate sources, add the evidence to the current reasoning context, and produce a grounded response.

The interaction loop is:

```text
interaction
 -> understand context
 -> determine information need
 -> use existing knowledge OR research
 -> verify/evaluate evidence
 -> reason
 -> respond
 -> observe/evaluate
 -> controlled improvement
```

Research results do not automatically become permanent company knowledge. Persistence requires the appropriate authorization, provenance, confidence and retention rules.

## External AI providers

External models are replaceable cognitive collaborators. They do not define Bitey's company identity, tenant boundaries, memory or business rules. The backend selects what context may be supplied and remains responsible for orchestration and authorization.

## Channel contract

Channels should transport identity, conversation/session identifiers, messages, language preferences and permitted attachments/metadata. They should not contain the authoritative business profile, provider secrets, cross-tenant memory, or duplicated decision logic.

## BiteFixes as reference tenant

BiteFixes is the first real company context used to build and measure Bitey. Bitey's architecture must therefore work for BiteFixes without hard-coding BiteFixes into the intelligence core. The same core should support future companies with isolated Company AI Profiles and authorized knowledge.

## Source of truth

`bitefixes-backend` is the authoritative repository for the backend intelligence architecture. Channel repositories must integrate with its API contract rather than implement parallel intelligence.
