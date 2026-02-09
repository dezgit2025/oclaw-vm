# OpenClaw Management Architecture Documentation

**Last Updated**: 2026-02-05
**Resource Group**: RG_OCLAW2026
**Region**: East US 2

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Network Topology Diagram](#network-topology-diagram)
4. [Azure Bastion](#azure-bastion)
5. [Security Model](#security-model)
6. [Virtual Machine Details](#virtual-machine-details)
7. [Connection Instructions](#connection-instructions)
8. [OpenClaw Access](#openclaw-access)
9. [Credentials and Secrets](#credentials-and-secrets)
10. [Cost Information](#cost-information)
11. [Troubleshooting](#troubleshooting)

---

## Overview

This architecture implements a secure, zone-redundant environment for running OpenClaw in Azure, using a dedicated Windows 11 management VM for secure administrative access. The design eliminates direct public exposure of the OpenClaw web interface while maintaining convenient browser-based management capabilities.

### Key Design Principles

- **Zero Public Exposure**: OpenClaw web ports (18789, 18791) are completely blocked from Internet access
- **VNet Isolation**: All workload VMs operate without public IP addresses
- **Bastion Access**: Azure Bastion provides secure RDP/SSH connectivity without exposing management ports
- **Zone Redundancy**: Both VMs deployed in Availability Zone 3 for enhanced reliability
- **Least Privilege**: NSG rules enforce defense-in-depth with explicit deny policies

---

## Architecture

### Components

| Component | Name | Purpose |
|-----------|------|---------|
| **Linux VM** | oclaw2026linux | OpenClaw application server |
| **Windows VM** | oclaw-admin-win11m | Management/admin workstation |
| **VNet** | vnet-eastus2 | Isolated network (172.20.0.0/16) |
| **Workload Subnet** | snet-eastus2-1 | VM subnet (172.20.0.0/24) |
| **Bastion Subnet** | AzureBastionSubnet | Dedicated Bastion subnet (172.20.1.0/26) |
| **Bastion** | bastion-oclaw2026 | Secure remote access service |
| **NSG** | oclaw2026linux-nsg | Network security rules for Linux VM |
| **NSG** | vnet-eastus2-snet-eastus2-1-nsg-eastus2 | Network security rules for subnet |

### Resource Hierarchy

```
Azure Subscription
└── Resource Group: RG_OCLAW2026
    ├── Virtual Network: vnet-eastus2 (172.20.0.0/16)
    │   ├── Subnet: snet-eastus2-1 (172.20.0.0/24)
    │   │   ├── VM: oclaw2026linux (172.20.0.4)
    │   │   └── VM: oclaw-admin-win11m (172.20.0.5)
    │   └── Subnet: AzureBastionSubnet (172.20.1.0/26)
    │       └── Azure Bastion: bastion-oclaw2026
    ├── Network Security Groups
    │   ├── oclaw2026linux-nsg
    │   └── vnet-eastus2-snet-eastus2-1-nsg-eastus2
    └── Public IP: bastion-oclaw2026-pip (20.246.72.67)
```

---

## Network Topology Diagram

```
                                    INTERNET
                                        |
                                        |
            ┌───────────────────────────┼───────────────────────────┐
            │                           |                           │
            │                   Public IP Address                   │
            │                   20.246.72.67                        │
            │                           |                           │
            │                  [Azure Bastion]                      │
            │                 bastion-oclaw2026                     │
            │                           |                           │
            │             DNS: bst-48e3e7d2-9a44-...               │
            │                    .bastion.azure.com                 │
            │                           |                           │
            └───────────────────────────┼───────────────────────────┘
                                        |
                    AzureBastionSubnet (172.20.1.0/26)
                                        |
    ════════════════════════════════════════════════════════════════
                          vnet-eastus2
                      172.20.0.0/16 (VNet)
    ════════════════════════════════════════════════════════════════
                                        |
                snet-eastus2-1 (172.20.0.0/24)
                                        |
                 ┌──────────────────────┴──────────────────────┐
                 |                                              |
        ┌────────┴────────┐                         ┌──────────┴─────────┐
        │  Linux VM       │                         │   Windows VM       │
        │ oclaw2026linux  │◄────────────────────────┤ oclaw-admin-win11m │
        │                 │    HTTP: 18789, 18791   │                    │
        │  172.20.0.4     │                         │   172.20.0.5       │
        │  Zone 3         │                         │   Zone 3           │
        │  NO PUBLIC IP   │                         │   NO PUBLIC IP     │
        │                 │                         │                    │
        │  OpenClaw       │                         │  Windows 11 24H2   │
        │  Ports:         │                         │  Enterprise        │
        │  • 18789 (Web)  │                         │  • Edge Browser    │
        │  • 18791 (Ctrl) │                         │  • RDP via Bastion │
        └─────────────────┘                         └────────────────────┘
             |
        ┌────┴────┐
        │   NSG   │
        │  Rules  │
        ├─────────┤
        │ ❌ 100  │ DenyOpenClawWebGateway (18789 from Internet)
        │ ❌ 101  │ DenyOpenClawControl (18791 from Internet)
        │ ✅ 200  │ AllowSSH (22 from Internet)
        │ ✅ 65000│ AllowVnetInBound (All ports from VNet)
        └─────────┘

═══════════════════════════════════════════════════════════════════

LEGEND:
  ═══   Network boundary
  ◄──   Network traffic flow
  ❌    Deny rule
  ✅    Allow rule

TRAFFIC FLOWS:
  1. Admin connects to Bastion public DNS/IP via Azure Portal
  2. Bastion provides RDP session to Windows VM (172.20.0.5)
  3. From Windows VM, browser connects to OpenClaw at 172.20.0.4:18789
  4. Internet cannot directly access ports 18789/18791 (blocked by NSG)
  5. SSH access to Linux VM allowed from Internet (port 22 only)
```

---

## Azure Bastion

### What is Azure Bastion?

Azure Bastion is a fully managed PaaS service that provides secure and seamless RDP/SSH connectivity to your virtual machines directly through the Azure Portal. It eliminates the need to expose RDP (3389) or SSH (22) ports to the public Internet.

### Why We're Using Bastion

| Traditional Approach | Azure Bastion Approach |
|---------------------|------------------------|
| VM needs public IP | VM has no public IP |
| RDP/SSH exposed to Internet | No management ports exposed |
| Must manage NSG rules for RDP | Bastion handles secure connectivity |
| Vulnerable to brute force attacks | Protected by Azure AD authentication |
| Need VPN or jump box | Direct browser-based access |

### Bastion Configuration

- **Name**: bastion-oclaw2026
- **SKU**: Standard
- **VNet**: vnet-eastus2
- **Dedicated Subnet**: AzureBastionSubnet (172.20.1.0/26)
- **Public IP**: 20.246.72.67
- **DNS Name**: bst-48e3e7d2-9a44-436a-a55e-dbe2a867fae1.bastion.azure.com

### Bastion Features

- **Secure RDP/SSH**: TLS-encrypted sessions through port 443
- **Azure Portal Integration**: Connect directly from VM blade
- **No Public IP Required**: VMs remain completely private
- **NSG Compatible**: Works seamlessly with restrictive NSG rules
- **Session Recording**: Optional logging for compliance
- **Copy/Paste**: Clipboard integration (Standard SKU)

---

## Security Model

### Defense-in-Depth Strategy

This architecture implements multiple layers of security:

```
Layer 1: Azure AD Authentication
         └─> User must authenticate to Azure Portal

Layer 2: Azure RBAC
         └─> User must have permissions to access VMs

Layer 3: Azure Bastion
         └─> Secure, audited connection through managed service

Layer 4: VNet Isolation
         └─> VMs have no public IPs, isolated network

Layer 5: Network Security Groups
         └─> Explicit deny rules for OpenClaw ports from Internet

Layer 6: VM-Level Security
         └─> OS firewall, authentication, logging
```

### Network Security Group Rules

#### Linux VM NSG (oclaw2026linux-nsg)

| Priority | Rule Name | Direction | Source | Dest Port | Protocol | Action | Purpose |
|----------|-----------|-----------|--------|-----------|----------|--------|---------|
| **100** | DenyOpenClawWebGateway | Inbound | Internet | 18789 | TCP | ❌ **DENY** | Block public access to Web Gateway |
| **101** | DenyOpenClawControl | Inbound | Internet | 18791 | TCP | ❌ **DENY** | Block public access to Control interface |
| **200** | AllowSSH | Inbound | Internet | 22 | TCP | ✅ **ALLOW** | SSH administrative access |
| **65000** | AllowVnetInBound | Inbound | VirtualNetwork | * | * | ✅ **ALLOW** | Internal VNet traffic |
| **65001** | AllowAzureLoadBalancerInBound | Inbound | AzureLoadBalancer | * | * | ✅ **ALLOW** | Azure health probes |
| **65500** | DenyAllInBound | Inbound | * | * | * | ❌ **DENY** | Default deny all |

### Access Control Matrix

| Source | Destination | Port | Status | Purpose |
|--------|-------------|------|--------|---------|
| Internet | Linux VM | 22 | ✅ Allowed | SSH administration |
| Internet | Linux VM | 18789 | ❌ Blocked | Web Gateway (security) |
| Internet | Linux VM | 18791 | ❌ Blocked | Control interface (security) |
| Internet | Windows VM | 3389 | ❌ Blocked | No public RDP (uses Bastion) |
| Windows VM | Linux VM | 18789 | ✅ Allowed | OpenClaw Web Gateway |
| Windows VM | Linux VM | 18791 | ✅ Allowed | OpenClaw Control |
| Azure Bastion | Windows VM | 3389 | ✅ Allowed | Secure RDP session |
| Azure Portal | Azure Bastion | 443 | ✅ Allowed | Bastion management |

### Security Posture Summary

**✅ Excellent Security Configuration**

1. **Minimal Public Exposure**: Only SSH (port 22) exposed to Internet for emergency access
2. **No Public IPs on Workloads**: Both VMs are completely private
3. **OpenClaw Isolation**: Web interface completely isolated from public Internet
4. **Bastion Protection**: RDP access protected by Azure AD and Bastion service
5. **Explicit Deny Rules**: Defense-in-depth with priority-based rule enforcement
6. **VNet Segmentation**: Bastion on dedicated subnet, workloads on separate subnet
7. **Zone Redundancy**: Both VMs in same zone for reliability

---

## Virtual Machine Details

### Linux VM: oclaw2026linux

| Property | Value |
|----------|-------|
| **VM Name** | oclaw2026linux |
| **Resource Group** | RG_OCLAW2026 |
| **Region** | East US 2 |
| **Availability Zone** | Zone 3 |
| **VM Size** | Standard_E2s_v3 |
| **vCPUs** | 2 |
| **Memory** | 16 GB |
| **OS Disk** | Premium SSD LRS |
| **Operating System** | Linux (Ubuntu/CentOS) |
| **Private IP** | 172.20.0.4 |
| **Public IP** | None (removed for security) |
| **VNet** | vnet-eastus2 |
| **Subnet** | snet-eastus2-1 |
| **NIC** | oclaw2026linux787_z3 |
| **NSG** | oclaw2026linux-nsg |
| **Admin Username** | azureadmin |

#### OpenClaw Configuration

- **Web Gateway Port**: 18789 (blocked from Internet, accessible from VNet)
- **Control/Browser Port**: 18791 (blocked from Internet, accessible from VNet)
- **SSH Port**: 22 (allowed from Internet)

### Windows VM: oclaw-admin-win11m

| Property | Value |
|----------|-------|
| **VM Name** | oclaw-admin-win11m |
| **Resource Group** | RG_OCLAW2026 |
| **Region** | East US 2 |
| **Availability Zone** | Zone 3 |
| **VM Size** | Standard_E2s_v3 |
| **vCPUs** | 2 |
| **Memory** | 16 GB |
| **OS Disk** | Premium SSD LRS |
| **Operating System** | Windows 11 Enterprise 24H2 |
| **Private IP** | 172.20.0.5 |
| **Public IP** | None (uses Bastion) |
| **VNet** | vnet-eastus2 |
| **Subnet** | snet-eastus2-1 |
| **Admin Username** | azureadmin |
| **Primary Purpose** | Management workstation for OpenClaw web interface |

#### Pre-installed Software

- Microsoft Edge (default browser)
- Remote Desktop client
- Network utilities (ping, tracert, etc.)

### Availability Zone Rationale

Both VMs are deployed in **Zone 3** for the following reasons:

- **Low Latency**: Same-zone placement minimizes network latency
- **Simplified Design**: No cross-zone traffic routing
- **Cost Efficiency**: No cross-zone data transfer charges
- **Future Expansion**: Can add VMs in Zones 1 and 2 for high availability if needed

---

## Connection Instructions

### Method 1: Connect via Azure Portal (Recommended)

#### Step 1: Navigate to Windows VM

1. Open Azure Portal: https://portal.azure.com
2. Navigate to **Virtual Machines**
3. Select **oclaw-admin-win11m**

#### Step 2: Connect via Bastion

1. Click **Connect** button at top of VM blade
2. Select **Connect via Bastion** from dropdown
3. Enter credentials:
   - **Username**: `azureadmin`
   - **Authentication Type**: Password
   - **Password**: `iVhGDstb1WwZo499eTEuAa1!`
4. Click **Connect**

#### Step 3: Wait for Session

- Bastion will establish secure RDP session in new browser tab
- Session may take 10-30 seconds to initialize
- You'll see Windows 11 desktop when connected

### Method 2: Connect via Azure CLI

```bash
# Connect to Windows VM via Bastion
az network bastion rdp \
  --name bastion-oclaw2026 \
  --resource-group RG_OCLAW2026 \
  --target-resource-id /subscriptions/{subscription-id}/resourceGroups/RG_OCLAW2026/providers/Microsoft.Compute/virtualMachines/oclaw-admin-win11m
```

### Method 3: SSH to Linux VM (Emergency Access)

```bash
# Direct SSH access (bypasses Bastion)
# Note: Requires Linux VM to have public IP or SSH from Windows VM
ssh azureadmin@172.20.0.4
```

### Troubleshooting Connection Issues

| Issue | Solution |
|-------|----------|
| "Cannot connect to Bastion" | Verify Bastion is running and not stopped |
| "Authentication failed" | Double-check credentials (case-sensitive) |
| "Network error" | Verify VM is running (not stopped/deallocated) |
| "Timeout connecting" | Check NSG rules haven't been modified |
| "Session disconnected" | Check Azure service health for Bastion |

---

## OpenClaw Access

### From Windows Management VM

Once connected to the Windows VM via Bastion, you can access OpenClaw through the web browser.

#### Step 1: Open Microsoft Edge

1. From Windows 11 desktop, open Microsoft Edge browser
2. You may pin Edge to taskbar for quick access

#### Step 2: Access OpenClaw Web Interface

Navigate to OpenClaw URLs using the Linux VM's private IP:

**Primary Interface - Web Gateway**
```
http://172.20.0.4:18789
```

**Secondary Interface - Control/Browser**
```
http://172.20.0.4:18791
```

#### Step 3: Bookmark for Convenience

1. Press **Ctrl+D** to bookmark the page
2. Save to Favorites Bar for quick access
3. Optionally create desktop shortcut

### OpenClaw Ports Reference

| Port | Interface | Purpose | URL |
|------|-----------|---------|-----|
| **18789** | Web Gateway | Primary web-based management interface | http://172.20.0.4:18789 |
| **18791** | Browser/Control | Secondary control interface | http://172.20.0.4:18791 |

### Network Path

```
Your Browser
    ↓
Azure Portal (HTTPS over Internet)
    ↓
Azure Bastion (TLS encrypted)
    ↓
Windows VM (172.20.0.5) via RDP
    ↓
Edge Browser on Windows VM
    ↓
OpenClaw on Linux VM (172.20.0.4) via HTTP ports 18789/18791
```

### Security Notes

- OpenClaw traffic between Windows and Linux VMs is **unencrypted HTTP**
- This is acceptable because traffic stays within Azure VNet (never touches Internet)
- VNet traffic is isolated at the Azure fabric layer
- Consider enabling TLS in OpenClaw for additional defense-in-depth

### Testing Connectivity

From Windows VM, open PowerShell and test connectivity:

```powershell
# Test if OpenClaw ports are reachable
Test-NetConnection -ComputerName 172.20.0.4 -Port 18789
Test-NetConnection -ComputerName 172.20.0.4 -Port 18791

# Expected output: TcpTestSucceeded : True
```

---

## Credentials and Secrets

### VM Administrator Credentials

**⚠️ SENSITIVE INFORMATION - STORE SECURELY**

| Resource | Username | Password |
|----------|----------|----------|
| **Linux VM** (oclaw2026linux) | azureadmin | iVhGDstb1WwZo499eTEuAa1! |
| **Windows VM** (oclaw-admin-win11m) | azureadmin | iVhGDstb1WwZo499eTEuAa1! |

### Credential Storage Recommendations

1. **Azure Key Vault** (Recommended for production)
   - Create Key Vault in RG_OCLAW2026
   - Store credentials as secrets
   - Grant access via Azure RBAC

2. **Password Manager**
   - Use enterprise password manager (1Password, LastPass, etc.)
   - Share credentials securely with team members

3. **Azure CLI Secret Storage**
   ```bash
   # Store in environment variable (local machine only)
   export OCLAW_ADMIN_PASSWORD="iVhGDstb1WwZo499eTEuAa1!"
   ```

4. **Local Encrypted File**
   - Store in encrypted file on local machine
   - Use disk encryption (BitLocker, FileVault, etc.)

### SSH Key Authentication (Recommended Enhancement)

For improved security, consider switching to SSH key authentication:

```bash
# Generate SSH key pair
ssh-keygen -t rsa -b 4096 -f ~/.ssh/oclaw2026_rsa

# Add public key to Linux VM
az vm user update \
  --resource-group RG_OCLAW2026 \
  --name oclaw2026linux \
  --username azureadmin \
  --ssh-key-value "$(cat ~/.ssh/oclaw2026_rsa.pub)"

# Connect using key
ssh -i ~/.ssh/oclaw2026_rsa azureadmin@172.20.0.4
```

### Password Rotation Policy

**Recommended Schedule:**

- **Every 90 days**: Rotate VM administrator passwords
- **After personnel changes**: Rotate immediately when team members leave
- **After suspected compromise**: Rotate immediately

**Rotation Commands:**

```bash
# Update Linux VM password
az vm user update \
  --resource-group RG_OCLAW2026 \
  --name oclaw2026linux \
  --username azureadmin \
  --password 'NewSecurePassword123!'

# Update Windows VM password
az vm user update \
  --resource-group RG_OCLAW2026 \
  --name oclaw-admin-win11m \
  --username azureadmin \
  --password 'NewSecurePassword123!'
```

---

## Cost Information

### Monthly Cost Estimate (East US 2)

| Resource | SKU/Size | Quantity | Est. Monthly Cost |
|----------|----------|----------|-------------------|
| **Linux VM** | Standard_E2s_v3 | 1 | $125.52 |
| **Windows VM** | Standard_E2s_v3 | 1 | $125.52 |
| **Premium SSD** | 128 GB P10 | 2 | $38.40 |
| **Azure Bastion** | Standard SKU | 1 | $146.00 |
| **VNet** | Standard | 1 | $0.00 |
| **NSG** | Standard | 2 | $0.00 |
| **Public IP** | Standard Static | 1 | $3.65 |
| **Data Transfer** | Outbound | ~5 GB | $0.43 |
| | | **Total** | **~$439.52/month** |

### Cost Breakdown by Category

```
Compute (VMs):           $251.04  (57%)
Storage (Disks):          $38.40   (9%)
Bastion Service:         $146.00  (33%)
Networking:                $4.08   (1%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total:                   $439.52/month
```

### Cost Optimization Opportunities

#### Option 1: Downsize Windows VM (Low Usage)

If Windows VM is used infrequently (< 4 hours/day):

```
Replace: Standard_E2s_v3 ($125.52/mo)
With:    Standard_B2ms ($62.05/mo)
Savings: $63.47/month (14% total reduction)
```

**Recommendation**: Good for occasional admin tasks, web browsing only

#### Option 2: Deallocate VMs When Not in Use

```bash
# Stop (deallocate) Windows VM to save compute costs
az vm deallocate --resource-group RG_OCLAW2026 --name oclaw-admin-win11m

# Restart when needed
az vm start --resource-group RG_OCLAW2026 --name oclaw-admin-win11m

# Savings: $4.18/day when deallocated (compute only, still pay for storage)
```

**Monthly Savings if VM stopped 50% of time**: $62.76

#### Option 3: Use Reserved Instances (1-year commitment)

```
Standard_E2s_v3 (1-year reserved):  $81.76/month per VM
Savings vs pay-as-you-go:           $43.76/month per VM
Total savings for 2 VMs:            $87.52/month (20% total reduction)
```

**Break-even**: Immediate if VMs run 24/7 for next year

#### Option 4: Downgrade Bastion to Basic SKU

```
Replace: Standard SKU ($146/mo)
With:    Basic SKU ($140/mo)
Savings: $6/month (1.4% reduction)
Trade-off: Lose IP-based connections, copy/paste features
```

**Recommendation**: Only if advanced features not needed

### Cost Monitoring

**Set up Azure Cost Alerts:**

```bash
# Create budget alert
az consumption budget create \
  --resource-group RG_OCLAW2026 \
  --budget-name oclaw-monthly-budget \
  --amount 500 \
  --time-grain Monthly \
  --start-date $(date +%Y-%m-01) \
  --end-date 2027-12-31
```

**Monitor in Azure Portal:**
1. Navigate to **Cost Management + Billing**
2. Select **Cost Analysis**
3. Filter by Resource Group: RG_OCLAW2026
4. View daily/monthly trends

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: Cannot Connect to Windows VM via Bastion

**Symptoms:**
- "Connection failed" error in Azure Portal
- Timeout when clicking "Connect via Bastion"

**Troubleshooting Steps:**

1. **Verify VM is Running**
   ```bash
   az vm get-instance-view \
     --resource-group RG_OCLAW2026 \
     --name oclaw-admin-win11m \
     --query "instanceView.statuses[?starts_with(code, 'PowerState/')].displayStatus" \
     -o tsv
   ```
   Expected: `VM running`

2. **Verify Bastion is Provisioned**
   ```bash
   az network bastion show \
     --resource-group RG_OCLAW2026 \
     --name bastion-oclaw2026 \
     --query "provisioningState" \
     -o tsv
   ```
   Expected: `Succeeded`

3. **Check Bastion Subnet Configuration**
   - Must be named exactly `AzureBastionSubnet`
   - Must be at least /26 in size (64 IPs)
   - Must be in same VNet as target VM

4. **Verify NSG Rules Don't Block Bastion**
   - Bastion needs to reach VM on RDP port 3389
   - Check VNet internal traffic is allowed

#### Issue: Cannot Access OpenClaw from Windows VM

**Symptoms:**
- Browser cannot reach http://172.20.0.4:18789
- Connection timeout or refused

**Troubleshooting Steps:**

1. **Test Network Connectivity**
   ```powershell
   # From Windows VM PowerShell
   Test-NetConnection -ComputerName 172.20.0.4 -Port 18789
   Test-NetConnection -ComputerName 172.20.0.4 -Port 18791
   ```

2. **Verify Linux VM is Running**
   ```bash
   az vm get-instance-view \
     --resource-group RG_OCLAW2026 \
     --name oclaw2026linux \
     --query "instanceView.statuses[?starts_with(code, 'PowerState/')].displayStatus" \
     -o tsv
   ```

3. **Check OpenClaw Service Status**
   ```bash
   # SSH to Linux VM
   ssh azureadmin@172.20.0.4

   # Check if OpenClaw is running
   sudo systemctl status openclaw
   # or
   sudo netstat -tlnp | grep -E ':(18789|18791)'
   ```

4. **Verify NSG Allows VNet Traffic**
   ```bash
   az network nsg rule show \
     --resource-group RG_OCLAW2026 \
     --nsg-name oclaw2026linux-nsg \
     --name AllowVnetInBound
   ```

#### Issue: SSH Access to Linux VM Not Working

**Symptoms:**
- Connection timeout when trying to SSH
- "No route to host" error

**Troubleshooting Steps:**

1. **Verify Linux VM Has Public IP (if accessing from Internet)**
   ```bash
   az vm show \
     --resource-group RG_OCLAW2026 \
     --name oclaw2026linux \
     --query "publicIps" \
     -o tsv
   ```
   Note: VM currently has no public IP by design

2. **SSH from Windows VM Instead**
   - Connect to Windows VM via Bastion
   - Use built-in SSH client or install PuTTY
   - SSH to 172.20.0.4 from Windows VM

3. **Verify SSH NSG Rule**
   ```bash
   az network nsg rule show \
     --resource-group RG_OCLAW2026 \
     --nsg-name oclaw2026linux-nsg \
     --name AllowSSH
   ```

#### Issue: Bastion Session Disconnects Frequently

**Possible Causes:**
- Browser timeout settings
- Network instability
- Azure service issues

**Solutions:**

1. **Use Supported Browser**
   - Microsoft Edge (recommended)
   - Google Chrome
   - Avoid Firefox (known compatibility issues)

2. **Disable Browser Extensions**
   - Ad blockers may interfere
   - Security extensions may block WebSockets

3. **Check Azure Service Health**
   ```bash
   az monitor metrics list \
     --resource /subscriptions/{subscription-id}/resourceGroups/RG_OCLAW2026/providers/Microsoft.Network/bastionHosts/bastion-oclaw2026 \
     --metric "Sessions" \
     --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
     --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ)
   ```

#### Issue: High Azure Costs

**Diagnosis:**

```bash
# View cost by resource
az consumption usage list \
  --start-date $(date -d '30 days ago' +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  --query "[?contains(instanceName, 'oclaw')].[instanceName, pretaxCost, usageStart]" \
  -o table
```

**Common Culprits:**
- VMs running 24/7 unnecessarily
- Premium storage for non-critical data
- Data egress charges (large downloads from Azure)
- Bastion Standard SKU if Basic would suffice

**Cost Reduction Steps:**
1. Stop/deallocate VMs when not in use
2. Consider Reserved Instances for long-term workloads
3. Review storage tiers (move cold data to Cool/Archive)
4. Monitor data transfer out of Azure

### Emergency Contacts and Resources

**Azure Support:**
- Portal: https://portal.azure.com -> Support + troubleshooting
- Phone: 1-800-642-7676 (US)

**Azure Status:**
- https://status.azure.com/en-us/status

**Documentation:**
- Azure Bastion: https://learn.microsoft.com/azure/bastion/
- NSG Rules: https://learn.microsoft.com/azure/virtual-network/network-security-groups-overview

---

## Appendix: Quick Reference Commands

### VM Management

```bash
# Start VMs
az vm start --resource-group RG_OCLAW2026 --name oclaw2026linux
az vm start --resource-group RG_OCLAW2026 --name oclaw-admin-win11m

# Stop VMs (deallocate to save costs)
az vm deallocate --resource-group RG_OCLAW2026 --name oclaw2026linux
az vm deallocate --resource-group RG_OCLAW2026 --name oclaw-admin-win11m

# Restart VMs
az vm restart --resource-group RG_OCLAW2026 --name oclaw2026linux
az vm restart --resource-group RG_OCLAW2026 --name oclaw-admin-win11m

# Check VM status
az vm get-instance-view \
  --resource-group RG_OCLAW2026 \
  --name oclaw2026linux \
  --query "instanceView.statuses[?starts_with(code, 'PowerState/')].displayStatus" \
  -o tsv
```

### Network Security

```bash
# List NSG rules
az network nsg rule list \
  --resource-group RG_OCLAW2026 \
  --nsg-name oclaw2026linux-nsg \
  --include-default \
  -o table

# Show specific rule
az network nsg rule show \
  --resource-group RG_OCLAW2026 \
  --nsg-name oclaw2026linux-nsg \
  --name DenyOpenClawWebGateway

# Update rule (example: change priority)
az network nsg rule update \
  --resource-group RG_OCLAW2026 \
  --nsg-name oclaw2026linux-nsg \
  --name DenyOpenClawWebGateway \
  --priority 100
```

### Bastion Management

```bash
# Show Bastion details
az network bastion show \
  --resource-group RG_OCLAW2026 \
  --name bastion-oclaw2026

# Update Bastion SKU
az network bastion update \
  --resource-group RG_OCLAW2026 \
  --name bastion-oclaw2026 \
  --sku Standard

# Delete Bastion (to save costs when not needed)
az network bastion delete \
  --resource-group RG_OCLAW2026 \
  --name bastion-oclaw2026
```

### Monitoring and Diagnostics

```bash
# View VM metrics
az monitor metrics list \
  --resource /subscriptions/{subscription-id}/resourceGroups/RG_OCLAW2026/providers/Microsoft.Compute/virtualMachines/oclaw2026linux \
  --metric "Percentage CPU" \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)

# Enable boot diagnostics
az vm boot-diagnostics enable \
  --resource-group RG_OCLAW2026 \
  --name oclaw2026linux

# Get boot diagnostics log
az vm boot-diagnostics get-boot-log \
  --resource-group RG_OCLAW2026 \
  --name oclaw2026linux
```

---

**Document Version**: 1.0
**Last Updated**: 2026-02-05
**Maintained By**: Infrastructure Team
**Review Schedule**: Quarterly

---

## Document Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-02-05 | 1.0 | Initial documentation creation | Claude Code |

---

**End of Document**
