# /project-template

Create a new Asana project template or update an existing one from a source of changes the user provides.

## What this skill does

You are working inside a repository that manages Asana project templates as local JSON files (`templates/<slug>/template.json`). Your job is to translate a source of structured information — a checklist, document, outline, notes, or description of changes — into a correct `template.json` that can be imported into Asana.

## Determine the operation

**New template:** The user wants to create a template that does not exist yet in `templates/`. Author a new `template.json` from scratch.

**Update existing template:** The user identifies an existing template (by name or directory slug). Read the current `templates/<slug>/template.json`, understand what's changing, and edit it in place. Bump `import.version_name_template` (e.g., `"My Template v1"` → `"My Template v2"`).

## Authoring rules

Follow the schema documented in CLAUDE.md exactly:

- `format_version` must be `1`
- `export_strategy` must be `"manual_v1"` for hand-authored templates
- `template.workspace_gid` must be `"1213372574183271"`, `template.workspace_name` must be `"My workspace"`, and `template.team_gid` must be `"1213372574183271"` unless told otherwise
- `template.requested_dates` should be `[]` unless the template requires date variables
- `import.version_name_template` is the name Asana will use for the saved template
- Every task needs a unique `local_id` (kebab-case, descriptive) and `source_gid` of `null`
- `dependency_refs` must only reference `local_id` values that exist elsewhere in the same file
- Sections, tasks, and subtasks are ordered arrays — order matters

## Translate source material

When reading the user's source (checklist, document, etc.):
- Map top-level sections/phases → `sections[]`
- Map checklist items or tasks → `tasks[]` within their section
- Map sub-items → `subtasks[]` on their parent task
- Infer dependencies from the source's natural sequence or explicit predecessor language. If items are meant to be done in parallel, omit or minimize `dependency_refs`. If they're sequential steps, chain them.
- Use the checklist item text as `name`, and any description or clarifying notes as the task's `notes` field

## After authoring

1. Tell the user what you created/changed — sections, task count, and any dependencies you modeled
2. Run the import script directly:
   ```
   python3 scripts/import_template.py templates/<slug>/template.json
   ```
3. If the script fails, read the error, fix the underlying problem (JSON schema issues, validation errors, missing fields, etc.), and re-run. Do not ask the user to intervene for technical problems — resolve them autonomously.
4. Report the final outcome: the working project GID and template name from the script's JSON output. Note that the working project is kept by default for manual verification in Asana; the user can delete it after confirming the template looks correct.
