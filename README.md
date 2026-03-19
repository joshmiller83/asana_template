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
