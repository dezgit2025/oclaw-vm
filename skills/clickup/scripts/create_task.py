#!/usr/bin/env python3

import argparse
import json

from clickup import load_token, client, api_post


def main():
    ap = argparse.ArgumentParser(description="Create a ClickUp task in a list.")
    ap.add_argument("--list-id", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--description", default="")
    ap.add_argument("--due-ms", type=int, default=None, help="Due date in epoch milliseconds")
    ap.add_argument("--due-date-time", action="store_true", help="Treat due-ms as an exact date+time (sets due_date_time=true)")
    ap.add_argument("--priority", type=int, default=None, help="1 urgent, 2 high, 3 normal, 4 low")
    ap.add_argument("--tags", default="", help="Comma-separated tags")
    ap.add_argument("--token-file", default=None)
    args = ap.parse_args()

    token = load_token(args.token_file)
    s = client(token)

    body = {
        "name": args.name,
        "description": args.description,
    }
    if args.due_ms is not None:
        body["due_date"] = args.due_ms
        if args.due_date_time:
            body["due_date_time"] = True
    if args.priority is not None:
        body["priority"] = args.priority
    if args.tags:
        body["tags"] = [t.strip() for t in args.tags.split(",") if t.strip()]

    out = api_post(s, f"/list/{args.list_id}/task", body)
    print(json.dumps({"id": out.get("id"), "url": out.get("url"), "name": out.get("name")}, indent=2))


if __name__ == "__main__":
    main()
