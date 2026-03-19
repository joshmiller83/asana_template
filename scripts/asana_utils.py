import json
import os
import re
import sys
import time
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


def require_access_token() -> str:
    token = os.environ.get("ASANA_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("ASANA_ACCESS_TOKEN is required in the environment or .env file.")
    return token


def asana_request(
    method: str,
    path: str,
    token: str,
    params: dict[str, str] | None = None,
    data: dict | None = None,
) -> dict:
    query = ""
    if params:
        query = "?" + urllib.parse.urlencode(params)

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    payload = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        payload = json.dumps(data).encode("utf-8")

    request = urllib.request.Request(
        f"{API_BASE_URL}{path}{query}",
        headers=headers,
        data=payload,
        method=method,
    )

    try:
        with urllib.request.urlopen(request) as response:
            body = response.read()
            if not body:
                return {}
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Asana API request failed with HTTP {exc.code} for {method} {path}: {body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Unable to reach Asana API: {exc.reason}") from exc


def asana_get(path: str, token: str, params: dict[str, str] | None = None) -> dict:
    return asana_request("GET", path, token, params=params)


def asana_post(path: str, token: str, data: dict) -> dict:
    return asana_request("POST", path, token, data=data)


def asana_delete(path: str, token: str) -> dict:
    return asana_request("DELETE", path, token)


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


def wait_for_job(token: str, job_gid: str, *, poll_interval: float = 1.0) -> dict:
    while True:
        payload = asana_get(f"/jobs/{job_gid}", token)
        status = payload.get("data", {}).get("status")

        if status == "succeeded":
            return payload

        if status == "failed":
            raise RuntimeError(f"Asana job {job_gid} failed: {json.dumps(payload)}")

        time.sleep(poll_interval)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "template"
