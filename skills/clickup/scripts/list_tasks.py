#!/usr/bin/env python3

import argparse
import json
from datetime import datetime, timezone

from clickup import load_token, client, api_get


def main():
    ap = argparse.ArgumentParser(description="List ClickUp tasks from a list.")
    ap.add_argument("--list-id", required=True)
    ap.add_argument("--include-closed", action="store_true")
    ap.add_argument("--due-after-ms", type=int, default=None)
    ap.add_argument("--due-before-ms", type=int, default=None)
    ap.add_argument("--token-file", default=None)
    ap.add_argument("--limit", type=int, default=50)
    args = ap.parse_args()

    token = load_token(args.token_file)
    s = client(token)

    params = {
        "archived": "false",
        "include_closed": str(args.include_closed).lower(),
        "page": 0,
        "order_by": "due_date",
        "reverse": "false",
        "subtasks": "true",
    }
    if args.due_after_ms is not None:
        params["due_date_gt"] = args.due_after_ms
    if args.due_before_ms is not None:
        params["due_date_lt"] = args.due_before_ms

    data = api_get(s, f"/list/{args.list_id}/task", params=params)
    tasks = data.get("tasks", [])[: args.limit]

    def simplify(t):
        return {
            "id": t.get("id"),
            "name": t.get("name"),
            "url": t.get("url"),
            "status": (t.get("status") or {}).get("status"),
            "due_date": t.get("due_date"),
            "priority": (t.get("priority") or {}).get("priority"),
        }

    print(json.dumps([simplify(t) for t in tasks], indent=2))


if __name__ == "__main__":
    main()
