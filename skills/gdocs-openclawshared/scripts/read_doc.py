#!/usr/bin/env python3

import argparse

from _common import assert_in_allowed_folder, build_services


def doc_to_text(doc: dict) -> str:
    out = []
    body = (doc.get("body") or {}).get("content") or []
    for el in body:
        para = el.get("paragraph")
        if not para:
            continue
        for pe in para.get("elements") or []:
            tr = (pe.get("textRun") or {}).get("content")
            if tr:
                out.append(tr)
    return "".join(out)


def main():
    ap = argparse.ArgumentParser(description="Read a Google Doc (restricted to OpenClawShared folder).")
    ap.add_argument("--token", required=True)
    ap.add_argument("--doc-id", required=True)
    args = ap.parse_args()

    drive, docs = build_services(args.token)
    assert_in_allowed_folder(drive, args.doc_id)

    doc = docs.documents().get(documentId=args.doc_id).execute()
    text = doc_to_text(doc)
    print(text)


if __name__ == "__main__":
    main()
