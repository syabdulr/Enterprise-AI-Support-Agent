# Power Platform Governance — Site Safety Incident Solution

> **Status note:** The Power Automate flow described in the architecture
> below is **pending environment access** — it is designed, not yet built.
> The APIM gateway, Azure Function, Dataverse write path, and Logic App
> escalation workflow it references are implemented in this repository
> (see `DEPLOY.md`). This document records the governance decisions that
> will apply when the flow is deployed.

## Architecture context

```
Power Automate flow (pending)
        │  HTTP call, subscription key
        ▼
APIM (subscription, rate limit 100/min)
        │
        ▼
Azure Function (validation + severity classification)
        │
        ▼
Dataverse (abs_siteincidents)
        │
        ▼  (poll every 5 min)
Logic App escalation (Teams notify + status update)
```

The flow is deliberately a thin client: it submits incidents through the
same governed API surface any other client uses. It holds no Dataverse
credentials and cannot write to Dataverse directly.

## Data loss prevention (DLP) policy

The environment-level DLP policy applies to this solution as follows:

- **Connectors used by the flow:** HTTP (to call APIM), and the Teams
  connector or Adaptive Card for requester confirmation UX — nothing else.
- **Data group placement:** the flow sits in the **Business data only**
  group. The HTTP connector is classified **Business**; connectors that
  reach consumer services (Gmail, consumer OneDrive, Twitter, etc.) are
  **Blocked** or **Non-Business** and cannot coexist with it in the same
  flow under this policy.
- **Blocked combinations:** the policy blocks the HTTP connector from
  combining with any non-approved connector in a single flow. This is the
  control that prevents a future maker from quietly adding, say, a
  consumer file connector on the other side of the incident data path.
- **Custom connector stance:** none used. If one is introduced later, it
  must be added to the DLP policy explicitly — the default posture is
  deny.

Practical effect: incident data can only traverse connectors the admin
has explicitly classified as Business, and the write path is the APIM
endpoint.

## Environment strategy

- **Dedicated environment, not the default one.** The default environment
  is where every maker in the tenant lands by accident; production
  business data does not belong there. The solution targets a dedicated
  environment (e.g. `Prod-SiteSafety`) with its own DLP policy boundary.
- **Separate dev/test environment** (e.g. `Dev-SiteSafety`) mirrors the
  DLP policy but with looser maker access, so flows are built and tested
  against test Dataverse rows before solution import to prod.
- **Maker access:** a small named group (the project team) has Environment
  Maker in dev; in prod, makers are effectively read-only — changes ship
  as managed solution imports, not in-place edits. The System
  Administrator role stays with the admin team.
- **Solution packaging:** the flow ships inside a managed solution with a
  environment-variable reference for the APIM base URL and subscription
  key secret reference, so the same artifact moves dev → prod with only
  configuration changing.

## Why the flow routes through APIM instead of Dataverse directly

The flow *could* use the native Dataverse connector with a service
account and bypass everything this repository enforces. It does not,
because:

1. **Guardrails are not optional.** The Azure Function validates the
   payload (required fields, severity enum) and runs triage
   classification before persisting. A direct Dataverse write skips
   validation and classification entirely — bad rows enter the system
   and the escalation Logic App acts on garbage.
2. **Rate limiting applies to everyone.** APIM enforces 100 calls/min per
   subscription key. A flow looping over a malformed spreadsheet would be
   throttled at the gateway rather than hammering Dataverse and the
   organization's API limits unbounded.
3. **One write path, one audit trail.** Every incident — whether it
   arrives from the flow, a future mobile app, or a partner system —
   enters through the same function, gets the same classification, and
   lands in the same audit log. Per-integration Dataverse credentials
   would fragment both security review and incident forensics.
4. **Credential blast radius.** The flow holds an APIM subscription key
   that can be rotated independently. Direct Dataverse access would
   require granting the flow's identity write privileges on the incident
   table — a far broader permission than "may call one endpoint."

## Governance summary

| Control | Applied where |
|---|---|
| DLP policy (Business-only, HTTP blocked from mixing) | Environment |
| Subscription key + 100/min rate limit | APIM |
| Payload validation + classification | Azure Function |
| Severity floors / escalation review | Logic App + Autogen review loop |
| Managed solution import, env variables | ALM across environments |
