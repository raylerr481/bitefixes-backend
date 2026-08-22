# Bitey Evolution Framework

## Purpose

Bitey IA is expected to improve over time. This document defines a durable measurement model so changes are recorded instead of relying on memory or subjective impressions.

## Non-blocking principle

Evaluation is not a mandatory gate in the live response path. A user receives the response produced by the current authorized intelligence flow. Evaluation runs after or alongside the interaction and records evidence for future improvement.

## Evolution markers

Each marker should be timestamped and tied to the relevant build/version. Recommended marker types:

- `interaction_observed` — representative real interaction captured for measurement.
- `evaluation_completed` — an evaluator assessed a response.
- `context_improved` — new/updated authorized context became available.
- `continuity_improved` — a regression in conversation continuity was fixed.
- `service_alignment_improved` — service/intent grounding was improved.
- `knowledge_updated` — company knowledge or evidence changed.
- `model/provider_changed` — external cognitive infrastructure changed.
- `bitey_capability_changed` — an intrinsic Bitey capability changed.
- `regression_detected` — a previously successful behavior degraded.
- `regression_fixed` — the degradation was corrected and validated.
- `release_validated` — a version passed its required evaluation set.

## Evaluation dimensions

Use consistent dimensions so historical scores remain comparable:

| Dimension | Meaning |
|---|---|
| context_grounding | Uses authorized company/context evidence correctly |
| conversation_continuity | Retains and applies established facts across turns |
| business_alignment | Acts consistently with the company's identity and capabilities |
| service_alignment | Advances the correct service/need |
| factuality | Avoids unsupported or contradictory claims |
| helpfulness | Moves the user toward a useful outcome |
| safety_authorization | Respects permissions, privacy and tenant boundaries |
| language_quality | Clear, natural and appropriate communication |
| external_collaboration | Uses external AI capabilities effectively when present |

## Marker record

A persisted evaluation marker should contain, where applicable:

```text
id
occurred_at
company_id
channel
conversation_id
bitey_version
build_id
marker_type
evaluator_type
evaluator_id
criteria
scores
strengths
weaknesses
missing_context
regression_reference
change_reference
result
```

Do not store secrets or unnecessary private content in the marker. Prefer references to protected source records.

## Periodic review cadence

### Continuous
Record meaningful interaction/evaluation events asynchronously.

### Weekly
Review recent regressions, repeated failures and major context gaps. Compare against the previous week.

### Monthly
Run a stable evaluation set covering core BiteFixes services and representative conversations. Compare the current version against the previous baseline.

### Release
Before promoting a material change, compare the candidate against the current baseline and record the result. A release marker must identify what changed and which measurements justify promotion.

## Baseline indicators

Maintain a time series for:

- average context grounding;
- conversation continuity;
- business/service alignment;
- factuality;
- helpfulness;
- safety/authorization;
- percentage of repeated-question regressions;
- unresolved evaluation failures;
- successful evaluation rate;
- evaluation coverage;
- change-to-improvement correlation.

A single aggregate score must never replace the dimension-level record.

## Evolution comparison

Every periodic review should answer:

1. What changed since the previous marker?
2. Which behavior improved?
3. Which behavior regressed?
4. What evidence explains the change?
5. Was the change caused by context, code, prompt/orchestration, external provider, channel behavior or data?
6. Does the new version outperform the previous baseline on the stable evaluation set?

## Long-term goal

The record is intended to show the transition from an externally powered assistant toward an increasingly capable **Bitey IA** that can collaborate with external IAs while developing and retaining its own reusable business reasoning capabilities.
