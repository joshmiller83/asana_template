#!/usr/bin/env python3

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

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


def build_requested_dates(template: dict, fallback_date: str) -> list[dict]:
    requested_dates = []
    for requested_date in template.get("requested_dates", []):
        requested_dates.append(
            {
                "gid": requested_date["gid"],
                "name": requested_date.get("name"),
                "description": requested_date.get("description"),
                "value": fallback_date,
            }
        )
    return requested_dates


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
                "created_at,modified_at"
            )
        },
    )


def simplify_task(task: dict, subtasks: list[dict]) -> dict:
    return {
        "gid": task["gid"],
        "name": task["name"],
        "notes": task.get("notes", ""),
        "resource_subtype": task.get("resource_subtype"),
        "completed": task.get("completed", False),
        "created_at": task.get("created_at"),
        "modified_at": task.get("modified_at"),
        "subtasks": [
            {
                "gid": subtask["gid"],
                "name": subtask["name"],
                "notes": subtask.get("notes", ""),
                "resource_subtype": subtask.get("resource_subtype"),
                "completed": subtask.get("completed", False),
                "created_at": subtask.get("created_at"),
                "modified_at": subtask.get("modified_at"),
            }
            for subtask in subtasks
        ],
    }


def build_snapshot(template: dict, project: dict, sections: list[dict], tasks: list[dict]) -> dict:
    section_index = [
        {
            "gid": section["gid"],
            "name": section["name"],
            "created_at": section.get("created_at"),
            "tasks": [],
        }
        for section in sections
    ]
    section_tasks = {section["gid"]: section for section in section_index}
    unsectioned_tasks: list[dict] = []

    for task in tasks:
        memberships = task.get("memberships") or []
        section_gid = None
        for membership in memberships:
            section = membership.get("section")
            if section and section.get("gid"):
                section_gid = section["gid"]
                break

        simplified = task["snapshot_task"]
        if section_gid and section_gid in section_tasks:
            section_tasks[section_gid]["tasks"].append(simplified)
        else:
            unsectioned_tasks.append(simplified)

    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "export_strategy": "instantiate_project_template",
        "template": template,
        "instantiated_project": project,
        "sections": section_index,
        "unsectioned_tasks": unsectioned_tasks,
    }


def render_outline(snapshot: dict) -> str:
    lines = []
    template = snapshot["template"]
    project = snapshot["instantiated_project"]

    lines.append(f"# {template['name']}")
    lines.append("")
    lines.append(f"- template_gid: `{template['gid']}`")
    lines.append(f"- export_strategy: `{snapshot['export_strategy']}`")
    lines.append(f"- instantiated_project_gid: `{project['gid']}`")

    requested_dates = template.get("requested_dates") or []
    if requested_dates:
        values = ", ".join(
            f"{requested_date['name']}={requested_date.get('value', 'export-date')}"
            for requested_date in requested_dates
        )
        lines.append(f"- requested_dates: `{values}`")

    lines.append("")

    if template.get("description"):
        lines.append("## Description")
        lines.append("")
        lines.append(template["description"])
        lines.append("")

    for section in snapshot["sections"]:
        lines.append(f"## {section['name']}")
        lines.append("")
        if not section["tasks"]:
            lines.append("_No tasks_")
            lines.append("")
            continue

        for task in section["tasks"]:
            lines.append(f"- {task['name']} `{task['gid']}`")
            if task.get("notes"):
                lines.append(f"  notes: {task['notes']}")
            for subtask in task.get("subtasks", []):
                lines.append(f"  - {subtask['name']} `{subtask['gid']}`")
                if subtask.get("notes"):
                    lines.append(f"    notes: {subtask['notes']}")
        lines.append("")

    if snapshot["unsectioned_tasks"]:
        lines.append("## Unsectioned")
        lines.append("")
        for task in snapshot["unsectioned_tasks"]:
            lines.append(f"- {task['name']} `{task['gid']}`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


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
            task["snapshot_task"] = simplify_task(task, get_subtasks(token, task["gid"]))
            tasks.append(task)

        snapshot = build_snapshot(template, project, sections, tasks)
        output_dir = output_root / f"{slugify(template['name'])}-{template['gid']}"
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
        default="exports",
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
