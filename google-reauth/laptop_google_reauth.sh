#!/usr/bin/env bash
set -euo pipefail

# Run this on YOUR LAPTOP.
# Purpose: guide you through the tunnel + then kick off the VM-side reauth script.
#
# Usage:
#   ./laptop_google_reauth.sh <ssh_target> <gmail_account>
# Example:
#   ./laptop_google_reauth.sh desazure@1.2.3.4 assistantdesi@gmail.com
#
# Notes:
# - This script does NOT start the tunnel for you (per your request).
# - It prints the exact tunnel command, waits for you to confirm, then SSHes into the VM
#   to run the reauth workflow.

VM_SSH=${1:-}
ACCOUNT=${2:-}
PORT=${PORT:-18793}

if [[ -z "$VM_SSH" || -z "$ACCOUNT" ]]; then
  echo "Usage: $0 <ssh_target> <gmail_account>" >&2
  echo "Example: $0 desazure@<vm-ip> assistantdesi@gmail.com" >&2
  exit 2
fi

TUNNEL_CMD="ssh -N -L ${PORT}:127.0.0.1:${PORT} ${VM_SSH}"

cat <<EOF

Step 1 (run on your laptop in a separate terminal):

  $TUNNEL_CMD

Leave it running.

Step 2: After the tunnel is up, come back here.
EOF

echo ""
read -r -p "Tunnel running? Type Y to continue (anything else to abort): " ans
if [[ ! "$ans" =~ ^[Yy]$ ]]; then
  echo "Aborted. Start the tunnel, then re-run." >&2
  exit 1
fi

echo ""
echo "Starting VM reauth workflow..."

echo ""
echo "(You will get a Google URL. Open it in your laptop browser and approve.)"

echo ""
ssh -t "$VM_SSH" \
  "bash /home/desazure/.openclaw/workspace/ops/google-auth/google_reauth.sh '$ACCOUNT' interactive"
