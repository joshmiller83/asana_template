# asana_template

Lightweight Python scripts for reading and modifying Asana project templates.

## Purpose

This repository is intended for CLI-driven automation against an Asana project template. The expected workflow is:

- load an Asana machine token from a local env file
- use Python scripts to inspect and update workspace project templates
- let an LLM-capable CLI operate on those scripts instead of editing templates manually in the Asana UI

## Notes

- keep credentials out of git
- prefer small, composable scripts
- treat this as an automation utility, not a full application
- keep this README updated with script usage as new commands are added

## Configuration

- copy `.env.example` to `.env`
- set `ASANA_ACCESS_TOKEN`
- optionally set `ASANA_WORKSPACE_GID`
- `.env` is ignored by git

## Environment

Use a local virtual environment for all script execution:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

This repo currently uses the Python standard library only, so there is no `requirements.txt` yet.

## Workflow Assumption

Asana appears to support project-template listing, retrieval, deletion, and instantiation directly, but not full in-place template editing through the same API surface.

Current working assumption:

- export a template by instantiating it into a temporary project
- inspect or edit the exported local snapshot
- later import changes by applying them to a temporary project and saving that project as a new template version
- manually archive or delete the older template in Asana

This means import is expected to create a new versioned template rather than mutate the original template GID in place.

## Editable Snapshot Contract

`template.json` is the source of truth for future imports.

Detailed format guidance lives in [TEMPLATE_JSON_FORMAT.md](/Users/jomiller/Developer/github/joshmiller83/asana_template/TEMPLATE_JSON_FORMAT.md).

Current managed fields:

- template name and description
- requested date values used during export/import instantiation
- ordered sections
- ordered tasks within sections
- ordered subtasks
- task `resource_subtype`
- task and subtask notes
- dependency links represented as `dependency_source_gids`

Current intent:

- `source_gid` preserves the original Asana object identity from the exported template snapshot
- `dependency_source_gids` preserves dependency relationships between exported tasks
- `outline.md` is a readable generated view and is not intended to be edited as the import source

Dependency note:

- export now captures dependencies from the instantiated project snapshot
- import will need a two-pass process: create all tasks first, then recreate dependency links once new Asana task IDs exist
- the first import pass will target dependency recreation for exported tasks that already have `source_gid` relationships

## Scripts

### `list_project_templates.py`

Lists project templates for the configured workspace.

```bash
python3 scripts/list_project_templates.py
```

Options:

- `--workspace-gid 1234567890` to target a specific workspace
- `--json` to print raw JSON

Examples:

```bash
python3 scripts/list_project_templates.py --workspace-gid 1234567890
```

```bash
python3 scripts/list_project_templates.py --json
```

Behavior:

- if `ASANA_WORKSPACE_GID` is set, the script uses it by default
- if the token only has access to one workspace, the script auto-selects it
- if multiple workspaces are available, the script prompts interactively when possible

### `download_template.py`

Exports one template, or all visible templates, into local snapshot files under `templates/`.

```bash
python3 scripts/download_template.py 1213441914697823
```

Output:

- `template.json` contains the structured snapshot
- `outline.md` contains a readable outline of sections, tasks, and subtasks
- task dependencies are preserved in `template.json` as `dependency_source_gids`

Options:

- `--all` to export all templates in the selected workspace
- `--workspace-gid 1234567890` to target a specific workspace
- `--output-dir path/to/templates` to change the output root
- `--date YYYY-MM-DD` to satisfy required template date variables during instantiation
- `--keep-project` to retain the temporary instantiated project for inspection

Examples:

```bash
python3 scripts/download_template.py 1213441914697823
```

```bash
python3 scripts/download_template.py --all
```

Behavior:

- the exporter instantiates a temporary project from the source template
- it reads the project, sections, tasks, and subtasks through standard project APIs
- it captures dependency links between tasks as source-task references
- it writes a local snapshot
- by default it deletes the temporary project when the export is complete

## Tests

Run the stdlib test suite with:

```bash
.venv/bin/python -m unittest discover -s tests
```
