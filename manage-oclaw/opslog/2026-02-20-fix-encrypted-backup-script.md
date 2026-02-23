# Fix: encrypted_backup_to_drive.py debugged and first successful run

**Date:** 2026-02-20
**Severity:** Routine
**Affected resource:** `oclaw2026linux`

## Script

`/home/desazure/.openclaw/workspace/ops/scripts/encrypted_backup_to_drive.py`

**Run with:** `~/.openclaw/workspace/.venv-gmail/bin/python3` (has google-api-python-client, google-auth)

## Bugs Fixed

| Bug | Fix |
|-----|-----|
| `decrypt_key()` called `gpg --decrypt` on plaintext base64 key | Read file directly, base64-decode |
| Token path `~/.credentials/token.json` (doesn't exist) | Changed to `~/.config/openclaw-gdrive/token-openclawshared.json` |
| GDrive folder name appended timestamp each run | Static folder `clawbot-backup`, timestamp only on file |
| Cleanup query used folder name string as parent ID | Uses actual folder ID from `find_or_create_folder()` |
| `openssl` used static zero IV | Changed to `-pbkdf2` with `-pass` (openssl handles salt/IV) |
| No token refresh logic | Added `creds.refresh()` fallback |
| Backed up `.venv`, `node_modules`, `.git` dirs | Added exclusion filters |
| No logging | Added `backup-log.md` — appends table row per run |
| `datetime.utcnow()` deprecation | Changed to `datetime.now(datetime.UTC)` |

## First Run Result

| Metric | Value |
|--------|-------|
| Files backed up | 193 |
| Archive size | 4.9 MB |
| Encrypted size | 4.9 MB |
| Drive folder | `clawbot-backup` |
| Drive file ID | `1ROX8uEuvjAiZWUsFUwKkHizLyuenyteQ` |
| Duration | 5.2s |

## Config

| Setting | Value |
|---------|-------|
| Backup root | `/home/desazure/.openclaw/workspace` |
| Encryption key | `/home/desazure/.secrets/openclaw_backup_key.gpg` (base64, not GPG-encrypted) |
| GDrive token | `~/.config/openclaw-gdrive/token-openclawshared.json` |
| Drive folder | `clawbot-backup` |
| Backup log | `~/.openclaw/workspace/ops/scripts/backup-log.md` |
| Files included | Modified in last 14 days |
| Retention | 14 days (old backups auto-deleted from Drive) |
| Excluded | `.venv*`, `__pycache__`, `.git`, `node_modules` |

## Related

- Encryption key stored: [2026-02-20-backup-key-stored-on-vm.md](2026-02-20-backup-key-stored-on-vm.md)
