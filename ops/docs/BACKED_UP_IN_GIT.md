# Files Included in Git Backup

This document lists the files and folders included in the version-controlled Git repository backup of the OpenClaw workspace.

## Included

- **Skills**: All skill code, scripts, and local documentation under `skills/`
- **Operational Tools**: Glue scripts, monitoring tools, reports under `ops/scripts/`
- **Documentation**: All markdown docs, guides, policies under `ops/docs/` and general `docs/` folder
- **Config**: Global or cross-skill configurations in `config/`
- **Memory**: Daily notes and durable memory logs under `memory/`
- **Workspace Root Files**: Versioned files at the root level like `GLOBAL_FOLDER_STRUCTURE.md`, `README.md`, etc.

## Purpose

Ensures all necessary code and documentation to maintain and operate OpenClaw are version-controlled and backed up.

# Guidelines

- Avoid committing large binaries, logs, or runtime data.
- Keep secrets and tokens out of Git.

---
