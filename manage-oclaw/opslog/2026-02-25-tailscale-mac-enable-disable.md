# Tailscale Mac Enable/Disable Procedure

**Date:** 2026-02-25
**Issue:** Tailscale interfered with MS Azure VPN client, required disable + reboot. Re-enabling needed specific steps.

## Problem

Tailscale and MS Azure VPN client conflict on Mac. Running both simultaneously causes connectivity issues. Had to disable Tailscale and reboot to restore Azure VPN.

## How to Disable Tailscale (Mac)

```bash
tailscale down
```

Or: Click Tailscale menu bar icon → Disconnect.

## How to Re-Enable Tailscale (Mac)

**Both steps are required:**

1. **Open Tailscale app** — System Settings → VPN → enable Tailscale toggle (or open the app from Applications/Spotlight)
2. **Run CLI command:**
   ```bash
   tailscale up
   ```

The GUI toggle alone starts the system extension but does NOT establish the tunnel. `tailscale up` is required to actually connect.

## Post-Reboot Gotcha

After a reboot, the Tailscale CLI may fail with:

```
The Tailscale CLI failed to start: Failed to load preferences.
```

**Fix:** Open the Tailscale app first (GUI), enable the VPN toggle in System Settings, THEN run `tailscale up`.

## Verification

```bash
# Check Tailscale is connected and shows all nodes
tailscale status

# Test SSH to oclaw
ssh oclaw "hostname"
```

## Key Lesson

- `tailscale down` / `tailscale up` are the disable/enable commands
- After reboot, the app must be opened before CLI works
- Azure VPN and Tailscale conflict — disable one before using the other
