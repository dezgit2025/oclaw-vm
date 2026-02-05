---
name: clickup
description: Create and list ClickUp tasks from chat using the ClickUp REST API (v2). Use when the user wants to create tasks, list tasks due today/this week, or set up a default Space/List destination.
---

# ClickUp (REST API)

This skill uses a Personal API Token stored locally on the host.

## Store token

Create `~/.config/openclaw-clickup/token` containing the token.

## Setup default destination

Use `scripts/setup_default.py` to find or create the Space + List.

## Create a task

Use `scripts/create_task.py` with `--list-id`.

## List tasks

Use `scripts/list_tasks.py` to query tasks with filters (due date, etc.).
