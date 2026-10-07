# SpaceLoop Production Release Checklist

## Pre-Release Verification (T - 2 hours)
- [ ] CI pipeline completely green on `main`.
- [ ] Database migration backwards-compatibility verified (expand-contract pattern).
- [ ] Secrets and environment variables provisioned across all target clusters.
- [ ] Security scan reports zero high/critical vulnerabilities.
- [ ] Payment gateway test transactions executed against staging sandbox.

## Deployment Phase (T = 0)
- [ ] Initiate blue-green canary deployment (10% traffic allocation).
- [ ] Monitor error rates, memory consumption, and lock contention for 15 minutes.
- [ ] Promote traffic to 100% upon healthy metrics.

## Post-Release Verification (T + 30 mins)
- [ ] Execute smoke test suite against live environment.
- [ ] Verify LoopBot AI responses and search vector ranking.
- [ ] Check escrow balance integrity and webhook ingestion.
- [ ] Close release tracking ticket and update CHANGELOG.md.
