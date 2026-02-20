#!/usr/bin/env python3

import argparse
import json

from _gdrive import ALLOWED_FOLDER_ID, build_drive


def main():
    ap = argparse.ArgumentParser(description="Create a Google Doc inside the OpenClawShared folder.")
    ap.add_argument("--token", required=True, help="Path to Drive token JSON")
    ap.add_argument("--title", required=True)
    args = ap.parse_args()

    svc = build_drive(args.token).service

    body = {
        "name": args.title,
        "mimeType": "application/vnd.google-apps.document",
        "parents": [ALLOWED_FOLDER_ID],
    }

    created = svc.files().create(body=body, fields="id, webViewLink").execute()
    print(json.dumps({"docId": created.get("id"), "url": created.get("webViewLink")}, indent=2))


if __name__ == "__main__":
    main()
