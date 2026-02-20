#!/usr/bin/env python3

import argparse

from _common import assert_in_allowed_folder, build_services


def main():
    ap = argparse.ArgumentParser(description="Append plain text to a Google Doc (restricted to OpenClawShared folder).")
    ap.add_argument("--token", required=True)
    ap.add_argument("--doc-id", required=True)
    ap.add_argument("--text", required=True)
    args = ap.parse_args()

    drive, docs = build_services(args.token)
    assert_in_allowed_folder(drive, args.doc_id)

    # Docs API: insertText at end of document. endIndex is in the last structural element.
    doc = docs.documents().get(documentId=args.doc_id).execute()
    content = (doc.get("body") or {}).get("content") or []
    end_index = None
    for el in reversed(content):
        if "endIndex" in el:
            end_index = el["endIndex"]
            break
    if end_index is None:
        raise SystemExit("Could not determine document endIndex")

    # Insert before final newline position (Docs usually ends with a newline).
    insert_at = max(1, int(end_index) - 1)

    requests = [
        {
            "insertText": {
                "location": {"index": insert_at},
                "text": "\n" + args.text + "\n",
            }
        }
    ]

    res = docs.documents().batchUpdate(documentId=args.doc_id, body={"requests": requests}).execute()
    print("OK: appended")


if __name__ == "__main__":
    main()
