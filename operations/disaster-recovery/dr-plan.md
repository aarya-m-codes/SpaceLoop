# Disaster Recovery (DR) Plan

## Target Objectives
- **RPO (Recovery Point Objective)**: <= 15 minutes of transactional data.
- **RTO (Recovery Time Objective)**: <= 60 minutes to full service restoration.

## Disaster Scenarios
1. **Primary Database Region Outage**:
   - Promote read-replica in secondary region to primary master.
   - Update DNS CNAME / connection string in Kubernetes secrets.
   - Restart backend pods.
2. **Total Cluster Failure**:
   - Apply Terraform/Helm infrastructure manifests to backup cloud region.
   - Restore database from latest WAL archive.
   - Switch Global Traffic Manager (Cloudflare) to secondary origin.
