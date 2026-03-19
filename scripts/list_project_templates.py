#!/usr/bin/env python3

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


API_BASE_URL = "https://app.asana.com/api/1.0"


def load_dotenv(env_path: Path) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def asana_get(path: str, token: str, params: dict[str, str] | None = None) -> dict:
    query = ""
    if params:
        query = "?" + urllib.parse.urlencode(params)

    request = urllib.request.Request(
        f"{API_BASE_URL}{path}{query}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Asana API request failed with HTTP {exc.code} for {path}: {body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Unable to reach Asana API: {exc.reason}") from exc


def paginate(path: str, token: str, params: dict[str, str] | None = None) -> list[dict]:
    merged_params = dict(params or {})
    merged_params.setdefault("limit", "100")

    items: list[dict] = []
    offset = None

    while True:
        page_params = dict(merged_params)
        if offset:
            page_params["offset"] = offset

        payload = asana_get(path, token, page_params)
        items.extend(payload.get("data", []))

        next_page = payload.get("next_page")
        if not next_page or not next_page.get("offset"):
            break

        offset = next_page["offset"]

    return items


def choose_workspace(workspaces: list[dict]) -> str:
    if not workspaces:
        raise RuntimeError("No workspaces are available for the configured Asana token.")

    if len(workspaces) == 1:
        workspace = workspaces[0]
        print(
            f"Using workspace {workspace['name']} ({workspace['gid']})",
            file=sys.stderr,
        )
        return workspace["gid"]

    if not sys.stdin.isatty():
        names = ", ".join(
            f"{workspace['name']} ({workspace['gid']})" for workspace in workspaces
        )
        raise RuntimeError(
            "Multiple workspaces are available. Pass --workspace-gid or set "
            f"ASANA_WORKSPACE_GID. Available: {names}"
        )

    print("Available workspaces:", file=sys.stderr)
    for index, workspace in enumerate(workspaces, start=1):
        print(
            f"{index}. {workspace['name']} ({workspace['gid']})",
            file=sys.stderr,
        )

    while True:
        choice = input("Choose a workspace number: ").strip()
        if not choice.isdigit():
            print("Enter a valid number.", file=sys.stderr)
            continue

        selected_index = int(choice) - 1
        if 0 <= selected_index < len(workspaces):
            return workspaces[selected_index]["gid"]

        print("Choice out of range.", file=sys.stderr)


def resolve_workspace_gid(token: str, cli_workspace_gid: str | None) -> str:
    if cli_workspace_gid:
        return cli_workspace_gid

    env_workspace_gid = os.environ.get("ASANA_WORKSPACE_GID")
    if env_workspace_gid:
        return env_workspace_gid

    workspaces = paginate("/workspaces", token)
    return choose_workspace(workspaces)


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

    token = os.environ.get("ASANA_ACCESS_TOKEN")
    if not token:
        parser.error("ASANA_ACCESS_TOKEN is required in the environment or .env file.")

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
