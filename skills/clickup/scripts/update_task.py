#!/usr/bin/env python3

import argparse
import json

from clickup import load_token, client


def main():
    ap = argparse.ArgumentParser(description="Update a ClickUp task (limited fields).")
    ap.add_argument("--task-id", required=True)
    ap.add_argument("--due-ms", type=int, default=None)
    ap.add_argument("--priority", type=int, default=None)
    ap.add_argument("--token-file", default=None)
    args = ap.parse_args()

    token = load_token(args.token_file)
    s = client(token)

    body = {}
    if args.due_ms is not None:
        body["due_date"] = args.due_ms
        body["due_date_time"] = True
    if args.priority is not None:
        body["priority"] = args.priority

    if not body:
        raise SystemExit("Nothing to update (pass --due-ms and/or --priority)")

    url = f"https://api.clickup.com/api/v2/task/{args.task_id}"
    r = s.put(url, data=json.dumps(body), timeout=30)
    r.raise_for_status()

    out = r.json()
    print(json.dumps({"id": out.get("id"), "url": out.get("url"), "due_date": out.get("due_date")}, indent=2))


if __name__ == "__main__":
    main()
