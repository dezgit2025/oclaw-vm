#!/usr/bin/env python3
"""Encrypted backup of recent workspace files to Google Drive.

Uses the .venv-gmail venv for Google API libs.
Shebang: run with ~/.openclaw/workspace/.venv-gmail/bin/python3
"""
import subprocess
import tarfile
import tempfile
import os
import datetime
import sys
from pathlib import Path
from base64 import b64decode

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# ── Config ──────────────────────────────────────────────────────────────
BACKUP_ROOT = Path('/home/desazure/.openclaw/workspace')
ENCRYPTION_KEY_FILE = Path('/home/desazure/.secrets/openclaw_backup_key.gpg')
GDRIVE_TOKEN = Path('/home/desazure/.config/openclaw-gdrive/token-openclawshared.json')
GDRIVE_FOLDER_NAME = 'clawbot-backup'
BACKUP_LOG = Path('/home/desazure/.openclaw/workspace/ops/scripts/backup-log.md')
DAYS_TO_BACKUP = 14
RETENTION_DAYS = 14


def log(msg):
    print(msg)


def find_recent_files(root: Path, days: int):
    """Find files modified in last N days under root."""
    cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
    files = []
    for p in root.rglob('*'):
        if p.is_file() and datetime.datetime.fromtimestamp(p.stat().st_mtime) >= cutoff:
            # Skip .venv dirs, __pycache__, .git, node_modules
            parts = p.relative_to(root).parts
            if any(part.startswith('.venv') or part in ('__pycache__', '.git', 'node_modules') for part in parts):
                continue
            files.append(p)
    return files


def create_archive(files, output_path):
    """Archive files to .tar.gz."""
    with tarfile.open(output_path, 'w:gz') as tar:
        for f in files:
            try:
                tar.add(f, arcname=f.relative_to(BACKUP_ROOT))
            except Exception as e:
                log(f'Warning: failed adding {f}: {e}')


def read_key():
    """Read the base64 encryption key (stored as plaintext, not GPG-encrypted)."""
    key_b64 = ENCRYPTION_KEY_FILE.read_text().strip()
    key_bytes = b64decode(key_b64)
    return key_bytes.hex()


def encrypt_archive(input_file, output_file, key_hex):
    """Encrypt archive using AES-256-CBC with random IV via openssl."""
    cmd = [
        'openssl', 'enc', '-aes-256-cbc', '-salt', '-pbkdf2',
        '-in', str(input_file),
        '-out', str(output_file),
        '-pass', f'pass:{key_hex}',
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f'Encryption failed: {result.stderr}')


def get_drive_service():
    """Build Google Drive API service from saved token."""
    if not GDRIVE_TOKEN.exists():
        raise RuntimeError(f'Token not found: {GDRIVE_TOKEN}')
    creds = Credentials.from_authorized_user_file(str(GDRIVE_TOKEN))
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
        else:
            raise RuntimeError('Google Drive credentials invalid and cannot refresh')
    return build('drive', 'v3', credentials=creds)


def find_or_create_folder(service, folder_path):
    """Find or create nested folder path (e.g. 'clawbot-backup').
    Returns the folder ID."""
    parent_id = 'root'
    for part in folder_path.split('/'):
        query = (f"name='{part}' and mimeType='application/vnd.google-apps.folder' "
                 f"and '{parent_id}' in parents and trashed=false")
        resp = service.files().list(q=query, spaces='drive', fields='files(id)').execute()
        files = resp.get('files', [])
        if files:
            parent_id = files[0]['id']
        else:
            meta = {'name': part, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]}
            folder = service.files().create(body=meta, fields='id').execute()
            parent_id = folder['id']
            log(f'Created Drive folder: {part}')
    return parent_id


def upload_to_gdrive(service, filepath, folder_id):
    """Upload file to a Google Drive folder."""
    name = os.path.basename(filepath)
    meta = {'name': name, 'parents': [folder_id]}
    media = MediaFileUpload(filepath, resumable=True)
    f = service.files().create(body=meta, media_body=media, fields='id,name,size').execute()
    log(f"Uploaded: {f['name']} (id={f['id']})")
    return f['id']


def cleanup_old_backups(service, folder_id, days):
    """Delete backup files older than N days from the Drive folder."""
    cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=days)
    cutoff_str = cutoff.strftime('%Y-%m-%dT%H:%M:%S')
    query = (f"'{folder_id}' in parents and trashed=false "
             f"and createdTime < '{cutoff_str}'")
    resp = service.files().list(q=query, spaces='drive', fields='files(id,name,createdTime)').execute()
    deleted = 0
    for f in resp.get('files', []):
        service.files().delete(fileId=f['id']).execute()
        log(f"Deleted old backup: {f['name']} (created {f['createdTime']})")
        deleted += 1
    return deleted


def write_backup_log(timestamp, file_count, archive_size, encrypted_size, drive_file_id, deleted_count, duration_s):
    """Append entry to backup-log.md."""
    BACKUP_LOG.parent.mkdir(parents=True, exist_ok=True)

    # Create header if file doesn't exist
    if not BACKUP_LOG.exists():
        BACKUP_LOG.write_text('# Backup Log\n\n'
                              '| Timestamp | Files | Archive | Encrypted | Drive ID | Old Deleted | Duration |\n'
                              '|-----------|-------|---------|-----------|----------|-------------|----------|\n')

    size_fmt = lambda b: f'{b/1024:.1f} KB' if b < 1048576 else f'{b/1048576:.1f} MB'
    line = (f'| {timestamp} | {file_count} | {size_fmt(archive_size)} | {size_fmt(encrypted_size)} '
            f'| {drive_file_id} | {deleted_count} | {duration_s:.1f}s |\n')

    with open(BACKUP_LOG, 'a') as f:
        f.write(line)


def main():
    start = datetime.datetime.now(datetime.UTC)
    timestamp = start.strftime('%Y%m%dT%H%M%SZ')

    log(f'=== Backup started: {timestamp} ===')

    # 1. Find files
    files_to_backup = find_recent_files(BACKUP_ROOT, DAYS_TO_BACKUP)
    log(f'Found {len(files_to_backup)} files modified in last {DAYS_TO_BACKUP} days')

    if not files_to_backup:
        log('No files to backup. Done.')
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = os.path.join(tmpdir, f'oclaw_backup_{timestamp}.tar.gz')
        encrypted_path = os.path.join(tmpdir, f'oclaw_backup_{timestamp}.enc')

        # 2. Create archive
        create_archive(files_to_backup, archive_path)
        archive_size = os.path.getsize(archive_path)
        log(f'Archive: {archive_size} bytes')

        # 3. Read key and encrypt
        key_hex = read_key()
        encrypt_archive(archive_path, encrypted_path, key_hex)
        encrypted_size = os.path.getsize(encrypted_path)
        log(f'Encrypted: {encrypted_size} bytes')

        # 4. Upload to Drive
        service = get_drive_service()
        folder_id = find_or_create_folder(service, GDRIVE_FOLDER_NAME)
        drive_file_id = upload_to_gdrive(service, encrypted_path, folder_id)

        # 5. Cleanup old backups
        deleted = cleanup_old_backups(service, folder_id, RETENTION_DAYS)

    duration = (datetime.datetime.now(datetime.UTC) - start).total_seconds()
    log(f'=== Backup completed in {duration:.1f}s ===')

    # 6. Log to backup-log.md
    write_backup_log(timestamp, len(files_to_backup), archive_size, encrypted_size, drive_file_id, deleted, duration)
    log(f'Logged to {BACKUP_LOG}')


if __name__ == '__main__':
    main()
