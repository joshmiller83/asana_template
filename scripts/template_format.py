from datetime import datetime, timezone


FORMAT_VERSION = 1


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


def simplify_subtask(subtask: dict) -> dict:
    return {
        "name": subtask["name"],
        "notes": subtask.get("notes", ""),
        "resource_subtype": subtask.get("resource_subtype", "default_task"),
        "source_gid": subtask.get("gid"),
        "dependency_source_gids": [
            dependency["gid"] for dependency in subtask.get("dependencies", [])
        ],
    }


def simplify_task(task: dict, subtasks: list[dict]) -> dict:
    return {
        "name": task["name"],
        "notes": task.get("notes", ""),
        "resource_subtype": task.get("resource_subtype", "default_task"),
        "source_gid": task.get("gid"),
        "dependency_source_gids": [
            dependency["gid"] for dependency in task.get("dependencies", [])
        ],
        "subtasks": [simplify_subtask(subtask) for subtask in subtasks],
    }


def build_editable_template(
    template: dict,
    project: dict,
    sections: list[dict],
    tasks: list[dict],
) -> dict:
    section_index = []
    section_lookup = {}
    for section in sections:
        entry = {
            "name": section["name"],
            "source_gid": section.get("gid"),
            "tasks": [],
        }
        section_index.append(entry)
        if section.get("gid"):
            section_lookup[section["gid"]] = entry

    unsectioned_tasks: list[dict] = []

    for task in tasks:
        memberships = task.get("memberships") or []
        section_gid = None
        for membership in memberships:
            section = membership.get("section")
            if section and section.get("gid"):
                section_gid = section["gid"]
                break

        simplified_task = task["editable_task"]
        if section_gid and section_gid in section_lookup:
            section_lookup[section_gid]["tasks"].append(simplified_task)
        else:
            unsectioned_tasks.append(simplified_task)

    return {
        "format_version": FORMAT_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "export_strategy": "instantiate_project_template",
        "template": {
            "name": template["name"],
            "description": template.get("description", ""),
            "source_gid": template["gid"],
            "workspace_name": (template.get("team") or {}).get("name"),
            "workspace_gid": (template.get("team") or {}).get("gid"),
            "requested_dates": template.get("requested_dates", []),
        },
        "import": {
            "mode": "create_new_versioned_template",
            "version_name_template": f"{template['name']} vNEXT",
            "source_template_gid": template["gid"],
        },
        "instantiated_project": {
            "name": project["name"],
            "source_gid": project["gid"],
        },
        "sections": section_index,
        "unsectioned_tasks": unsectioned_tasks,
    }


def render_outline(editable_template: dict) -> str:
    lines = []
    template = editable_template["template"]
    import_block = editable_template["import"]
    project = editable_template.get("instantiated_project") or {}

    lines.append(f"# {template['name']}")
    lines.append("")
    lines.append(f"- source_template_gid: `{template['source_gid']}`")
    lines.append(f"- export_strategy: `{editable_template['export_strategy']}`")
    lines.append(f"- format_version: `{editable_template['format_version']}`")
    lines.append(f"- import_mode: `{import_block['mode']}`")
    lines.append(f"- next_version_name: `{import_block['version_name_template']}`")
    if project.get("source_gid"):
        lines.append(f"- instantiated_project_gid: `{project['source_gid']}`")

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

    for section in editable_template["sections"]:
        lines.append(f"## {section['name']}")
        lines.append("")
        if not section["tasks"]:
            lines.append("_No tasks_")
            lines.append("")
            continue

        for task in section["tasks"]:
            lines.append(f"- {task['name']}")
            if task.get("source_gid"):
                lines.append(f"  source_gid: `{task['source_gid']}`")
            if task.get("dependency_source_gids"):
                lines.append(
                    "  depends_on_source_gids: "
                    + ", ".join(f"`{gid}`" for gid in task["dependency_source_gids"])
                )
            if task.get("notes"):
                lines.append(f"  notes: {task['notes']}")
            for subtask in task.get("subtasks", []):
                lines.append(f"  - {subtask['name']}")
                if subtask.get("source_gid"):
                    lines.append(f"    source_gid: `{subtask['source_gid']}`")
                if subtask.get("dependency_source_gids"):
                    lines.append(
                        "    depends_on_source_gids: "
                        + ", ".join(f"`{gid}`" for gid in subtask["dependency_source_gids"])
                    )
                if subtask.get("notes"):
                    lines.append(f"    notes: {subtask['notes']}")
        lines.append("")

    if editable_template["unsectioned_tasks"]:
        lines.append("## Unsectioned")
        lines.append("")
        for task in editable_template["unsectioned_tasks"]:
            lines.append(f"- {task['name']}")
            if task.get("source_gid"):
                lines.append(f"  source_gid: `{task['source_gid']}`")
            if task.get("dependency_source_gids"):
                lines.append(
                    "  depends_on_source_gids: "
                    + ", ".join(f"`{gid}`" for gid in task["dependency_source_gids"])
                )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
