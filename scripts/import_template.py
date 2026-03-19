#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path

try:
    from .asana_utils import (
        asana_delete,
        asana_get,
        asana_post,
        asana_request,
        load_dotenv,
        paginate,
        require_access_token,
    )
except ImportError:
    from asana_utils import (
        asana_delete,
        asana_get,
        asana_post,
        asana_request,
        load_dotenv,
        paginate,
        require_access_token,
    )


def load_template(path: Path) -> dict:
    return json.loads(path.read_text())


def collect_known_task_source_gids(template_data: dict) -> set[str]:
    known: set[str] = set()

    def collect_task(task: dict) -> None:
        source_gid = task.get("source_gid")
        if source_gid:
            known.add(source_gid)
        for subtask in task.get("subtasks", []):
            subtask_gid = subtask.get("source_gid")
            if subtask_gid:
                known.add(subtask_gid)

    for section in template_data.get("sections", []):
        for task in section.get("tasks", []):
            collect_task(task)

    for task in template_data.get("unsectioned_tasks", []):
        collect_task(task)

    return known


def validate_template_for_import(template_data: dict) -> list[str]:
    errors: list[str] = []

    if template_data.get("format_version") != 1:
        errors.append(
            f"Unsupported format_version {template_data.get('format_version')!r}; expected 1."
        )

    template_block = template_data.get("template") or {}
    import_block = template_data.get("import") or {}

    if not template_block.get("workspace_gid"):
        errors.append("template.workspace_gid is required.")

    if not import_block.get("version_name_template"):
        errors.append("import.version_name_template is required.")

    known_source_gids = collect_known_task_source_gids(template_data)

    def validate_task(task: dict, location: str) -> None:
        if not task.get("name"):
            errors.append(f"{location} is missing a task name.")

        for dependency_gid in task.get("dependency_source_gids", []):
            if dependency_gid not in known_source_gids:
                errors.append(
                    f"{location} has dependency_source_gid {dependency_gid} that does not exist in this template."
                )

        for index, subtask in enumerate(task.get("subtasks", []), start=1):
            subtask_location = f"{location}.subtasks[{index}]"
            if not subtask.get("name"):
                errors.append(f"{subtask_location} is missing a subtask name.")
            for dependency_gid in subtask.get("dependency_source_gids", []):
                if dependency_gid not in known_source_gids:
                    errors.append(
                        f"{subtask_location} has dependency_source_gid {dependency_gid} that does not exist in this template."
                    )

    for section_index, section in enumerate(template_data.get("sections", []), start=1):
        if "name" not in section:
            errors.append(f"sections[{section_index}] is missing a section name.")
        for task_index, task in enumerate(section.get("tasks", []), start=1):
            validate_task(task, f"sections[{section_index}].tasks[{task_index}]")

    for task_index, task in enumerate(template_data.get("unsectioned_tasks", []), start=1):
        validate_task(task, f"unsectioned_tasks[{task_index}]")

    return errors


def create_project(token: str, template_data: dict) -> dict:
    template_block = template_data["template"]
    import_block = template_data["import"]
    workspace_gid = resolve_import_workspace_gid(token, template_data)
    payload = {
        "data": {
            "name": import_block["version_name_template"],
            "notes": template_block.get("description", ""),
            "workspace": workspace_gid,
        }
    }
    return asana_post("/projects", token, payload)["data"]


def resolve_import_workspace_gid(token: str, template_data: dict) -> str:
    template_block = template_data.get("template") or {}
    requested_workspace_gid = template_block.get("workspace_gid")
    requested_workspace_name = template_block.get("workspace_name")

    workspaces = paginate("/workspaces", token)
    if requested_workspace_gid and any(
        workspace["gid"] == requested_workspace_gid for workspace in workspaces
    ):
        return requested_workspace_gid

    if requested_workspace_name:
        matching = [
            workspace
            for workspace in workspaces
            if workspace.get("name") == requested_workspace_name
        ]
        if len(matching) == 1:
            return matching[0]["gid"]

    if len(workspaces) == 1:
        return workspaces[0]["gid"]

    raise RuntimeError(
        "Unable to resolve a real Asana workspace for import from template.workspace_gid "
        f"={requested_workspace_gid!r} and template.workspace_name={requested_workspace_name!r}."
    )


def get_project_sections(token: str, project_gid: str) -> list[dict]:
    payload = asana_get(
        f"/projects/{project_gid}/sections",
        token,
        {"opt_fields": "gid,name"},
    )
    return payload.get("data", [])


def update_section_name(token: str, section_gid: str, name: str) -> dict:
    return asana_request("PUT", f"/sections/{section_gid}", token, data={"data": {"name": name}})[
        "data"
    ]


def create_section(token: str, project_gid: str, name: str) -> dict:
    return asana_post(
        f"/projects/{project_gid}/sections",
        token,
        {"data": {"name": name}},
    )["data"]


def create_task(token: str, workspace_gid: str, task_data: dict) -> dict:
    payload = {
        "data": {
            "workspace": workspace_gid,
            "name": task_data["name"],
            "notes": task_data.get("notes", ""),
            "resource_subtype": task_data.get("resource_subtype", "default_task"),
        }
    }
    return asana_post("/tasks", token, payload)["data"]


def add_task_to_project(
    token: str,
    task_gid: str,
    project_gid: str,
    section_gid: str | None,
    previous_task_gid: str | None,
) -> None:
    data: dict[str, object] = {"project": project_gid}
    if section_gid:
        data["section"] = section_gid
    if previous_task_gid:
        data["insert_after"] = previous_task_gid

    asana_post(f"/tasks/{task_gid}/addProject", token, {"data": data})


def create_subtask(token: str, parent_task_gid: str, subtask_data: dict) -> dict:
    payload = {
        "data": {
            "name": subtask_data["name"],
            "notes": subtask_data.get("notes", ""),
            "resource_subtype": subtask_data.get("resource_subtype", "default_task"),
        }
    }
    return asana_post(f"/tasks/{parent_task_gid}/subtasks", token, payload)["data"]


def add_dependencies(token: str, task_gid: str, dependency_gids: list[str]) -> None:
    if not dependency_gids:
        return

    asana_post(
        f"/tasks/{task_gid}/addDependencies",
        token,
        {"data": {"dependencies": dependency_gids}},
    )


def save_project_as_template(
    token: str, project_gid: str, name: str, workspace_gid: str
) -> dict:
    payload = {
        "data": {"name": name, "public": False, "workspace": workspace_gid}
    }
    return asana_post(f"/projects/{project_gid}/saveAsTemplate", token, payload)["data"]


def initialize_sections(
    token: str, project_gid: str, template_data: dict
) -> tuple[list[dict], list[dict]]:
    desired_sections = template_data.get("sections", [])
    existing_sections = get_project_sections(token, project_gid)

    created_sections: list[dict] = []
    if desired_sections:
        if existing_sections:
            first_section = update_section_name(
                token, existing_sections[0]["gid"], desired_sections[0]["name"]
            )
            created_sections.append(first_section)
        else:
            created_sections.append(create_section(token, project_gid, desired_sections[0]["name"]))

        for section in desired_sections[1:]:
            created_sections.append(create_section(token, project_gid, section["name"]))

    return desired_sections, created_sections


def build_project_from_template(token: str, template_data: dict) -> tuple[dict, dict[str, str]]:
    project = create_project(token, template_data)
    workspace_gid = resolve_import_workspace_gid(token, template_data)
    source_to_new_gid: dict[str, str] = {}
    deferred_dependencies: list[tuple[str, list[str]]] = []

    desired_sections, created_sections = initialize_sections(token, project["gid"], template_data)

    for section_data, section_record in zip(desired_sections, created_sections):
        previous_task_gid = None
        for task_data in section_data.get("tasks", []):
            created_task = create_task(token, workspace_gid, task_data)
            add_task_to_project(
                token,
                created_task["gid"],
                project["gid"],
                section_record["gid"],
                previous_task_gid,
            )
            previous_task_gid = created_task["gid"]

            if task_data.get("source_gid"):
                source_to_new_gid[task_data["source_gid"]] = created_task["gid"]

            if task_data.get("dependency_source_gids"):
                deferred_dependencies.append(
                    (created_task["gid"], task_data["dependency_source_gids"])
                )

            for subtask_data in task_data.get("subtasks", []):
                created_subtask = create_subtask(token, created_task["gid"], subtask_data)
                if subtask_data.get("source_gid"):
                    source_to_new_gid[subtask_data["source_gid"]] = created_subtask["gid"]
                if subtask_data.get("dependency_source_gids"):
                    deferred_dependencies.append(
                        (created_subtask["gid"], subtask_data["dependency_source_gids"])
                    )

    previous_task_gid = None
    for task_data in template_data.get("unsectioned_tasks", []):
        created_task = create_task(token, workspace_gid, task_data)
        add_task_to_project(
            token,
            created_task["gid"],
            project["gid"],
            None,
            previous_task_gid,
        )
        previous_task_gid = created_task["gid"]

        if task_data.get("source_gid"):
            source_to_new_gid[task_data["source_gid"]] = created_task["gid"]

        if task_data.get("dependency_source_gids"):
            deferred_dependencies.append(
                (created_task["gid"], task_data["dependency_source_gids"])
            )

        for subtask_data in task_data.get("subtasks", []):
            created_subtask = create_subtask(token, created_task["gid"], subtask_data)
            if subtask_data.get("source_gid"):
                source_to_new_gid[subtask_data["source_gid"]] = created_subtask["gid"]
            if subtask_data.get("dependency_source_gids"):
                deferred_dependencies.append(
                    (created_subtask["gid"], subtask_data["dependency_source_gids"])
                )

    for task_gid, dependency_source_gids in deferred_dependencies:
        resolved_dependency_gids = [
            source_to_new_gid[dependency_source_gid]
            for dependency_source_gid in dependency_source_gids
            if dependency_source_gid in source_to_new_gid
        ]
        add_dependencies(token, task_gid, resolved_dependency_gids)

    return project, source_to_new_gid


def import_template(
    token: str, template_path: Path, *, keep_project: bool = False
) -> tuple[dict, dict]:
    template_data = load_template(template_path)
    errors = validate_template_for_import(template_data)
    if errors:
        raise RuntimeError("Template validation failed:\n- " + "\n- ".join(errors))

    project = build_project_from_template(token, template_data)[0]

    try:
        workspace_gid = resolve_import_workspace_gid(token, template_data)
        job = save_project_as_template(
            token,
            project["gid"],
            template_data["import"]["version_name_template"],
            workspace_gid,
        )
        return project, job
    finally:
        if not keep_project:
            asana_delete(f"/projects/{project['gid']}", token)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import a local template.json into Asana as a new versioned project template."
    )
    parser.add_argument(
        "template_json",
        help="Path to the edited template.json file to import.",
    )
    parser.add_argument(
        "--keep-project",
        action="store_true",
        help="Keep the temporary working project instead of deleting it after template creation.",
    )
    return parser


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(repo_root / ".env")

    parser = build_parser()
    args = parser.parse_args()

    try:
        token = require_access_token()
        project, job = import_template(
            token, Path(args.template_json), keep_project=args.keep_project
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "working_project_gid": project["gid"],
                "template_creation_job_gid": job.get("gid"),
                "template_gid": job.get("new_project_template", {}).get("gid"),
                "template_name": job.get("new_project_template", {}).get("name")
                or job.get("new_project", {}).get("name"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
