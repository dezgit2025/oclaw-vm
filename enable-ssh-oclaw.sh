#!/bin/bash
# Re-enable SSH to oclaw2026linux VM
# Run this when Azure policy removes the NSG rules

set -e

MY_IP=$(curl -s ifconfig.me)
echo "Adding SSH rules for IP: $MY_IP"

# Add to NIC-level NSG
echo "Updating NIC NSG (oclaw2026linux-nsg)..."
az network nsg rule create --name AllowSSHFromMyIP \
  --nsg-name oclaw2026linux-nsg --resource-group rg_oclaw2026 \
  --priority 105 --direction Inbound --access Allow --protocol Tcp \
  --source-address-prefixes $MY_IP --destination-port-ranges 22 \
  -o none 2>/dev/null || az network nsg rule update --name AllowSSHFromMyIP \
  --nsg-name oclaw2026linux-nsg --resource-group rg_oclaw2026 \
  --source-address-prefixes $MY_IP -o none

# Add to Subnet-level NSG
echo "Updating Subnet NSG (vnet-eastus2-snet-eastus2-1-nsg-eastus2)..."
az network nsg rule create --name AllowSSHFromMyIP \
  --nsg-name vnet-eastus2-snet-eastus2-1-nsg-eastus2 --resource-group rg_oclaw2026 \
  --priority 100 --direction Inbound --access Allow --protocol Tcp \
  --source-address-prefixes $MY_IP --destination-port-ranges 22 \
  -o none 2>/dev/null || az network nsg rule update --name AllowSSHFromMyIP \
  --nsg-name vnet-eastus2-snet-eastus2-1-nsg-eastus2 --resource-group rg_oclaw2026 \
  --source-address-prefixes $MY_IP -o none

echo "Done. Testing SSH..."
ssh -o ConnectTimeout=15 oclaw "echo 'SSH working!' && hostname"
