# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

This repo automates Asana project template management via the Asana API. The workflow: export a template to a local JSON snapshot, edit the JSON (optionally with LLM help), then import it back as a new versioned template. The LLM's role is to understand complex task/dependency relationships and produce correct `template.json` edits — the scripts handle all API interactions.

## Environment Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
# No external dependencies — stdlib only
```

`.env` file (git-ignored):
```
ASANA_ACCESS_TOKEN=your_machine_token
ASANA_WORKSPACE_GID=1213372574183271  # optional
```

## Common Commands

```bash
# List available templates
python3 scripts/list_project_templates.py --workspace-gid <gid>
python3 scripts/list_project_templates.py --json

# Export a template to templates/<slug>/
python3 scripts/download_template.py <template_gid>
python3 scripts/download_template.py --all
python3 scripts/download_template.py <template_gid> --keep-project  # don't delete temp project

# Import edited template.json as new versioned template
python3 scripts/import_template.py templates/<slug>/template.json
python3 scripts/import_template.py templates/<slug>/template.json --delete-project

# Run tests
.venv/bin/python -m unittest discover -s tests
```

## Architecture

### Three-Phase Workflow

**Export** (`download_template.py`): Instantiates a template into a temporary Asana project, reads its full structure (sections → tasks → subtasks + dependencies), serializes to `template.json` (editable) and `outline.md` (human-readable), then deletes the temp project.

**Edit**: User (or LLM) modifies `template.json` directly. The `outline.md` is read-only — it's generated output.

**Import** (`import_template.py`): Validates JSON, creates a working project, runs a **two-pass creation** (pass 1: create all tasks/subtasks building a gid map; pass 2: resolve dependency refs and link them), saves the project as a new template, then polls until the template is materialized in Asana.

### Key Modules

- **`scripts/asana_utils.py`** — low-level HTTP wrapper (`asana_get/post/delete`, `paginate`, `wait_for_job`, workspace resolution)
- **`scripts/template_format.py`** — schema conversion (`build_editable_template`, `simplify_task`, `render_outline`); `FORMAT_VERSION = 1` is the current schema version
- **`scripts/download_template.py`** — export orchestration
- **`scripts/import_template.py`** — import orchestration, validation, two-pass creation

### `template.json` Schema

```json
{
  "format_version": 1,
  "template": {
    "source_gid": "...",        // original Asana template gid — do NOT change
    "workspace_gid": "...",
    "team_gid": "...",          // required by Asana saveAsTemplate; use "1213372574183271"
    "requested_dates": [...]    // date variables needed at instantiation
  },
  "import": {
    "version_name_template": "My Template v2"  // name for the next import
  },
  "sections": [
    {
      "name": "Section Name",
      "tasks": [
        {
          "name": "Task Name",
          "notes": "...",
          "resource_subtype": "default_task",  // or "milestone"
          "source_gid": "12345",  // null or omit for brand-new tasks
          "local_id": "my-new-task",  // unique string for new tasks without gids
          "dependency_refs": ["source_gid_of_predecessor", "local_id_of_predecessor"],
          "subtasks": [...]
        }
      ]
    }
  ],
  "unsectioned_tasks": []
}
```

### Task Identity Rules

- **Existing tasks**: identified by `source_gid` (their original Asana gid)
- **New tasks**: use a unique `local_id` string (e.g., `"draft-review"`) with `source_gid: null`
- **Dependencies**: `dependency_refs` must contain `source_gid` or `local_id` values that exist elsewhere in the same file
- Deleting a task requires removing its identifier from all `dependency_refs` elsewhere

### Safe Edits to `template.json`

Safe: rename tasks/sections, reorder, edit notes, add/remove tasks (with proper `local_id`), change `resource_subtype`, modify `dependency_refs`, update `version_name_template`, update `requested_dates[].value`.

Never: change `format_version`, change `source_gid` on existing tasks, invent `source_gid` values.

## Template Directories

Each template lives at `templates/<slug>/`:
- `template.json` — source of truth, the file to edit
- `outline.md` — generated view for human/LLM review, never edit directly

Current templates: `deployment-task`, `management-planning-task`, `collaborative-development-task`, `1_on_1_meeting_task`, `incident_response_task`, `setup-diffy-for-website`.

## LLM-Assisted Editing Workflow

1. Read `templates/<slug>/outline.md` to understand current template structure
2. Read `templates/<slug>/template.json` to understand the full schema
3. Make targeted edits to `template.json` — add/remove/reorder tasks, update dependencies
4. Validate that all `dependency_refs` point to real `source_gid` or `local_id` values in the file
5. Update `import.version_name_template` if this is a new version
6. Run `python3 scripts/import_template.py templates/<slug>/template.json` to push to Asana
