# Discovery Brief — Site Safety Incident Intake & Escalation

> **Provenance:** This is a **self-run discovery exercise on a portfolio
> project**, not a client engagement. The scenario (site safety incident
> reporting for a construction organization) is hypothetical. It exists
> to demonstrate the discovery-to-delivery thinking a Copilot Studio /
> Power Platform engagement expects: problem framing, measurable
> acceptance criteria, NFRs, and outcome metrics defined **before**
> solution design. The artifacts referenced below are implemented in this
> repository.

## 1. Problem statement

Site safety incidents (hazards, near-misses, injuries) are reported
inconsistently today: paper forms, texts to supervisors, verbal
pass-offs. Consequences:

- **Slow acknowledgment.** A critical hazard reported at 07:40 may not
  reach the responsible supervisor until end of shift.
- **Inconsistent triage.** Severity is judged differently by every
  reporter; "small" electrical issues are sometimes low-rated because the
  reporter doesn't know the classification rules.
- **No single record.** Incidents live in inboxes and notebooks; nothing
  is queryable, trendable, or auditable.
- **Escalation depends on people remembering.** High-severity incidents
  get escalated when someone remembers to escalate them.

The intended user base is ~300 field workers (reporters) and ~15 safety
staff (responders) across multiple sites, mixed mobile literacy.

## 2. Personas

| Persona | Need |
|---|---|
| Field worker (reporter) | Report an incident in under 2 minutes, from a phone, without knowing severity rules |
| Safety officer (responder) | See high/critical incidents fast, with a defensible classification |
| Site supervisor | Get notified of critical hazards at their site immediately |
| IT / platform admin | Governed write path, audit trail, no ungoverned connector sprawl |

## 3. Scope

**In scope:**
- Incident intake (structured form / conversational), severity
  classification at write time, persistent incident records, automated
  escalation for high/critical, notification to site channel.

**Out of scope (v1):**
- Regulatory form generation (e.g. ministry reports)
- Offline capture (dead-zone sites) — capture via SMS fallback later
- Analytics/BI beyond raw record query
- Multilingual intake

## 4. Value hypothesis

If every incident enters through one governed intake that classifies
severity automatically and escalates deterministically, then:

1. Time-to-acknowledgment for critical incidents drops from hours to
   minutes (notification is automatic, not person-dependent).
2. Classification becomes consistent (one classifier, reviewable
   policy) instead of reporter-dependent.
3. Every incident becomes a queryable record from day one — audit and
   trend analysis become possible at zero marginal effort.

We will consider the hypothesis **supported** if the outcome metrics in
§7 move as stated in a 90-day pilot on one site.

## 5. Acceptance criteria

| # | Criterion | Verification |
|---|---|---|
| AC-1 | Worker can submit an incident from a phone in ≤ 2 min | Timed pilot task (n≥10) |
| AC-2 | Every submitted incident is persisted with category + severity | Record present in Dataverse within 5 s of submit |
| AC-3 | Critical incidents trigger supervisor notification without human action | Escalation log entry + notification within 5 min of submit |
| AC-4 | Severity classification is reproducible: same input → same output | Golden-set regression run (eval pipeline) |
| AC-5 | Writes only enter through the governed API | APIM policy + no direct-write identities on the table |
| AC-6 | Reporter PII never appears in notifications or logs | Guardrail redaction test + audit trail review |

## 6. Non-functional requirements

**Latency**
- API write path (submit → persisted): p95 ≤ 2 s
- Escalation (submit → notification dispatched): ≤ 5 min (polling
  cadence bound; acceptable for v1)
- Intake UI interaction: every step ≤ 1 s perceived

**Privacy (reporter data)**
- Reporter identity stored on the incident record only; never included
  in escalation payloads or logs (guardrail-enforced redaction)
- Retention: incident records retained per safety-regulation minimums
  (7 years); reporter contact fields purged after case closure + 90 days
- Data stays within the tenant; no consumer services in the data path
  (DLP policy, see POWER_PLATFORM_GOVERNANCE.md)

**Security**
- All writes via API Management with subscription keys; no client holds
  Dataverse credentials (blast-radius rationale in governance doc)
- Secrets in Key Vault-referenced app settings; never in flow or
  solution artifacts
- Rate limiting (100 calls/min/subscription) to prevent runaway or
  abusive automation
- Audit trail for every write and every guardrail decision

**Availability / supportability**
- Dependency failure (classification service down) must fail closed:
  incident still persisted, flagged "unclassified", queued for review —
  never silently dropped
- All escalation decisions reconstructible from logs after the fact

## 7. Outcome metrics

| Metric | Baseline (paper/text) | Pilot target (90 days) |
|---|---|---|
| Adoption: % of incidents via the governed intake | ~0% | ≥ 60% on pilot site |
| Task success: completed submissions / started | n/a | ≥ 90% |
| Median time-to-acknowledgment, critical incidents | hours (anecdotal) | ≤ 15 min |
| False-escalation rate (high/critical later downgraded) | unknown | ≤ 20%, trending down |
| Missed-escalation rate (high/critical left unescalated >1h) | unknown | 0 |

Metrics are instrumented from system data (submission timestamps,
escalation log, status transitions), not self-report — with the
exception of adoption denominator, which needs site-level incident
counts from the safety team.

## 8. Risks & assumptions

| # | Risk / assumption | Mitigation / validation |
|---|---|---|
| R1 | Workers won't adopt another app | Keep intake to one screen; measure drop-off in pilot |
| R2 | Classifier severity floors wrong for real data | Floors are config, not code; review downgrades weekly in pilot |
| R3 | 5-min polling feels slow for critical | Acceptable v1; v2 moves to event-driven trigger |
| R4 | Pilot site has poor connectivity | SMS fallback deferred; choose connected pilot site |
| A1 | Assumption: safety team can supply monthly incident counts for the adoption denominator | Confirm before pilot start |

## 9. Traceability — brief → implementation

| Brief element | Implemented artifact (this repo) |
|---|---|
| Governed write path (AC-5) | `infra/apim.bicep`, `functions/incident_write/` |
| Classification at write time (AC-2, AC-4) | `src/sk/plugins/incident_plugins.py` triage in the Function |
| Persistent records (AC-2) | `src/dataverse/` (`abs_siteincidents`) |
| Deterministic escalation (AC-3) | `infra/logic-app-escalation.json` |
| PII redaction in payloads (AC-6) | Guardrail detector + redact mode (platform repo) |
| Reproducible classification (AC-4) | Golden-set eval pipeline (platform repo) |
| Governance controls (§6 security) | `docs/POWER_PLATFORM_GOVERNANCE.md` |
| Severity review before escalation | `src/autogen_review/` two-agent loop |

## 10. Decision ask

For the hypothetical sponsor: approve a 90-day single-site pilot with
the outcome metrics in §7 as the success gate, and the v1 scope in §3 as
the build boundary.
