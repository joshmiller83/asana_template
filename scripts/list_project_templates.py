#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path

from asana_utils import load_dotenv, paginate, require_access_token, resolve_workspace_gid


def list_project_templates(token: str, workspace_gid: str) -> list[dict]:
    # Asana exposes project templates via GET /project_templates scoped by workspace.
    return paginate(
        "/project_templates",
        token,
        {
            "workspace": workspace_gid,
            "opt_fields": "gid,name,team.name,owner.name,created_at",
        },
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List project templates visible in an Asana workspace."
    )
    parser.add_argument(
        "--workspace-gid",
        help="Workspace GID. Defaults to ASANA_WORKSPACE_GID or interactive selection.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON instead of a text table.",
    )
    return parser


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(repo_root / ".env")

    parser = build_parser()
    args = parser.parse_args()

    try:
        token = require_access_token()
    except RuntimeError as exc:
        parser.error(str(exc))

    try:
        workspace_gid = resolve_workspace_gid(token, args.workspace_gid)
        templates = list_project_templates(token, workspace_gid)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(templates, indent=2))
        return 0

    if not templates:
        print(f"No project templates found for workspace {workspace_gid}.")
        return 0

    for template in templates:
        team_name = (template.get("team") or {}).get("name", "-")
        owner_name = (template.get("owner") or {}).get("name", "-")
        created_at = template.get("created_at", "-")
        print(
            f"{template['gid']}\t{template['name']}\tteam={team_name}\towner={owner_name}\tcreated_at={created_at}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
