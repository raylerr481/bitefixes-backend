# Bitey IA / Bitey Trainer enterprise contract

BiteFixes and Bitey IA are independent projects with independent codebases.

Bitey Trainer belongs to the general Bitey IA project. BiteFixes may consume its capabilities only through an explicit authorized contract.

## Commercial capabilities exposed by BiteFixes

### 1. Bitey IA contextual

BiteFixes may deploy a Bitey IA experience for a customer using that customer's authorized business context, knowledge, services, workflows and approved channels such as website and WhatsApp.

The customer's tenant is isolated from BiteFixes and from every other customer.

### 2. Bitey IA Trainer

BiteFixes may sell Trainer as a professional service for evaluating and improving a customer's AI system.

Typical operations:

- diagnose quality problems;
- compare responses;
- identify failure patterns;
- organize authorized knowledge;
- prepare evaluation datasets;
- propose prompt/routing improvements;
- run regression evaluations;
- produce an improvement report.

## Boundary

BiteFixes does not copy Bitey Trainer source code into this repository.

BiteFixes does not expose its private company/customer data to the general Bitey IA product unless the customer and contract explicitly authorize the transfer.

Provider credentials remain server-side. No browser or mobile client receives provider secrets.

## Human approval

The integration must route the following to a real person rather than automate them:

- identity verification;
- voice/photo/video capture when a platform requires a human;
- legal acceptance/signatures;
- payment authorization;
- any task whose target platform explicitly prohibits automated agents.

## Suggested request contract

```json
{
  "operation": "evaluate|plan|opportunity",
  "tenant_id": "server-side tenant identifier",
  "objective": "customer objective",
  "input": {},
  "metadata": {
    "channel": "bitefixes",
    "human_approval": false
  }
}
```

The actual production endpoint, authentication and payload version must be negotiated between the deployed Bitey IA service and BiteFixes Backend. Do not hard-code provider credentials or private customer data into frontend applications.
