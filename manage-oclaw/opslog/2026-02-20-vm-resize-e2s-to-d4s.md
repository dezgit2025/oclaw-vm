# VM Resize: Standard_E2s_v3 → Standard_D4s_v3

**Date:** 2026-02-20
**Severity:** Planned change
**Affected resource:** `oclaw2026linux` in `RG_OCLAW2026` (East US 2)

## Reason

Gateway process was consuming high CPU on 2-vCPU VM. Upgraded to 4 vCPU for ~20% more headroom.

## Change

| | Before | After |
|---|---|---|
| **SKU** | Standard_E2s_v3 | Standard_D4s_v3 |
| **vCPU** | 2 | 4 |
| **RAM** | 16 GiB | 16 GiB |
| **Series** | Memory-optimized (Ev3) | General-purpose (Dv3) |
| **Region** | East US 2 | East US 2 (unchanged) |

## SKU Selection

First choice was `Standard_D4as_v5` (AMD, v5 gen). Multiple SKUs were capacity-constrained in East US 2 at time of resize:

| SKU Attempted | Result |
|---------------|--------|
| Standard_D4as_v5 | `SkuNotAvailable` — capacity restriction |
| Standard_D4as_v4 | `SkuNotAvailable` — capacity restriction |
| Standard_D4s_v5 | `SkuNotAvailable` — capacity restriction |
| **Standard_D4s_v3** | **Succeeded** |

## Steps Performed

1. `az vm deallocate --name oclaw2026linux --resource-group RG_OCLAW2026`
2. `az vm resize --name oclaw2026linux --resource-group RG_OCLAW2026 --size Standard_D4s_v3` — succeeded
3. `az vm start --name oclaw2026linux --resource-group RG_OCLAW2026`
4. `check-setup-nsg-for-oclaw-ssh.py` — NSG rules re-created (cleared on deallocation)
5. `create-manage-tunnel-oclaw.py start` — tunnel reconnected
6. Verified: `nproc` = 4, `free -h` = 15 GiB available, gateway active with telegram provider running

## Post-Resize Verification

- VM: running, 4 cores, 15 GiB available
- NSG: re-applied to both subnet + VM NSGs
- SSH tunnel: up (ports 18792–18797)
- Gateway: `active (running)`, telegram provider started, no errors

## Notes

- Deallocation clears NSG rules — always re-run `check-setup-nsg-for-oclaw-ssh.py` after resize/restart
- If v5 SKUs become available later, consider re-sizing to `Standard_D4as_v5` for better perf/cost
- No config changes were needed — only the VM SKU changed
