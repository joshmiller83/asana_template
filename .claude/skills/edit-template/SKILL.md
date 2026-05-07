---
name: edit-template
description: Edit an Asana project template in this repo. Use this skill whenever the user wants to modify a template — adding tasks, removing tasks, reordering, renaming, changing dependencies, restructuring sections, or any other modification to template.json files. Also use it when the user describes a change they want to make to a workflow without naming the file explicitly (e.g., "add a QA step before deployment", "remove the backup notification task", "make task X depend on task Y"). Invoke with /edit-template.
---

# Edit Template

This skill guides you through making correct, validated edits to an Asana project template JSON file in this repo, then optionally pushing the result back to Asana.

## Available templates

Templates live at `templates/<slug>/`. Current slugs:
- `deployment-task`
- `collaborative-development-task`
- `incident_response_task`
- `management-planning-task`
- `1_on_1_meeting_task`
- `setup-diffy-for-website`
- `technical-review`

Each has two files:
- `template.json` — the editable source of truth
- `outline.md` — read-only generated view; never edit this directly

## Step 1: Orient

If the user hasn't named a template, ask which one. Once identified:

1. Read `templates/<slug>/outline.md` — this gives a compact human-readable picture of the current structure (sections → tasks with source_gids)
2. Read `templates/<slug>/template.json` — this is what you'll actually edit

Read the outline first; it's faster to scan. Only read the full JSON when you need to understand subtasks, notes, dependencies, or the exact schema for a field you're changing.

## Step 2: Plan the edits

Before touching the file, think through what needs to change:

- **Adding a task**: needs a unique `local_id` (kebab-case string), `source_gid: null`, correct section placement
- **Removing a task**: delete its entry AND remove its `source_gid` or `local_id` from any `dependency_refs` elsewhere
- **Reordering**: move the task object within the `tasks` array; order in JSON = order in Asana
- **Renaming**: just change the `name` field
- **Dependencies**: `dependency_refs` lists identifiers the task _depends on_ (i.e., predecessors). Each ref must be a `source_gid` or `local_id` that exists somewhere else in the same file.
- **New section**: add a new object to the `sections` array with a `name` and `tasks: []`

If the user's request would break referential integrity (e.g., removing a task that others depend on), flag it and ask how to handle the dangling refs.

## Step 3: Edit template.json

Make the targeted edits. Key rules:

- **Never** change `format_version` (must stay `1`)
- **Never** change or invent `source_gid` values on existing tasks
- **Never** add a `source_gid` to a brand-new task — use `local_id` instead
- `local_id` must be unique within the file
- After edits, bump `import.version_name_template` (e.g., `"Deployment Task v3"`) unless the user says not to

## Step 4: Validate

Before finishing, do a quick mental scan:

1. Every string in any `dependency_refs` array matches either a `source_gid` or `local_id` elsewhere in the file
2. Every new task without a `source_gid` has a `local_id`
3. No duplicate `local_id` values
4. `format_version` is still `1`

If you're unsure, you can run the validator without actually importing:
```bash
cd /Users/jomiller/Developer/github/joshmiller83/asana_template
source .venv/bin/activate
python3 -c "
import json, sys
sys.path.insert(0, 'scripts')
from import_template import validate_template_for_import
data = json.load(open('templates/<slug>/template.json'))
errs = validate_template_for_import(data)
print('OK' if not errs else '\n'.join(errs))
"
```

## Step 5: Push to Asana (optional)

Ask the user if they want to push to Asana now. If yes:
```bash
cd /Users/jomiller/Developer/github/joshmiller83/asana_template
source .venv/bin/activate
python3 scripts/import_template.py templates/<slug>/template.json
```

The script creates a new versioned template in Asana and polls until it materializes. It takes ~30–60 seconds. Share the output with the user so they can see the new template GID.

If the user passes `--delete-project`, the temporary working project is cleaned up after import. This is usually fine unless they want to inspect the project in Asana first.

## Common patterns

**Add a new task to an existing section:**
```json
{
  "name": "New task name",
  "notes": "",
  "resource_subtype": "default_task",
  "source_gid": null,
  "local_id": "new-task-slug",
  "dependency_refs": ["source_gid_of_predecessor"],
  "subtasks": []
}
```

**Add a milestone:**
Same as above but `"resource_subtype": "milestone"`.

**Make task B depend on task A** (A must finish before B starts):
Add A's identifier to B's `dependency_refs`.

**Remove a dependency:**
Delete the ref from `dependency_refs`. Don't delete the task itself unless the user asks.
