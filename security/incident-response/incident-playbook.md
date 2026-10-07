# Security Incident Response Playbook

## Phase 1: Identification & Triage
1. Alert fired via Prometheus/Grafana or security disclosure received.
2. Determine Severity Level (SEV-1: Critical Data/Fund Breach, SEV-2: Service Disruption, SEV-3: Non-exploitable bug).
3. Designate Incident Commander (IC).

## Phase 2: Containment
1. Revoke compromised API keys, JWT signing keys, or lock credentials.
2. If lock or PIN vulnerability detected: Temporarily switch physical spaces to manual security guard verification.
3. If payment escrow anomaly: Pause automated payouts via feature flag `ENABLE_INSTANT_ESCROW_RELEASE=false`.

## Phase 3: Eradication & Recovery
1. Deploy hotfix through emergency pipeline.
2. Rotate all database credentials and Redis auth tokens.
3. Verify integrity of audit logs.

## Phase 4: Post-Mortem
1. Complete blameless post-mortem within 48 hours.
2. Track action items in Jira/GitHub Issues.
