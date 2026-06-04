#!/usr/bin/env python3
"""
get-softr-database
==================
Export a full Softr Tables database **schema** (every table, every field, and all
of their details) to a timestamped JSON file on your Desktop.

What it does
------------
Given a Softr API key and a database ID, it calls two endpoints:

    GET /api/v1/databases/{id}           -> database metadata
    GET /api/v1/databases/{id}/tables    -> all tables, each with its full
                                            `fields` array (type, options,
                                            choices, formulas, AI settings, ...)

and writes the combined result to:

    ~/Desktop/softr-database-<databaseId>-<YYYYMMDD-HHMMSS>.json

Usage
-----
    get-softr-database                      # prompts for DB ID, then API key (hidden)
    get-softr-database <database_id>        # prompts only for the API key
    SOFTR_API_KEY=xxx get-softr-database <database_id>   # fully non-interactive

The API key may also be supplied via the SOFTR_API_KEY environment variable, so
it never has to be typed (or stored) in plain text.

Only the Python standard library is used — no `pip install` required.
"""

import os
import sys
import json
import getpass
import datetime
import urllib.request
import urllib.error

API_BASE = "https://tables-api.softr.io/api/v1"
TIMEOUT_SECONDS = 60


def api_get(path, api_key):
    """GET a Softr Tables API path and return the parsed JSON body."""
    req = urllib.request.Request(
        API_BASE + path,
        headers={
            "Softr-Api-Key": api_key,
            "Content-Type": "application/json",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        hint = ""
        if e.code in (401, 403):
            hint = "\n  (Check that the API key is correct and has access to this database.)"
        elif e.code == 404:
            hint = "\n  (Check that the database ID is correct.)"
        raise SystemExit(f"\n[x] HTTP {e.code} on GET {path}\n  {body}{hint}")
    except urllib.error.URLError as e:
        raise SystemExit(f"\n[x] Network error on GET {path}: {e.reason}")
    except json.JSONDecodeError:
        raise SystemExit(f"\n[x] Could not parse JSON response from GET {path}")


def prompt_database_id():
    if len(sys.argv) > 1 and sys.argv[1].strip():
        return sys.argv[1].strip()
    try:
        value = input("Softr database ID: ").strip()
    except (EOFError, KeyboardInterrupt):
        raise SystemExit("\n[x] Cancelled.")
    if not value:
        raise SystemExit("[x] No database ID provided.")
    return value


def prompt_api_key():
    value = os.environ.get("SOFTR_API_KEY", "").strip()
    if value:
        return value
    try:
        value = getpass.getpass("Softr API key (input hidden): ").strip()
    except (EOFError, KeyboardInterrupt):
        raise SystemExit("\n[x] Cancelled.")
    if not value:
        raise SystemExit("[x] No API key provided.")
    return value


def output_dir():
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    return desktop if os.path.isdir(desktop) else os.path.expanduser("~")


def main():
    database_id = prompt_database_id()
    api_key = prompt_api_key()

    print(f"\n-> Fetching database {database_id} ...")
    db = api_get(f"/databases/{database_id}", api_key).get("data", {}) or {}
    print(f"   Database: {db.get('name', '(unknown)')}  "
          f"({db.get('tablesCount', '?')} tables reported)")

    print("-> Fetching tables and fields ...")
    tables = api_get(f"/databases/{database_id}/tables", api_key).get("data", []) or []
    total_fields = sum(len(t.get("fields", []) or []) for t in tables)
    print(f"   Retrieved {len(tables)} tables, {total_fields} fields total.")

    now = datetime.datetime.now()
    payload = {
        "exportedAt": now.isoformat(timespec="seconds"),
        "source": API_BASE,
        "databaseId": database_id,
        "database": db,
        "tableCount": len(tables),
        "fieldCount": total_fields,
        "tables": tables,
    }

    stamp = now.strftime("%Y%m%d-%H%M%S")
    filename = f"softr-database-{database_id}-{stamp}.json"
    path = os.path.join(output_dir(), filename)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\n[ok] Saved schema to:\n     {path}")

    # Brief per-table summary so the result is readable at a glance.
    if tables:
        print("\n     Tables:")
        for t in tables:
            print(f"       - {t.get('name', '(unnamed)')}: "
                  f"{len(t.get('fields', []) or [])} fields")


if __name__ == "__main__":
    main()
