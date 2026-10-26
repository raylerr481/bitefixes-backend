# Bitey multi-tenant contract

Bitey Cloud is multi-tenant. BiteFixes is one tenant, not the backend's hard-coded identity.

Every business object that can contain customer or knowledge data must be tenant-scoped. At minimum this includes conversations, messages, memory, documents, embeddings/vector records, tickets, customers, services, workflows and incidents.

Assistant branding is tenant configuration. A tenant may choose an assistant name, welcome message, language, personality and visual identity. Branding must never grant additional permissions or alter security policy.

## Request lifecycle

```text
channel -> gateway -> authenticated principal -> tenant context -> policy -> memory/RAG/tools -> AI provider -> response
```

The server derives tenant context from trusted authentication and/or a validated integration credential. A browser-provided tenant identifier is not sufficient authorization.

## Vector isolation

Every vector record must carry tenant metadata and every retrieval must apply the tenant filter before results are returned to the model.

## Provider isolation

Provider credentials are server-side. Tenants select allowed provider policies; they never receive Bitey Cloud provider secrets.

## Failure isolation

An incident in one tenant must not expose data from another tenant and must not automatically modify another tenant's configuration.
