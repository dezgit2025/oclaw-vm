#!/bin/bash
#
# fix-oclaw-linux-nsg.sh
# Fixes SSH access to oclaw2026linux VM by adding/updating NSG rules
#
# Azure has TWO levels of NSG filtering:
#   1. Subnet-level NSG: vnet-eastus2-snet-eastus2-1-nsg-eastus2
#   2. NIC-level NSG: oclaw2026linux-nsg
#
# Traffic must pass BOTH. Azure Policy/JIT may remove rules from either or both.
#

set -e

# Configuration
RESOURCE_GROUP="RG_OCLAW2026"
NIC_NSG="oclaw2026linux-nsg"
SUBNET_NSG="vnet-eastus2-snet-eastus2-1-nsg-eastus2"
RULE_NAME="AllowSSHFromMyIP"
SSH_HOST="oclaw"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "  OpenClaw Linux VM SSH Fix Script"
echo "========================================"
echo ""

# Step 1: Check Azure CLI authentication
echo -n "Checking Azure CLI authentication... "
if ! az account show &>/dev/null; then
    echo -e "${RED}FAILED${NC}"
    echo "Error: Not logged in to Azure CLI. Run 'az login' first."
    exit 1
fi
echo -e "${GREEN}OK${NC}"

# Step 2: Get current public IP
echo -n "Getting current public IP... "
MY_IP=$(curl -s --connect-timeout 5 ifconfig.me)
if [[ -z "$MY_IP" || ! "$MY_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${RED}FAILED${NC}"
    echo "Error: Could not determine public IP address."
    exit 1
fi
echo -e "${GREEN}$MY_IP${NC}"

# Step 3: Check VM power state
echo -n "Checking VM power state... "
VM_STATE=$(az vm show -n oclaw2026linux -g "$RESOURCE_GROUP" -d --query powerState -o tsv 2>/dev/null)
if [[ "$VM_STATE" != "VM running" ]]; then
    echo -e "${YELLOW}$VM_STATE${NC}"
    echo "Warning: VM is not running. Starting VM..."
    az vm start -n oclaw2026linux -g "$RESOURCE_GROUP" --no-wait
    echo "VM start initiated. Wait 1-2 minutes, then re-run this script."
    exit 1
fi
echo -e "${GREEN}Running${NC}"

# Step 4: Update/Create NIC-level NSG rule
echo -n "Updating NIC NSG ($NIC_NSG)... "
if az network nsg rule show --nsg-name "$NIC_NSG" -g "$RESOURCE_GROUP" --name "$RULE_NAME" &>/dev/null; then
    # Rule exists, update it
    az network nsg rule update \
        --name "$RULE_NAME" \
        --nsg-name "$NIC_NSG" \
        --resource-group "$RESOURCE_GROUP" \
        --source-address-prefixes "$MY_IP" \
        -o none 2>/dev/null
    echo -e "${GREEN}Updated${NC}"
else
    # Rule doesn't exist, create it
    az network nsg rule create \
        --name "$RULE_NAME" \
        --nsg-name "$NIC_NSG" \
        --resource-group "$RESOURCE_GROUP" \
        --priority 105 \
        --direction Inbound \
        --access Allow \
        --protocol Tcp \
        --source-address-prefixes "$MY_IP" \
        --destination-port-ranges 22 \
        -o none 2>/dev/null
    echo -e "${GREEN}Created${NC}"
fi

# Step 5: Update/Create Subnet-level NSG rule
echo -n "Updating Subnet NSG ($SUBNET_NSG)... "
if az network nsg rule show --nsg-name "$SUBNET_NSG" -g "$RESOURCE_GROUP" --name "$RULE_NAME" &>/dev/null; then
    # Rule exists, update it
    az network nsg rule update \
        --name "$RULE_NAME" \
        --nsg-name "$SUBNET_NSG" \
        --resource-group "$RESOURCE_GROUP" \
        --source-address-prefixes "$MY_IP" \
        -o none 2>/dev/null
    echo -e "${GREEN}Updated${NC}"
else
    # Rule doesn't exist, create it
    az network nsg rule create \
        --name "$RULE_NAME" \
        --nsg-name "$SUBNET_NSG" \
        --resource-group "$RESOURCE_GROUP" \
        --priority 105 \
        --direction Inbound \
        --access Allow \
        --protocol Tcp \
        --source-address-prefixes "$MY_IP" \
        --destination-port-ranges 22 \
        -o none 2>/dev/null
    echo -e "${GREEN}Created${NC}"
fi

# Step 6: Wait for NSG rules to propagate
echo -n "Waiting for rules to propagate... "
sleep 3
echo -e "${GREEN}Done${NC}"

# Step 7: Test SSH connectivity
echo -n "Testing SSH connection... "
if ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no -o BatchMode=yes "$SSH_HOST" "exit 0" 2>/dev/null; then
    echo -e "${GREEN}SUCCESS${NC}"
    echo ""
    echo "========================================"
    echo -e "  ${GREEN}SSH is working!${NC}"
    echo "  Connect with: ssh $SSH_HOST"
    echo "========================================"
else
    echo -e "${RED}FAILED${NC}"
    echo ""
    echo "========================================"
    echo -e "  ${RED}SSH test failed${NC}"
    echo ""
    echo "  Troubleshooting steps:"
    echo "  1. Wait 30 seconds and try: ssh $SSH_HOST"
    echo "  2. Check public IP is attached:"
    echo "     az network public-ip show -n oclaw2026linux-ip -g $RESOURCE_GROUP --query ipAddress"
    echo "  3. Check effective NSG rules:"
    echo "     az network nic list-effective-nsg --name oclaw2026linux787_z3 -g rg_oclaw2026"
    echo "========================================"
    exit 1
fi
