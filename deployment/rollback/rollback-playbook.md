# Production Rollback Playbook

## Triggers for Rollback
1. Error rate exceeding 1% within 5 minutes of release.
2. Latency (p99) exceeding 1500ms on core APIs (`/bookings`, `/spaces`, `/auth`).
3. Failure in smart door lock PIN generation or payment escrow settlement.

## Execution Steps
1. **Kubernetes Rollback**:
   ```bash
   kubectl rollout undo deployment/spaceloop-backend-production -n production
   kubectl rollout status deployment/spaceloop-backend-production -n production
   ```
2. **Database Reversion**:
   - If a migration was executed, run the down-migration script:
   ```bash
   python scripts/database/rollback_migration.py --target-version PREV
   ```
3. **Cache Purge**:
   - Flush invalidated session caches:
   ```bash
   redis-cli -u $REDIS_URL FLUSHDB
   ```
4. **Incident Notification**:
   - Notify on-call team and update platform status page.
