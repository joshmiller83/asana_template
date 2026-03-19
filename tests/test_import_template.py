import tempfile
import unittest
from pathlib import Path

from scripts.import_template import (
    collect_known_task_refs,
    dependency_refs_for_task,
    load_template,
    resolve_import_workspace_gid,
    task_reference_keys,
    validate_template_for_import,
)


class ImportTemplateTests(unittest.TestCase):
    def test_collect_known_task_refs_includes_source_gids_local_ids_and_subtasks(self) -> None:
        template_data = {
            "sections": [
                {
                    "tasks": [
                        {
                            "source_gid": "task-1",
                            "local_id": "local-task-1",
                            "subtasks": [
                                {"source_gid": "subtask-1"},
                                {"local_id": "local-subtask-1"},
                            ],
                        }
                    ]
                }
            ],
            "unsectioned_tasks": [{"source_gid": "task-2", "subtasks": []}],
        }

        self.assertEqual(
            collect_known_task_refs(template_data),
            {"task-1", "local-task-1", "subtask-1", "local-subtask-1", "task-2"},
        )

    def test_validate_template_for_import_rejects_missing_dependency_target(self) -> None:
        template_data = {
            "format_version": 1,
            "template": {"workspace_gid": "workspace-1"},
            "import": {"version_name_template": "Deployment Task v2"},
            "sections": [
                {
                    "name": "Planning",
                    "tasks": [
                        {
                            "name": "Task A",
                            "source_gid": "task-a",
                            "dependency_source_gids": ["missing-task"],
                            "subtasks": [],
                        }
                    ],
                }
            ],
            "unsectioned_tasks": [],
        }

        errors = validate_template_for_import(template_data)

        self.assertEqual(len(errors), 1)
        self.assertIn("missing-task", errors[0])

    def test_validate_template_for_import_accepts_new_task_without_source_gid(self) -> None:
        template_data = {
            "format_version": 1,
            "template": {"workspace_gid": "workspace-1"},
            "import": {"version_name_template": "Deployment Task v2"},
            "sections": [
                {
                    "name": "Monitoring",
                    "tasks": [
                        {
                            "name": "New task",
                            "source_gid": None,
                            "dependency_source_gids": [],
                            "subtasks": [],
                        }
                    ],
                }
            ],
            "unsectioned_tasks": [],
        }

        self.assertEqual(validate_template_for_import(template_data), [])

    def test_load_template_reads_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "template.json"
            path.write_text('{"format_version": 1}')
            data = load_template(path)

        self.assertEqual(data["format_version"], 1)

    def test_resolve_import_workspace_gid_falls_back_by_name(self) -> None:
        template_data = {
            "template": {
                "workspace_gid": "team-like-gid",
                "workspace_name": "My workspace",
            }
        }

        from unittest.mock import patch

        with patch(
            "scripts.import_template.paginate",
            return_value=[{"gid": "real-workspace-gid", "name": "My workspace"}],
        ):
            resolved = resolve_import_workspace_gid("token", template_data)

        self.assertEqual(resolved, "real-workspace-gid")

    def test_task_reference_keys_prefers_both_source_gid_and_local_id(self) -> None:
        task = {"source_gid": "task-1", "local_id": "local-1"}
        self.assertEqual(task_reference_keys(task), ["task-1", "local-1"])

    def test_dependency_refs_for_task_supports_new_field(self) -> None:
        task = {"dependency_refs": ["local-a", "local-b"]}
        self.assertEqual(dependency_refs_for_task(task), ["local-a", "local-b"])

    def test_validate_template_for_import_accepts_local_id_dependencies_for_v1(self) -> None:
        template_data = {
            "format_version": 1,
            "template": {"workspace_gid": "workspace-1"},
            "import": {"version_name_template": "Management Planning Task v1"},
            "sections": [
                {
                    "name": "Planning",
                    "tasks": [
                        {
                            "name": "First task",
                            "local_id": "first-task",
                            "dependency_refs": [],
                            "subtasks": [],
                        },
                        {
                            "name": "Second task",
                            "local_id": "second-task",
                            "dependency_refs": ["first-task"],
                            "subtasks": [],
                        },
                    ],
                }
            ],
            "unsectioned_tasks": [],
        }

        self.assertEqual(validate_template_for_import(template_data), [])

    def test_validate_template_for_import_rejects_duplicate_local_ids(self) -> None:
        template_data = {
            "format_version": 1,
            "template": {"workspace_gid": "workspace-1"},
            "import": {"version_name_template": "Management Planning Task v1"},
            "sections": [
                {
                    "name": "Planning",
                    "tasks": [
                        {
                            "name": "Task A",
                            "local_id": "dup",
                            "dependency_refs": [],
                            "subtasks": [],
                        },
                        {
                            "name": "Task B",
                            "local_id": "dup",
                            "dependency_refs": [],
                            "subtasks": [],
                        },
                    ],
                }
            ],
            "unsectioned_tasks": [],
        }

        errors = validate_template_for_import(template_data)
        self.assertEqual(len(errors), 1)
        self.assertIn("reuses identifier", errors[0])


if __name__ == "__main__":
    unittest.main()
