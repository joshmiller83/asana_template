#!/usr/bin/env python3

import argparse
import json
from datetime import date
from pathlib import Path

try:
    from .asana_utils import (
        asana_delete,
        asana_get,
        asana_post,
        load_dotenv,
        paginate,
        require_access_token,
        resolve_workspace_gid,
        slugify,
        wait_for_job,
    )
    from .template_format import (
        build_editable_template,
        build_requested_dates,
        render_outline,
        simplify_task,
    )
except ImportError:
    from asana_utils import (
        asana_delete,
        asana_get,
        asana_post,
        load_dotenv,
        paginate,
        require_access_token,
        resolve_workspace_gid,
        slugify,
        wait_for_job,
    )
    from template_format import (
        build_editable_template,
        build_requested_dates,
        render_outline,
        simplify_task,
    )


def list_project_templates(token: str, workspace_gid: str) -> list[dict]:
    return paginate(
        "/project_templates",
        token,
        {
            "workspace": workspace_gid,
            "opt_fields": "gid,name,team.name,owner.name,requested_dates",
        },
    )


def get_project_template(token: str, template_gid: str) -> dict:
    payload = asana_get(
        f"/project_templates/{template_gid}",
        token,
        {
            "opt_fields": (
                "gid,name,description,team.gid,team.name,owner.gid,owner.name,"
                "requested_dates,created_at,modified_at"
            )
        },
    )
    return payload["data"]

def instantiate_template(
    token: str,
    template_gid: str,
    template_name: str,
    requested_dates: list[dict],
) -> dict:
    payload = {
        "data": {
            "name": f"{template_name} [export snapshot]",
            "requested_dates": [
                {"gid": requested_date["gid"], "value": requested_date["value"]}
                for requested_date in requested_dates
            ],
        }
    }
    response = asana_post(
        f"/project_templates/{template_gid}/instantiateProject",
        token,
        payload,
    )
    job = response["data"]
    job_gid = job["gid"]
    wait_for_job(token, job_gid)
    return job["new_project"]


def get_project(token: str, project_gid: str) -> dict:
    payload = asana_get(
        f"/projects/{project_gid}",
        token,
        {
            "opt_fields": (
                "gid,name,notes,team.gid,team.name,owner.gid,owner.name,"
                "start_on,due_on,created_at,modified_at"
            )
        },
    )
    return payload["data"]


def get_sections(token: str, project_gid: str) -> list[dict]:
    return paginate(
        f"/projects/{project_gid}/sections",
        token,
        {"opt_fields": "gid,name,created_at"},
    )


def get_project_tasks(token: str, project_gid: str) -> list[dict]:
    return paginate(
        "/tasks",
        token,
        {
            "project": project_gid,
            "opt_fields": (
                "gid,name,notes,resource_subtype,completed,parent.gid,parent.name,"
                "memberships.project.gid,memberships.section.gid,memberships.section.name,"
                "dependencies.gid,"
                "created_at,modified_at"
            ),
        },
    )


def get_subtasks(token: str, task_gid: str) -> list[dict]:
    return paginate(
        f"/tasks/{task_gid}/subtasks",
        token,
        {
            "opt_fields": (
                "gid,name,notes,resource_subtype,completed,parent.gid,parent.name,"
                "dependencies.gid,"
                "created_at,modified_at"
            )
        },
    )

def write_snapshot(output_dir: Path, snapshot: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "template.json").write_text(json.dumps(snapshot, indent=2) + "\n")
    (output_dir / "outline.md").write_text(render_outline(snapshot))


def export_template(
    token: str,
    template_gid: str,
    output_root: Path,
    fallback_date: str,
    keep_project: bool,
) -> Path:
    template = get_project_template(token, template_gid)
    requested_dates = build_requested_dates(template, fallback_date)
    template["requested_dates"] = requested_dates

    new_project = instantiate_template(
        token,
        template_gid,
        template["name"],
        requested_dates,
    )
    project_gid = new_project["gid"]

    try:
        project = get_project(token, project_gid)
        sections = get_sections(token, project_gid)
        tasks = []
        for task in get_project_tasks(token, project_gid):
            if task.get("parent"):
                continue
            task["editable_task"] = simplify_task(task, get_subtasks(token, task["gid"]))
            tasks.append(task)

        snapshot = build_editable_template(template, project, sections, tasks)
        output_dir = output_root / slugify(template["name"])
        write_snapshot(output_dir, snapshot)
        return output_dir
    finally:
        if not keep_project:
            asana_delete(f"/projects/{project_gid}", token)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export one Asana project template to a local snapshot."
    )
    parser.add_argument(
        "template_gid",
        nargs="?",
        help="Project template GID. Omit with --all to export every template in the workspace.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Export all project templates visible in the selected workspace.",
    )
    parser.add_argument(
        "--workspace-gid",
        help="Workspace GID. Defaults to ASANA_WORKSPACE_GID or interactive selection.",
    )
    parser.add_argument(
        "--output-dir",
        default="templates",
        help="Directory where template snapshots will be written.",
    )
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Fallback YYYY-MM-DD used for any required template date variables.",
    )
    parser.add_argument(
        "--keep-project",
        action="store_true",
        help="Keep the temporary instantiated project instead of deleting it after export.",
    )
    return parser


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(repo_root / ".env")

    parser = build_parser()
    args = parser.parse_args()

    if not args.all and not args.template_gid:
        parser.error("Provide a template GID or use --all.")

    if args.all and args.template_gid:
        parser.error("Use either a template GID or --all, not both.")

    try:
        token = require_access_token()
        workspace_gid = resolve_workspace_gid(token, args.workspace_gid)
    except RuntimeError as exc:
        parser.error(str(exc))

    output_root = repo_root / args.output_dir

    try:
        if args.all:
            template_gids = [
                template["gid"] for template in list_project_templates(token, workspace_gid)
            ]
        else:
            template_gids = [args.template_gid]

        for template_gid in template_gids:
            output_dir = export_template(
                token,
                template_gid,
                output_root,
                args.date,
                args.keep_project,
            )
            print(f"Exported template {template_gid} -> {output_dir}")
    except RuntimeError as exc:
        print(str(exc))
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
