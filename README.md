# BiteFixes Backend

FastAPI backend and **enterprise AI brain for BiteFixes.com**. This project remains dedicated to BiteFixes and its authorized channels. It is independent from the general Bitey IA supracerebro.

## Architectural boundary

```text
BiteFixes.com
  ├─ website / AI globe
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
          ├─ intent / service / workflows
          ├─ tickets + customers
          ├─ external AI collaboration
          └─ tenant / permission controls
```

This repository is **not** the general Bitey IA web supracerebro. `bitey-web` is the separate Bitey IA project that provides the general web-based AI experience. The two projects must remain separate and must not be merged merely because they share architectural ideas.

## Bitey IA relationship

The enterprise architecture developed in BiteFixes is an important reference for the broader Bitey IA model, but BiteFixes-specific business logic stays here.

```text
Bitey IA
  = general supracerebro / web AI

BiteFixes Backend
  = specialized enterprise brain for BiteFixes.com
```

External AI models are collaborators. They do not become the identity or authority of BiteFixes. This backend controls authorized company context, business rules, provider selection, tenant isolation and operational workflows.

## Enterprise context

BiteFixes may use authorized context from the company website, onboarding information, approved documents, supported channels, conversation history, customer information, services/capabilities and operational knowledge. Context acquisition must respect authorization, privacy, retention and tenant isolation.

## Intelligent web research

Research is part of the BiteFixes interaction engine. When existing authorized knowledge is insufficient, the system can investigate public information, evaluate evidence and use relevant results in the current response. Research evidence does not automatically become permanent company knowledge.

## Core responsibilities

- FastAPI API and BiteFixes enterprise runtime.
- Supabase persistence.
- Company AI Profile and business context.
- Customer and conversation memory.
- Knowledge and retrieval.
- Intelligent web research.
- Intent detection and service resolution.
- Tickets, customers and operational workflows.
- External AI provider collaboration.
- Channel contracts for the website widget, WhatsApp, Telegram and other authorized channels.
- Security, tenant isolation and provider credential protection.
- Tests, observability and production deployment.

## Product ecosystem

- `bitey-web` — **Bitey IA**, general web-based supracerebro and ChatGPT/Claude-like AI experience.
- `bitey-ai` — **Bitey Plugin Web**, WordPress plugin/channel.
- `bitefixes-backend` — **BiteFixes Backend**, this specialized enterprise brain.
- `bitefixes-app` — **BiteFixes App**, mobile extension of BiteFixes.com.

## Important

This architectural clarification does not require changing the existing BiteFixes runtime. The purpose is to preserve the working backend while keeping the new Bitey IA supracerebro as a separate project.
