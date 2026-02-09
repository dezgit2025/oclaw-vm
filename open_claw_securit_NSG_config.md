# OpenClaw VM Security NSG Configuration

## VM Information

- **VM Name**: oclaw2026linux
- **Resource Group**: RG_OCLAW2026
- **Location**: eastus2
- **Availability Zone**: 3
- **VM Size**: Standard_E2s_v3
- **Private IP**: 172.20.0.4

## Network Configuration

- **VNet**: vnet-eastus2
  - Address Space: 172.20.0.0/16
- **Subnet**: snet-eastus2-1
  - Address Prefix: 172.20.0.0/24
- **NIC**: oclaw2026linux787_z3
- **VM NSG**: oclaw2026linux-nsg
- **Subnet NSG**: vnet-eastus2-snet-eastus2-1-nsg-eastus2

## NSG Inbound Rules (Priority Order)

| Priority | Rule Name | Source | Port | Protocol | Access | Description |
|----------|-----------|--------|------|----------|--------|-------------|
| **100** | DenyOpenClawWebGateway | Internet | 18789 | TCP | ❌ **DENY** | Block public access to OpenClaw Web Gateway (18789) |
| **101** | DenyOpenClawControl | Internet | 18791 | TCP | ❌ **DENY** | Block public access to OpenClaw Browser/Control (18791) |
| **200** | AllowSSH | Internet | 22 | TCP | ✅ **ALLOW** | Allow SSH access from Internet |
| **65000** | AllowVnetInBound | VirtualNetwork | * | * | ✅ **ALLOW** | Allow inbound traffic from all VMs in VNET |
| **65001** | AllowAzureLoadBalancerInBound | AzureLoadBalancer | * | * | ✅ **ALLOW** | Allow inbound traffic from azure load balancer |
| **65500** | DenyAllInBound | * | * | * | ❌ **DENY** | Deny all inbound traffic |

## Access Summary

### From Internet (Public Access)

- ✅ **Port 22 (SSH)**: ALLOWED - SSH administrative access
- ❌ **Port 18789 (OpenClaw Web Gateway)**: BLOCKED
- ❌ **Port 18791 (OpenClaw Browser/Control)**: BLOCKED
- ❌ **All other ports**: BLOCKED

### From VNet (Internal Access)

- ✅ **All ports ALLOWED** - Including OpenClaw ports 18789 and 18791
- ✅ Future Windows admin VM will be able to access OpenClaw web interface at:
  - `http://172.20.0.4:18789` (Web Gateway)
  - `http://172.20.0.4:18791` (Browser/Control)

## OpenClaw Ports

| Port | Purpose | Public Access | VNet Access |
|------|---------|---------------|-------------|
| 18789 | Default Web Gateway Port | ❌ Blocked | ✅ Allowed |
| 18791 | Browser/Control Port | ❌ Blocked | ✅ Allowed |

## Security Posture

**✅ Excellent Security Configuration**

1. **Minimal Public Exposure**: Only SSH (port 22) exposed to Internet for administration
2. **OpenClaw Isolation**: OpenClaw ports completely isolated from public access
3. **Internal Connectivity**: Full internal VNet connectivity for administrative access
4. **Defense in Depth**: Explicit deny rules prevent accidental exposure
5. **Rule Priority**: Deny rules have higher priority than allow rules for OpenClaw ports

## Commands Used

### Create Deny Rules for OpenClaw Ports

```bash
# Block OpenClaw Web Gateway (18789)
az network nsg rule create \
  --nsg-name oclaw2026linux-nsg \
  -g RG_OCLAW2026 \
  --name DenyOpenClawWebGateway \
  --priority 100 \
  --direction Inbound \
  --access Deny \
  --protocol Tcp \
  --source-address-prefixes Internet \
  --source-port-ranges '*' \
  --destination-address-prefixes '*' \
  --destination-port-ranges 18789 \
  --description "Block public access to OpenClaw Web Gateway (18789)"

# Block OpenClaw Browser/Control (18791)
az network nsg rule create \
  --nsg-name oclaw2026linux-nsg \
  -g RG_OCLAW2026 \
  --name DenyOpenClawControl \
  --priority 101 \
  --direction Inbound \
  --access Deny \
  --protocol Tcp \
  --source-address-prefixes Internet \
  --source-port-ranges '*' \
  --destination-address-prefixes '*' \
  --destination-port-ranges 18791 \
  --description "Block public access to OpenClaw Browser/Control (18791)"
```

### Create Allow Rule for SSH

```bash
# Allow SSH access
az network nsg rule create \
  --nsg-name oclaw2026linux-nsg \
  -g RG_OCLAW2026 \
  --name AllowSSH \
  --priority 200 \
  --direction Inbound \
  --access Allow \
  --protocol Tcp \
  --source-address-prefixes Internet \
  --source-port-ranges '*' \
  --destination-address-prefixes '*' \
  --destination-port-ranges 22 \
  --description "Allow SSH access from Internet"
```

### Verify NSG Rules

```bash
# List all inbound rules
az network nsg rule list \
  --nsg-name oclaw2026linux-nsg \
  -g RG_OCLAW2026 \
  --include-default \
  --query "[?direction=='Inbound'].{Name:name, Priority:priority, Access:access, Protocol:protocol, Source:sourceAddressPrefix, DestPort:destinationPortRange}" \
  -o table
```

## Windows Admin VM Requirements

To create a Windows admin VM in the same VNet for OpenClaw administration:

### Required Parameters

```bash
--resource-group RG_OCLAW2026
--location eastus2
--vnet-name vnet-eastus2
--subnet snet-eastus2-1
--zone 3  # Same zone as oclaw2026linux for optimal latency
```

### Recommended Configuration

- **Size**: Standard_B2s or Standard_B2ms
- **OS**: Windows Server 2022 Datacenter (lower cost, sufficient for web browsing)
- **Private IP**: 172.20.0.5 (next available in subnet)
- **Purpose**: Browser-based administration of OpenClaw web interface

### Network Access from Windows VM

Once created in the same VNet, the Windows VM will have native access to:
- OpenClaw Web Gateway: `http://172.20.0.4:18789`
- OpenClaw Control Interface: `http://172.20.0.4:18791`

---

**Configuration Date**: 2026-02-05
**Last Updated**: 2026-02-05
