# Stored openclaw backup key on VM

**Date:** 2026-02-20
**Severity:** Routine
**Affected resource:** `oclaw2026linux`

## What

Stored the openclaw backup encryption key on the VM in a secure location.

## Details

| Item | Value |
|------|-------|
| Path | `/home/desazure/.secrets/openclaw_backup_key.gpg` |
| Directory | `/home/desazure/.secrets/` |
| Dir permissions | `700` (owner only) |
| File permissions | `600` (owner read/write only) |
| Owner | `desazure:desazure` |

## Steps Performed

1. Created `~/.secrets/` directory with `chmod 700`
2. Wrote key to `~/.secrets/openclaw_backup_key.gpg`
3. Set file permissions to `chmod 600`
4. Verified permissions and contents
