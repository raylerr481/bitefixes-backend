# Bitey Cognitive Layer

Bitey now has two optional cognitive components:

- **OpenCog Hyperon / MeTTa**: local symbolic reasoning and knowledge experimentation.
- **Letta**: persistent stateful-agent memory and continual context management.

The existing architecture remains authoritative:

- Supabase = business source of truth.
- Groq = primary external LLM.
- Bitey decision/workflow engine = authority for tickets, quotes and actions.
- Hyperon/Letta = cognitive support, not business-authority replacement.

## Render environment

Add these variables:

```text
BITEY_HYPERON_ENABLED=true
BITEY_LETTA_ENABLED=true
LETTA_API_KEY=<secret>
LETTA_AGENT_ID=<agent id created in Letta>
```

`LETTA_API_KEY` is optional until a Letta agent is provisioned. Do not commit it to GitHub.

## Letta

Install is provided by `letta-client`. The adapter uses an existing `LETTA_AGENT_ID` so production does not create uncontrolled agents automatically.

Letta's official Python SDK is installed with `pip install letta-client`. See https://docs.letta.com/api/python.

## Hyperon

The Python package is `hyperon`. The adapter is deliberately isolated because Hyperon is an active pre-alpha experimental project and uses native components.

See https://github.com/trueagi-io/hyperon-experimental.

## Cognitive loop

```text
customer message
  -> Bitey context + Supabase knowledge
  -> Groq / external AI reasoning
  -> cognitive observation
  -> Letta persistent memory (when configured)
  -> Hyperon symbolic layer (when available)
  -> Bitey validation
  -> workflow / response
```

A cognitive component failure must never take down `/chat`; the adapters fail closed and Bitey continues with its normal core.
