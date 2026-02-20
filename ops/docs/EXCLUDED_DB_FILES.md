# Files Excluded from Git Backup

This document lists database files, large mutable data files, and secrets that are **excluded** from the Git backup.

## Excluded Files

- **Database Files**: SQLite `.db` or `.sqlite` files that store runtime state
- **Log Files**: Large JSONL or log files under `logs/` or similar directories
- **Token Caches & Secrets**: OAuth tokens, API keys, and other secret material stored in local config folders
- **Temporary or Build Artifacts**: Any generated files or temp data

## Management

- These files are backed up separately or managed via secure vaults/encrypted storage where applicable.
- Ensure `.gitignore` excludes these file patterns:
  ```
  *.db
  *.sqlite
  logs/
  *.token.json
  *.cache/
  *.jsonl
  ```

## Purpose

To keep the Git repository clean, reduce risk of committing secrets, and avoid bloating version control with large files.

---
