# Template JSON Format

This document explains the editable `template.json` format used in this repo.

Status:

- this format is real and currently produced by the exporter
- import is still being built
- some import behavior described here is intentional but still experimental
- if the importer forces format changes later, this document should be updated with the code

`template.json` is the source of truth for template edits.

`outline.md` is only a generated human-readable view. Do not treat `outline.md` as import input.

## Design Goals

- keep the file readable enough for human and LLM editing
- preserve enough identity to map an exported template back into a new imported version
- preserve ordering for sections, tasks, and subtasks
- preserve task dependencies
- allow safe editing without requiring every raw Asana field

## High-Level Model

Each template directory contains:

- `template.json`
- `outline.md`

The directory name is a stable repo path, for example:

- `templates/collaborative-development-task/`
- `templates/deployment-task/`

The directory name is for git and human organization. The real Asana identity lives inside `template.json`.

## Top-Level Shape

Example:

```json
{
  "format_version": 1,
  "exported_at": "2026-03-19T21:50:53.731060+00:00",
  "export_strategy": "instantiate_project_template",
  "template": {
    "name": "Collaborative Development Task",
    "description": "",
    "source_gid": "1213441914697823",
    "workspace_name": "My workspace",
    "workspace_gid": "1213372574183271",
    "requested_dates": []
  },
  "import": {
    "mode": "create_new_versioned_template",
    "version_name_template": "Collaborative Development Task vNEXT",
    "source_template_gid": "1213441914697823"
  },
  "instantiated_project": {
    "name": "Collaborative Development Task [export snapshot]",
    "source_gid": "1213754294945032"
  },
  "sections": [],
  "unsectioned_tasks": []
}
```

## Field Reference

### `format_version`

Current value:

- `1`

Purpose:

- identifies the expected JSON contract
- lets us evolve the importer later without guessing what shape a file uses

Editing guidance:

- do not change this unless the code changes with it

### `exported_at`

Purpose:

- records when the snapshot was created

Editing guidance:

- safe to leave unchanged
- safe to update manually, but there is usually no reason to do so
- importer should not depend on this value

### `export_strategy`

Current value:

- `instantiate_project_template`

Purpose:

- documents how the snapshot was created

Editing guidance:

- do not change this manually

### `template`

This contains the source template metadata.

Fields:

- `name`
- `description`
- `source_gid`
- `workspace_name`
- `workspace_gid`
- `requested_dates`

#### `template.name`

Purpose:

- source template display name
- likely default basis for the next imported template name

Editing guidance:

- safe to edit
- if you want the next versioned template to have a different base name, update this and also update `import.version_name_template`

#### `template.description`

Purpose:

- template-level description

Editing guidance:

- safe to edit

#### `template.source_gid`

Purpose:

- original Asana project template gid from the export source

Editing guidance:

- do not delete
- do not replace with a made-up value
- if you are intentionally re-basing the file onto another exported source template, only change this if you know exactly why

#### `template.workspace_name`

Purpose:

- human-readable workspace label from export time

Editing guidance:

- informational only
- importer should prefer `workspace_gid`, not this field
- safe to leave unchanged

#### `template.workspace_gid`

Purpose:

- Asana workspace identity for later import operations

Editing guidance:

- do not remove
- do not change unless the import target really is a different workspace

#### `template.requested_dates`

This is an array of required date variables the source template expects during instantiation.

Example:

```json
[
  {
    "gid": "1",
    "name": "Start Date",
    "description": "Choose a start date for your project.",
    "value": "2026-03-19"
  }
]
```

Field meaning:

- `gid`: Asana’s identity for the requested date slot
- `name`: human-readable label
- `description`: human-readable help text
- `value`: the date value used during export, and likely reused or overridden during import

Editing guidance:

- keep `gid`
- keep `name` and `description` if possible
- changing `value` is safe and often useful
- if a template has multiple requested date variables, preserve them all
- do not invent additional requested date entries unless the source template truly has them

### `import`

This block describes the intended import behavior.

Fields:

- `mode`
- `version_name_template`
- `source_template_gid`

#### `import.mode`

Current value:

- `create_new_versioned_template`

Meaning:

- import is expected to create a new template version instead of mutating the original template in place

Editing guidance:

- do not change this manually for now

#### `import.version_name_template`

Purpose:

- intended name for the next imported template version

Editing guidance:

- safe to edit
- recommended to update this intentionally before import

Examples:

- `Collaborative Development Task v2`
- `Collaborative Development Task v3`
- `Collaborative Development Task 2026-03-19`

Recommendation:

- choose a stable versioning scheme and keep it consistent within the repo

#### `import.source_template_gid`

Purpose:

- records which exported Asana template this edited file came from

Editing guidance:

- keep it
- normally this should match `template.source_gid`

### `instantiated_project`

This records metadata about the temporary project used during export.

Fields:

- `name`
- `source_gid`

Editing guidance:

- informational only
- keep it for traceability
- importer should not rely on this old temporary project still existing

## Sections

`sections` is an ordered array.

Order matters.

Each section object currently looks like:

```json
{
  "name": "Planning",
  "source_gid": "1213752650464445",
  "tasks": []
}
```

Field meaning:

- `name`: section title
- `source_gid`: gid of the exported section from the temporary instantiated project
- `tasks`: ordered task list

Editing guidance:

- section order is meaningful
- renaming a section is safe
- reordering sections should be supported by import
- adding a new section should be possible by creating a new object
- if you add a new section manually, omit `source_gid` or set it to `null`
- deleting a section should imply deleting or moving its tasks; do not leave orphaned tasks

## Tasks

Each section has an ordered `tasks` array.

Each task object currently looks like:

```json
{
  "name": "Implement the solution",
  "notes": "",
  "resource_subtype": "default_task",
  "source_gid": "1213752357302933",
  "dependency_source_gids": [
    "1213752357276236",
    "1213752357302918",
    "1213754562651541"
  ],
  "subtasks": []
}
```

Field meaning:

- `name`: task title
- `notes`: task notes/body
- `resource_subtype`: task type
- `source_gid`: exported task gid from the temporary instantiated project
- `dependency_source_gids`: predecessor task gids from the same exported graph
- `subtasks`: ordered subtask list

### Editable task fields

These are intended to be safely editable:

- `name`
- `notes`
- `resource_subtype`
- `subtasks`
- task order inside the section

### `resource_subtype`

Current examples:

- `default_task`
- `milestone`

Editing guidance:

- preserve valid Asana values
- avoid inventing unknown values
- if you are unsure, use `default_task`

### `source_gid`

Purpose:

- tracks which exported task this record came from

Editing guidance:

- preserve it for existing tasks
- for a brand new task you add manually, omit `source_gid` or set it to `null`
- do not reuse another task’s `source_gid`

### `dependency_source_gids`

This is the key dependency field.

Meaning:

- the current task depends on the tasks referenced by these gids
- each gid should refer to another task from the same exported template graph

If task `B` has:

```json
"dependency_source_gids": ["gid-of-A"]
```

that means:

- `A` must happen before `B`
- `B` is blocked by `A`

Editing guidance:

- use predecessor task `source_gid` values here
- keep the array flat
- do not put section gids here
- do not put template gids here
- do not put task names here
- do not put dependents here; this field is for dependencies only

Safe edits:

- add or remove dependency references between existing exported tasks
- preserve the exact gid strings when referencing exported tasks

Risky or currently experimental edits:

- adding dependencies that point to brand new tasks without `source_gid`
- adding dependencies that point to subtasks
- adding cross-template dependencies

Why this is tricky:

- importer must create all new tasks first
- only after new Asana task ids exist can it recreate dependency links
- existing exported tasks have `source_gid`, which gives us a stable reference bridge
- brand new tasks need an additional local identity mechanism before dependency recreation is fully reliable

Practical rule for now:

- dependencies between existing exported tasks are the safest case
- edits involving brand new tasks and dependencies are expected but still experimental until importer support is finished

## Subtasks

Each task has a `subtasks` array.

Each subtask currently uses the same core shape:

```json
{
  "name": "Write tests",
  "notes": "",
  "resource_subtype": "default_task",
  "source_gid": "1213759999999999",
  "dependency_source_gids": []
}
```

Editing guidance:

- subtask order is meaningful
- renaming and editing notes is safe
- for brand new subtasks, omit `source_gid` or set it to `null`

Important limitation:

- subtask dependency recreation is more experimental than top-level task dependency recreation
- if you need the first import tests to be low risk, keep dependency edits focused on top-level tasks first

## `unsectioned_tasks`

This is an ordered array for tasks that are not in a section.

Current templates may or may not use it.

Editing guidance:

- same task rules apply here
- avoid leaving a task duplicated both in `unsectioned_tasks` and inside a section

## Safe Editing Rules

These edits should be reasonable for the importer to support:

- rename the template
- change template description
- update `import.version_name_template`
- update requested date `value` fields
- rename sections
- reorder sections
- add a new section
- remove a section
- rename tasks
- reorder tasks inside a section
- move tasks between sections
- edit task notes
- change task `resource_subtype` between known values
- add or remove subtasks
- edit dependency relationships between existing exported tasks

## Risky or Experimental Edits

These may work later, but should be treated carefully:

- dependencies involving brand new tasks with no `source_gid`
- dependencies involving brand new subtasks
- changing `source_gid` values
- changing `workspace_gid`
- deleting requested date entries
- changing `format_version`
- creating malformed JSON

## How To Add New Content

### Add a new section

Example:

```json
{
  "name": "Launch",
  "source_gid": null,
  "tasks": []
}
```

### Add a new task

Example:

```json
{
  "name": "Prepare release notes",
  "notes": "",
  "resource_subtype": "default_task",
  "source_gid": null,
  "dependency_source_gids": [],
  "subtasks": []
}
```

### Add a dependency between existing exported tasks

If task `Implement the solution` should depend on `If bug, verify repeatable`, add the predecessor’s `source_gid` to the dependent task:

```json
{
  "name": "Implement the solution",
  "dependency_source_gids": [
    "1213752357276236",
    "1213752357302918",
    "1213754562651541"
  ]
}
```

The actual gids must match existing task `source_gid` values from the same file.

## How To Remove Content

### Remove a dependency

- delete the predecessor gid from `dependency_source_gids`

### Remove a task

- remove the task object from its array
- also remove its `source_gid` from any other task’s `dependency_source_gids`

This is important.

If you delete a task but leave its gid referenced elsewhere, import should either fail validation or produce broken dependency recreation.

### Remove a section

- remove the section object
- either remove its tasks too or move them somewhere else first
- clean up any dependency references if tasks were removed

## JSON Editing Hygiene

Before treating a modified file as importable:

- make sure the file is valid JSON
- make sure arrays and commas are correct
- make sure dependency gids are strings
- make sure every referenced dependency gid still exists somewhere in the same file unless you intentionally removed that dependency
- make sure new tasks do not accidentally copy another task’s `source_gid`

## Recommended LLM Editing Instructions

If you use an LLM to edit these files, give it rules like:

- preserve valid JSON
- preserve all existing `source_gid` values for existing objects
- do not invent new `source_gid` values
- set `source_gid` to `null` or omit it for newly created tasks and sections
- preserve `dependency_source_gids` unless intentionally changing dependencies
- if removing a task, also remove references to its gid from all `dependency_source_gids` arrays
- do not edit `format_version`
- do not use `outline.md` as the source of truth

## Current Import Assumptions

The planned importer is expected to work roughly like this:

1. Read `template.json`.
2. Instantiate or create a working project structure.
3. Create or update sections.
4. Create top-level tasks.
5. Create subtasks.
6. Recreate dependency links in a later pass after new task ids exist.
7. Save the result as a new versioned Asana template.

Because of that design, these fields are especially important:

- `template.workspace_gid`
- `template.requested_dates[*].gid`
- `template.requested_dates[*].value`
- `import.version_name_template`
- all existing task `source_gid` values
- all `dependency_source_gids` references

## Short Version

If you want the best chance of successful import:

- edit `template.json`, not `outline.md`
- keep existing `source_gid` values
- never invent new `source_gid` values
- use `null` or omit `source_gid` for new sections, tasks, and subtasks
- keep dependency references pointing at real task `source_gid` values in the same file
- when deleting a task, also delete any dependency references to it
- keep `format_version` unchanged
- update `import.version_name_template` intentionally before import
