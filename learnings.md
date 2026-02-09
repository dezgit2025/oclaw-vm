# Azure Networking Troubleshooting Learnings

## Date: 2026-02-05

---

## Issue: SSH Connection to Linux VM Timing Out Despite NIC-Level NSG Rules

### Symptoms
- `ssh oclaw` command resulted in "Operation timed out"
- NSG rule on NIC (oclaw2026linux-nsg) showed SSH (port 22) was allowed
- VM was running and SSH service was active

### Root Cause
**Azure has TWO levels of NSG filtering:**

1. **NIC-level NSG** (attached to network interface) - `oclaw2026linux-nsg`
2. **Subnet-level NSG** (attached to subnet) - `vnet-eastus2-snet-eastus2-1-nsg-eastus2`

Traffic must pass BOTH NSGs. If either blocks, connection fails.

```
Internet → Subnet NSG → NIC NSG → VM
              ↓            ↓
           BLOCKED      ALLOWED
              ↓
        CONNECTION FAILS
```

### What Happened
- NIC-level NSG had rule `AllowSSHFromMyIP` (priority 105) allowing SSH from my IP
- Subnet-level NSG had NO custom rules, only defaults:
  - `AllowVnetInBound` (priority 65000) - allows VNet traffic
  - `DenyAllInBound` (priority 65500) - denies everything else from Internet
- **Result:** SSH from Internet blocked at subnet level before reaching NIC

### Policy Behavior
Azure policies or automated security tools may:
- Remove "risky" rules from **BOTH** subnet-level AND NIC-level NSGs
- Rules can be removed within minutes of being added
- Create false sense of security when checking only one NSG level

**IMPORTANT:** Policy removes rules from BOTH levels, not just subnet!

### Observed Behavior (2026-02-05)
1. Added SSH rules to both NSGs → SSH worked
2. ~10 minutes later → SSH failed
3. Checked subnet NSG → rule removed by policy
4. Re-added subnet rule, checked NIC NSG → rule ALSO removed
5. Had to re-add rules to BOTH NSGs again

---

## Solution

### Step 1: Identify Both NSGs

```bash
# Check NIC-level NSG
az network nic show --ids <NIC_ID> --query "networkSecurityGroup.id" -o tsv

# Check Subnet-level NSG
az network vnet subnet show --vnet-name <VNET> --name <SUBNET> --resource-group <RG> --query "networkSecurityGroup.id" -o tsv
```

### Step 2: Add Rules to BOTH NSGs

```bash
# Add to NIC-level NSG
az network nsg rule create \
  --name AllowSSHFromMyIP \
  --nsg-name oclaw2026linux-nsg \
  --resource-group rg_oclaw2026 \
  --priority 105 \
  --direction Inbound \
  --access Allow \
  --protocol Tcp \
  --source-address-prefixes <YOUR_IP> \
  --destination-port-ranges 22

# Add to Subnet-level NSG (CRITICAL - often missed!)
az network nsg rule create \
  --name AllowSSHFromMyIP \
  --nsg-name vnet-eastus2-snet-eastus2-1-nsg-eastus2 \
  --resource-group rg_oclaw2026 \
  --priority 100 \
  --direction Inbound \
  --access Allow \
  --protocol Tcp \
  --source-address-prefixes <YOUR_IP> \
  --destination-port-ranges 22
```

---

## Key Learnings

### 1. Always Check Both NSG Levels
When troubleshooting connectivity:
```bash
# Quick check for both NSGs
az network nic show --name <NIC_NAME> -g <RG> --query "networkSecurityGroup.id"
az network vnet subnet show --vnet-name <VNET> --name <SUBNET> -g <RG> --query "networkSecurityGroup.id"
```

### 2. NSG Rule Evaluation Order
- Rules evaluated by **priority** (lower number = higher priority)
- **First match wins** (Allow or Deny)
- Default rules have priority 65000+ (evaluated last)
- Traffic must be allowed by BOTH subnet and NIC NSGs

### 3. Common Pitfall
Adding rules only to NIC-level NSG and forgetting subnet-level NSG. This is especially problematic when:
- Azure Policy auto-remediates subnet NSG rules
- Security tools clean up "overly permissive" subnet rules
- Different teams manage NIC vs subnet NSGs

### 4. Debugging Commands

```bash
# List all rules on an NSG (including defaults)
az network nsg show --name <NSG_NAME> -g <RG> --query "securityRules[]" -o table
az network nsg show --name <NSG_NAME> -g <RG> --query "defaultSecurityRules[]" -o table

# Check effective security rules for a NIC (shows combined result)
az network nic list-effective-nsg --name <NIC_NAME> -g <RG>

# Verify your current public IP
curl -s ifconfig.me
```

### 5. Quick Connectivity Test
```bash
# Test SSH with timeout
ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no user@host "echo 'Success'"
```

---

## Current Configuration (oclaw2026linux)

| Component | Name | SSH Rule |
|-----------|------|----------|
| VM | oclaw2026linux | - |
| Private IP | 172.20.0.4 | - |
| Public IP | 20.81.190.88 | - |
| NIC NSG | oclaw2026linux-nsg | AllowSSHFromMyIP (priority 105) |
| Subnet NSG | vnet-eastus2-snet-eastus2-1-nsg-eastus2 | AllowSSHFromMyIP (priority 100) |
| SSH Config | `ssh oclaw` | ~/.ssh/oclaw-key-v4.pem |

---

## Quick Fix Script

When SSH stops working, run this to re-enable (updates your IP automatically):

```bash
# Get current IP and add rules to BOTH NSGs
MY_IP=$(curl -s ifconfig.me)
echo "Adding SSH rules for IP: $MY_IP"

# Add to NIC-level NSG
az network nsg rule create --name AllowSSHFromMyIP \
  --nsg-name oclaw2026linux-nsg --resource-group rg_oclaw2026 \
  --priority 105 --direction Inbound --access Allow --protocol Tcp \
  --source-address-prefixes $MY_IP --destination-port-ranges 22 \
  -o none 2>/dev/null || az network nsg rule update --name AllowSSHFromMyIP \
  --nsg-name oclaw2026linux-nsg --resource-group rg_oclaw2026 \
  --source-address-prefixes $MY_IP -o none

# Add to Subnet-level NSG
az network nsg rule create --name AllowSSHFromMyIP \
  --nsg-name vnet-eastus2-snet-eastus2-1-nsg-eastus2 --resource-group rg_oclaw2026 \
  --priority 100 --direction Inbound --access Allow --protocol Tcp \
  --source-address-prefixes $MY_IP --destination-port-ranges 22 \
  -o none 2>/dev/null || az network nsg rule update --name AllowSSHFromMyIP \
  --nsg-name vnet-eastus2-snet-eastus2-1-nsg-eastus2 --resource-group rg_oclaw2026 \
  --source-address-prefixes $MY_IP -o none

echo "Done. Testing SSH..."
ssh -o ConnectTimeout=10 oclaw "echo 'SSH working!'"
```

---

## References

- [Azure NSG Overview](https://learn.microsoft.com/en-us/azure/virtual-network/network-security-groups-overview)
- [NSG Rule Evaluation](https://learn.microsoft.com/en-us/azure/virtual-network/network-security-group-how-it-works)
- [Diagnose VM Network Traffic Filter Problem](https://learn.microsoft.com/en-us/azure/virtual-network/diagnose-network-traffic-filter-problem)
