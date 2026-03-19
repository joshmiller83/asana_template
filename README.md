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
