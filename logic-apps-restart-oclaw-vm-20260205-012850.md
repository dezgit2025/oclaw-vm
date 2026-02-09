# VM Watchdog Logic App Documentation

**Created:** 2026-02-05
**Author:** Claude Code
**Logic App Name:** `vm-watchdog-oclaw`
**Resource Group:** `RG_OCLAW2026`
**Location:** eastus2

---

## Problem Statement

The Azure VM `oclaw2026linux` was unexpectedly shutting down/deallocating. SSH connections were failing with connection timeouts.

### Investigation Findings

1. **VM Status:** VM was deallocated (not running)
2. **NSG Issue:** Network Security Group had no SSH rule - fixed by adding AllowSSH rule on port 22
3. **Auto-shutdown Policy:** Checked for DevTestLab auto-shutdown schedule - **none found**
4. **Activity Log Analysis:** Found deallocation events triggered by a service principal:
   - **Caller:** `7355f99c-0211-455d-aa02-4a559687ae60`
   - **Time:** 2026-02-05T05:52:43 UTC
   - **Operation:** `Microsoft.Compute/virtualMachines/deallocate/action`

The shutdown was triggered by an automated service principal (likely Azure Budget action, Policy, or Automation), not manual user action or auto-shutdown policy.

---

## Solution Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **Start/Stop VMs v2** | Deploy full Azure solution | Feature-rich, Microsoft supported | Heavier, more complex |
| **Custom Logic App** | Simple watchdog to restart VM | Lightweight, cheap, quick to deploy | Manual setup |
| **Azure Automation Runbook** | PowerShell script on schedule | Flexible | More overhead |
| **Find root cause** | Identify and disable the shutdown trigger | Permanent fix | Requires more investigation |

**Decision:** Implemented Option 2 (Custom Logic App) as immediate solution while root cause investigation continues.

---

## Solution Implemented

### Logic App Configuration

| Setting | Value |
|---------|-------|
| **Name** | `vm-watchdog-oclaw` |
| **Type** | Consumption (pay-per-execution) |
| **Trigger** | Recurrence - every 30 minutes |
| **Identity** | System-assigned Managed Identity |
| **Role Assignment** | Virtual Machine Contributor on target VM |

### Workflow Logic

```
1. TRIGGER: Recurrence (every 30 minutes)
      ↓
2. ACTION: HTTP GET - Get VM Instance View
   URL: https://management.azure.com/.../virtualMachines/oclaw2026linux/instanceView
   Auth: Managed Service Identity
      ↓
3. CONDITION: Check if PowerState/running NOT in response
      ↓
   IF TRUE → ACTION: HTTP POST - Start VM
             URL: https://management.azure.com/.../virtualMachines/oclaw2026linux/start
             Auth: Managed Service Identity
      ↓
   IF FALSE → Do nothing (VM already running)
```

### Resources Created

| Resource | Resource ID |
|----------|-------------|
| Logic App | `/subscriptions/c34d54e5-7eb9-4ba8-8424-c6ab8635ccdc/resourceGroups/RG_OCLAW2026/providers/Microsoft.Logic/workflows/vm-watchdog-oclaw` |
| Role Assignment | Virtual Machine Contributor scoped to `oclaw2026linux` |

---

## Cost Estimate

| Component | Calculation | Monthly Cost |
|-----------|-------------|--------------|
| Trigger executions | 2 per hour × 24 × 30 = 1,440 | ~$0.04 |
| HTTP actions | ~2,880-4,320 actions | ~$0.10-0.20 |
| **Total** | | **~$0.25-0.50/month** |

Note: First 4,000 built-in actions per subscription are free.

---

## Management Commands

```bash
# View Logic App details
az logic workflow show -n vm-watchdog-oclaw -g RG_OCLAW2026 -o table

# Check run history
az rest --method GET \
  --uri "https://management.azure.com/subscriptions/c34d54e5-7eb9-4ba8-8424-c6ab8635ccdc/resourceGroups/RG_OCLAW2026/providers/Microsoft.Logic/workflows/vm-watchdog-oclaw/runs?api-version=2016-06-01&\$top=5" \
  --query "value[].{Name:name, Status:properties.status, StartTime:properties.startTime}" -o table

# Manually trigger a run
az rest --method POST \
  --uri "https://management.azure.com/subscriptions/c34d54e5-7eb9-4ba8-8424-c6ab8635ccdc/resourceGroups/RG_OCLAW2026/providers/Microsoft.Logic/workflows/vm-watchdog-oclaw/triggers/Recurrence/run?api-version=2016-06-01"

# Disable Logic App (pause monitoring)
az logic workflow update -n vm-watchdog-oclaw -g RG_OCLAW2026 --state Disabled

# Enable Logic App (resume monitoring)
az logic workflow update -n vm-watchdog-oclaw -g RG_OCLAW2026 --state Enabled

# Delete Logic App (remove completely)
az logic workflow delete -n vm-watchdog-oclaw -g RG_OCLAW2026 --yes
```

---

## SSH Configuration

SSH key and config were also set up during this session:

| Item | Location |
|------|----------|
| Private Key | `~/.ssh/oclaw-key-v4.pem` |
| SSH Config Host | `oclaw` |

```bash
# Connect to VM
ssh oclaw
```

SSH Config entry (`~/.ssh/config`):
```
Host oclaw
  HostName 20.81.190.88
  User desazure
  IdentityFile ~/.ssh/oclaw-key-v4.pem
```

---

## Outstanding Items / Future Work

1. **Identify root cause:** Determine what service principal `7355f99c-0211-455d-aa02-4a559687ae60` belongs to and why it's shutting down the VM
   - Check Azure Budgets
   - Check Azure Policy assignments
   - Check for existing Automation Runbooks

2. **Consider permanent fix:** Once root cause is identified, either:
   - Disable the shutdown trigger
   - Exclude `oclaw2026linux` from its scope
   - Adjust budget/policy thresholds

3. **Monitoring:** Consider adding Application Insights or alert on Logic App failures

---

## References

- [Start/Stop VMs v2 Overview](https://learn.microsoft.com/en-us/azure/azure-functions/start-stop-v2/overview)
- [Logic Apps Pricing](https://azure.microsoft.com/pricing/details/logic-apps/)
- [Managed Identities for Azure Resources](https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview)
