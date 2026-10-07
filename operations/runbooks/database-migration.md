# Database Migration Runbook

## Principles
1. **Zero Downtime**: Use expand-and-contract schema migrations. Never drop or rename columns in the same release as application changes.
2. **Backward Compatibility**: New database versions must support both the current and previous application container versions.

## Standard Execution Process
1. **Pre-Migration Snapshot**:
   ```bash
   pg_dump -U spaceloop -d spaceloop_db -Fc -f /backup/pre_mig_$(date +%s).dump
   ```
2. **Apply Migration**:
   ```bash
   python scripts/database/migrate.py
   ```
3. **Verify Health**:
   - Check connection pool utilization.
   - Run verification query: `SELECT count(*) FROM migrations_log;`
