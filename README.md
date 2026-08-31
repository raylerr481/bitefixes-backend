# BiteFixes Backend

`bitefixes-backend` is the **specialized enterprise backend and intelligence system for BiteFixes.com** and the production pilot for the configurable Bitey IA CRM SaaS.

The existing FastAPI + Supabase + Render architecture is preserved and extended incrementally. This repository is not replaced by a new backend.

## BiteFixes pilot model

BiteFixes.com remains a public business website. **Authentication is required only for the private Support Portal**, where authorized BiteFixes personnel manage customers, employees, conversations, tickets, services and sales.

Customers do not authenticate to the administrative Support Portal. They reach the business through three customer channels:

- WhatsApp
- Telegram
- Configurable web Bitey widget/globe

```text
Public BiteFixes.com
       │
       ├── services / sales / contact
       └── Support Portal (private)
                 │
                 └── authenticated staff
                       ├── owner
                       ├── admin
                       ├── technician
                       └── worker

Customer channels
   ├── WhatsApp ─┐
   ├── Telegram ─┼──> Bitey Conversation Engine
   └── Web widget┘            │
                              ▼
                         CRM + IA + Memory
                              │
                           Supabase
                              │
                           Render
```

## SaaS evolution

BiteFixes is the first production tenant. The same engine is being generalized for other companies without replacing the proven BiteFixes workflow.

Each tenant can define its own company identity, assistant name, logo, language/currency, services, knowledge, employees, roles and enabled customer channels. The internal intelligence engine remains Bitey while the customer-facing assistant and Portal can be white-label.

## Enterprise onboarding flow

A future customer does not need to understand the internal schema. Bitey guides the business through an assessment using the same Web, WhatsApp or Telegram conversation channels. The company can also upload a business document as an input artifact.

```text
Company request
      ↓
Guided assessment
      ↓
Business evidence / documents
      ↓
Profile + missing information
      ↓
AI analysis and recommendations
      ↓
Solution plan
      ↓
Configuration preview
      ↓
Customer approval
      ↓
Versioned tenant configuration
      ↓
Install / activate channels and Portal
```

The backend never invents missing business facts. The assessment identifies what is missing and generates the next questions. Business rules, permissions and secrets remain controlled by the backend.

### Enterprise configuration endpoints

- `POST /company-profile/import` — securely ingest an approved PDF, DOCX, TXT, CSV, JSON or Markdown company document.
- `POST /company-profile/assessment` — evaluate the supplied enterprise profile and return missing sections, next questions and implementation recommendations.
- `POST /company-profile/configuration-preview` — compile a non-secret tenant manifest only when the assessment is complete.

The manifest is a **configuration artifact**, not a replacement for Bitey Core. It can later be versioned, reviewed, installed and rolled back.

## Data boundary

The backend treats the authenticated employee context as authoritative for private Portal access. Customer records and operational data are scoped to the employee's company/tenant.

```text
Tenant A → customers, conversations, tickets, services, sales
Tenant B → customers, conversations, tickets, services, sales

Tenant A data MUST NOT be visible to Tenant B.
```

## Core CRM flow

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

Bitey should turn channel conversations into authorized CRM actions rather than acting only as a chatbot.

## Architecture

- FastAPI backend remains the authoritative business/API layer.
- Supabase remains the canonical persistence layer.
- Render remains the production runtime.
- Bitey remains the intelligence/conversation engine.
- WhatsApp, Telegram and Web are the primary customer ingress channels.
- The Support Portal is the private operational interface for company personnel.
- Enterprise configuration is additive and backward-compatible with the BiteFixes pilot.

## API configuration metadata

`/info` and `/gateway/status` expose non-secret tenant presentation metadata and the canonical customer channels. Secrets and authoritative business data remain server-side.

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

## Related repositories

- `bitefixes-web` — public BiteFixes website/frontend and Web channel.
- `bitey-ai` — configurable WordPress enterprise/Web widget integration.
- `bitefixes-app` — mobile channel; future customer/employee experiences can use the same authorized APIs.

The goal is to **improve and generalize the existing BiteFixes product into Bitey IA CRM SaaS**, not to replace the working system or remove existing capabilities.
