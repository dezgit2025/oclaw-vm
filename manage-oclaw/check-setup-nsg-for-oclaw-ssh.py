#!/usr/bin/env python3
"""Check and setup NSG rules for SSH access to oclaw VM.

Detects your current public IP, verifies the oclaw VM is running,
checks/creates NSG rules on both the subnet and VM NSGs, and tests SSH.
"""

import subprocess
import sys
import json

# ── Config ──────────────────────────────────────────────────────────────────
RESOURCE_GROUP = "RG_OCLAW2026"
VM_NAME = "oclaw2026linux"
VM_NSG = "oclaw2026linux-nsg"
SUBNET_NSG = "vnet-eastus2-snet-eastus2-1-nsg-eastus2"
RULE_NAME = "AllowSSH-MyIP"
RULE_PRIORITY = 100
SSH_HOST = "oclaw"
SSH_TIMEOUT = 10


def run(cmd, parse_json=False):
    """Run a command and return stdout. Exit on failure."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FAIL: {' '.join(cmd)}")
        print(f"  {result.stderr.strip()}")
        return None
    output = result.stdout.strip()
    if parse_json and output:
        return json.loads(output)
    return output


def get_public_ip():
    """Get current public IP address."""
    print("\n[1] Detecting public IP...")
    ip = run(["curl", "-s", "ifconfig.me"])
    if not ip:
        print("  Could not detect public IP.")
        sys.exit(1)
    print(f"  Your IP: {ip}")
    return ip


def check_vm_running():
    """Check if the oclaw VM is running."""
    print(f"\n[2] Checking VM '{VM_NAME}' power state...")
    data = run([
        "az", "vm", "get-instance-view",
        "--name", VM_NAME,
        "--resource-group", RESOURCE_GROUP,
        "--query", "instanceView.statuses[?starts_with(code,'PowerState')].displayStatus | [0]",
        "-o", "json",
    ], parse_json=True)
    if data is None:
        print("  Could not query VM status.")
        return False
    print(f"  VM status: {data}")
    if data != "VM running":
        print("  VM is NOT running. Start it before proceeding.")
        return False
    return True


def check_nsg_rule(nsg_name, my_ip):
    """Check if an SSH allow rule exists for our IP on the given NSG."""
    rules = run([
        "az", "network", "nsg", "rule", "list",
        "--nsg-name", nsg_name,
        "--resource-group", RESOURCE_GROUP,
        "--query", f"[?name=='{RULE_NAME}']",
        "-o", "json",
    ], parse_json=True)

    if rules is None:
        return None  # error

    if not rules:
        return False  # no rule exists

    rule = rules[0]
    source = rule.get("sourceAddressPrefix", "")
    access = rule.get("access", "")
    port = rule.get("destinationPortRange", "")

    if source == my_ip and access == "Allow" and port == "22":
        return True  # rule exists and matches

    # Rule exists but with different IP
    return "stale"


def create_nsg_rule(nsg_name, my_ip):
    """Create SSH allow rule for our IP on the given NSG."""
    result = run([
        "az", "network", "nsg", "rule", "create",
        "--nsg-name", nsg_name,
        "--resource-group", RESOURCE_GROUP,
        "--name", RULE_NAME,
        "--priority", str(RULE_PRIORITY),
        "--direction", "Inbound",
        "--access", "Allow",
        "--protocol", "Tcp",
        "--source-address-prefixes", my_ip,
        "--destination-port-ranges", "22",
        "--destination-address-prefixes", "*",
        "--source-port-ranges", "*",
        "-o", "json",
    ])
    return result is not None


def update_nsg_rule(nsg_name, my_ip):
    """Update existing SSH rule with new IP."""
    result = run([
        "az", "network", "nsg", "rule", "update",
        "--nsg-name", nsg_name,
        "--resource-group", RESOURCE_GROUP,
        "--name", RULE_NAME,
        "--source-address-prefixes", my_ip,
        "-o", "json",
    ])
    return result is not None


def handle_nsg(nsg_name, label, my_ip):
    """Check and fix NSG rule for a given NSG."""
    print(f"\n  Checking '{nsg_name}'...")
    status = check_nsg_rule(nsg_name, my_ip)

    if status is True:
        print(f"    Rule '{RULE_NAME}' exists with correct IP ({my_ip}).")
        return True
    elif status == "stale":
        print(f"    Rule '{RULE_NAME}' exists but has wrong IP. Updating...")
        if update_nsg_rule(nsg_name, my_ip):
            print(f"    Updated to {my_ip}.")
            return True
        else:
            print(f"    Failed to update rule.")
            return False
    elif status is False:
        print(f"    No rule found. Creating '{RULE_NAME}' for {my_ip}...")
        if create_nsg_rule(nsg_name, my_ip):
            print(f"    Rule created.")
            return True
        else:
            print(f"    Failed to create rule.")
            return False
    else:
        print(f"    Error checking NSG rules.")
        return False


def test_ssh():
    """Test SSH connectivity to oclaw."""
    print(f"\n[4] Testing SSH to '{SSH_HOST}'...")
    result = subprocess.run(
        ["ssh", "-o", f"ConnectTimeout={SSH_TIMEOUT}",
         "-o", "StrictHostKeyChecking=accept-new",
         SSH_HOST, "echo", "SSH_OK"],
        capture_output=True, text=True,
    )
    if result.returncode == 0 and "SSH_OK" in result.stdout:
        print("  SSH connection successful.")
        return True
    else:
        print("  SSH connection FAILED.")
        if result.stderr.strip():
            print(f"  {result.stderr.strip()}")
        return False


def main():
    print("=" * 60)
    print("  oclaw SSH NSG Setup & Check")
    print("=" * 60)

    my_ip = get_public_ip()

    if not check_vm_running():
        sys.exit(1)

    print(f"\n[3] Checking NSG rules for SSH (port 22)...")
    subnet_ok = handle_nsg(SUBNET_NSG, "Subnet NSG", my_ip)
    vm_ok = handle_nsg(VM_NSG, "VM NSG", my_ip)

    if not (subnet_ok and vm_ok):
        print("\nNSG setup incomplete. Fix errors above before testing SSH.")
        sys.exit(1)

    if not test_ssh():
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  All checks passed. SSH to oclaw is ready.")
    print("=" * 60)


if __name__ == "__main__":
    main()
