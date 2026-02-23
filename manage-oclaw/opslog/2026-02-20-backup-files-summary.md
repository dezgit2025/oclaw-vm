# Backup Files and Documentation Summary

**Date:** 2026-02-20

## File Locations (on VM `oclaw2026linux`)

| Item | Path | Description |
|------|------|-------------|
| Backup Script | `~/.openclaw/workspace/ops/scripts/encrypted_backup_to_drive.py` | Python script to archive, encrypt, and upload backups |
| Backup Log | `~/.openclaw/workspace/ops/scripts/backup-log.md` | Markdown log of each backup run with stats |
| Backup Docs | `~/.openclaw/workspace/ops/docs/BACKUP_SCRIPTS.md` | Documentation for the backup script and log |
| Encryption Key | `~/.secrets/openclaw_backup_key.gpg` | Base64 AES-256 key (chmod 600) |
| GDrive Token | `~/.config/openclaw-gdrive/token-openclawshared.json` | Google Drive OAuth token |

## Directory Structure

```
~/.openclaw/workspace/ops/
├── scripts/
│   ├── encrypted_backup_to_drive.py
│   └── backup-log.md
└── docs/
    └── BACKUP_SCRIPTS.md
```

## Run Command

```bash
~/.openclaw/workspace/.venv-gmail/bin/python3 ~/.openclaw/workspace/ops/scripts/encrypted_backup_to_drive.py
```

## BACKUP_SCRIPTS.md (copy from VM)

### Backup Script
- Path: `~/.openclaw/workspace/ops/scripts/encrypted_backup_to_drive.py`
- Description: This script creates compressed archives of files changed in the last 14 days, encrypts the archive using AES-256, and uploads it to Google Drive in a timestamped folder.

### Backup Log
- Path: `~/.openclaw/workspace/ops/scripts/backup-log.md`
- Description: Markdown log recording details of each backup operation including file counts, archive sizes, backup duration, and Google Drive file IDs.

These files are part of the automated backup workflow for the OpenClaw workspace.

## Related

- [2026-02-20-backup-key-stored-on-vm.md](2026-02-20-backup-key-stored-on-vm.md) — Key storage
- [2026-02-20-fix-encrypted-backup-script.md](2026-02-20-fix-encrypted-backup-script.md) — Script debug/fix details
