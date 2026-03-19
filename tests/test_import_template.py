import tempfile
import unittest
from pathlib import Path

from scripts.import_template import (
    collect_known_task_source_gids,
    load_template,
    resolve_import_workspace_gid,
    validate_template_for_import,
)


class ImportTemplateTests(unittest.TestCase):
    def test_collect_known_task_source_gids_includes_tasks_and_subtasks(self) -> None:
        template_data = {
            "sections": [
                {
                    "tasks": [
                        {
                            "source_gid": "task-1",
                            "subtasks": [
                                {"source_gid": "subtask-1"},
                                {"source_gid": None},
                            ],
                        }
                    ]
                }
            ],
            "unsectioned_tasks": [{"source_gid": "task-2", "subtasks": []}],
        }

        self.assertEqual(
            collect_known_task_source_gids(template_data),
            {"task-1", "subtask-1", "task-2"},
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


if __name__ == "__main__":
    unittest.main()
