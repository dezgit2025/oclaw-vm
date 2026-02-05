#!/usr/bin/env python3

import argparse
from typing import Optional

from clickup import load_token, client, api_get, api_post


def find_space(team_id: str, space_name: str, s) -> Optional[dict]:
    data = api_get(s, f"/team/{team_id}/space")
    for sp in data.get("spaces", []):
        if sp.get("name") == space_name:
            return sp
    return None


def get_folderless_lists(space_id: str, s) -> list[dict]:
    data = api_get(s, f"/space/{space_id}/list")
    return data.get("lists", [])


def find_folderless_list(space_id: str, list_name: str, s) -> Optional[dict]:
    for lst in get_folderless_lists(space_id, s):
        if lst.get("name") == list_name:
            return lst
    return None


def main():
    ap = argparse.ArgumentParser(description="Find or create default ClickUp Space + List.")
    ap.add_argument("--space", required=True, help="Space name")
    ap.add_argument("--list", required=True, help="List name")
    ap.add_argument("--create-space", action="store_true", help="Create the space if missing")
    ap.add_argument("--create-list", action="store_true", help="Create the list if missing")
    ap.add_argument("--token-file", default=None)
    args = ap.parse_args()

    token = load_token(args.token_file)
    s = client(token)

    teams = api_get(s, "/team").get("teams", [])
    if not teams:
        raise SystemExit("No ClickUp workspaces/teams found for this token")

    # choose first team by default
    team = teams[0]
    team_id = team["id"]

    space = find_space(team_id, args.space, s)
    if not space:
        if not args.create_space:
            raise SystemExit(f"Space '{args.space}' not found. Re-run with --create-space")
        space = api_post(
            s,
            f"/team/{team_id}/space",
            {
                "name": args.space,
                "multiple_assignees": True,
                "features": {
                    "due_dates": {"enabled": True, "start_date": False, "remap_due_dates": True, "remap_closed_due_date": False},
                    "time_tracking": {"enabled": True},
                    "tags": {"enabled": True},
                    "time_estimates": {"enabled": True},
                    "checklists": {"enabled": True},
                    "custom_fields": {"enabled": True},
                    "remap_dependencies": {"enabled": True},
                    "dependency_warning": {"enabled": True},
                    "portfolios": {"enabled": False},
                },
            },
        )

    space_id = space["id"]

    lst = find_folderless_list(space_id, args.list, s)
    if not lst:
        # Many workspaces always create a default folderless list named "List" in a hidden folder.
        # Creating new lists can be permission-gated, so prefer renaming an existing folderless list.
        existing = get_folderless_lists(space_id, s)
        if existing:
            candidate = existing[0]
            # rename via PUT /list/{list_id}
            import requests
            r = s.put(
                f"https://api.clickup.com/api/v2/list/{candidate['id']}",
                json={"name": args.list},
                timeout=30,
            )
            r.raise_for_status()
            lst = r.json()
        else:
            if not args.create_list:
                raise SystemExit(
                    f"No folderless lists found in space '{args.space}'. Re-run with --create-list to attempt list creation."
                )
            lst = api_post(
                s,
                f"/space/{space_id}/list",
                {
                    "name": args.list,
                    "content": "Tasks created by OpenClaw",
                    "due_dates": True,
                    "priority": True,
                    "assignee": True,
                },
            )

    print(f"OK team={team.get('name')} teamId={team_id}")
    print(f"OK spaceName={args.space} spaceId={space_id}")
    print(f"OK listName={args.list} listId={lst['id']}")


if __name__ == "__main__":
    main()
