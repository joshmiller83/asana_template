import unittest

from scripts.template_format import (
    FORMAT_VERSION,
    build_editable_template,
    build_requested_dates,
    render_outline,
    simplify_task,
)


class TemplateFormatTests(unittest.TestCase):
    def test_build_requested_dates_preserves_metadata_and_assigns_value(self) -> None:
        template = {
            "requested_dates": [
                {
                    "gid": "1",
                    "name": "Start Date",
                    "description": "Choose a start date.",
                }
            ]
        }

        requested_dates = build_requested_dates(template, "2026-03-19")

        self.assertEqual(
            requested_dates,
            [
                {
                    "gid": "1",
                    "name": "Start Date",
                    "description": "Choose a start date.",
                    "value": "2026-03-19",
                }
            ],
        )

    def test_build_editable_template_creates_managed_schema(self) -> None:
        template = {
            "gid": "template-1",
            "name": "Deployment Task",
            "description": "Template description",
            "team": {"gid": "workspace-1", "name": "My workspace"},
            "requested_dates": [{"gid": "1", "name": "Start Date", "value": "2026-03-19"}],
        }
        project = {"gid": "project-1", "name": "Deployment Task [export snapshot]"}
        sections = [
            {"gid": "section-1", "name": "Planning"},
            {"gid": "section-2", "name": "Execution"},
        ]
        tasks = [
            {
                "memberships": [{"section": {"gid": "section-1", "name": "Planning"}}],
                "editable_task": {
                    "name": "Define rollout",
                    "notes": "Capture steps",
                    "resource_subtype": "default_task",
                    "source_gid": "task-1",
                    "dependency_source_gids": ["task-0"],
                    "subtasks": [],
                },
            },
            {
                "memberships": [],
                "editable_task": {
                    "name": "Floating task",
                    "notes": "",
                    "resource_subtype": "milestone",
                    "source_gid": "task-2",
                    "dependency_source_gids": [],
                    "subtasks": [],
                },
            },
        ]

        editable = build_editable_template(template, project, sections, tasks)

        self.assertEqual(editable["format_version"], FORMAT_VERSION)
        self.assertEqual(editable["template"]["source_gid"], "template-1")
        self.assertEqual(editable["template"]["workspace_gid"], "workspace-1")
        self.assertEqual(editable["import"]["mode"], "create_new_versioned_template")
        self.assertEqual(editable["import"]["source_template_gid"], "template-1")
        self.assertEqual(editable["sections"][0]["tasks"][0]["name"], "Define rollout")
        self.assertEqual(editable["sections"][0]["tasks"][0]["source_gid"], "task-1")
        self.assertEqual(
            editable["sections"][0]["tasks"][0]["dependency_source_gids"],
            ["task-0"],
        )
        self.assertEqual(editable["unsectioned_tasks"][0]["name"], "Floating task")

    def test_simplify_task_keeps_only_managed_fields(self) -> None:
        task = {
            "gid": "task-1",
            "name": "Implement feature",
            "notes": "Do the work",
            "resource_subtype": "default_task",
            "dependencies": [{"gid": "task-0"}],
            "completed": False,
            "created_at": "ignored",
        }
        subtasks = [
            {
                "gid": "subtask-1",
                "name": "Write tests",
                "notes": "Before code",
                "resource_subtype": "default_task",
                "dependencies": [{"gid": "subtask-0"}],
                "completed": False,
            }
        ]

        simplified = simplify_task(task, subtasks)

        self.assertEqual(
            simplified,
            {
                "name": "Implement feature",
                "notes": "Do the work",
                "resource_subtype": "default_task",
                "source_gid": "task-1",
                "dependency_source_gids": ["task-0"],
                "subtasks": [
                    {
                        "name": "Write tests",
                        "notes": "Before code",
                        "resource_subtype": "default_task",
                        "source_gid": "subtask-1",
                        "dependency_source_gids": ["subtask-0"],
                    }
                ],
            },
        )

    def test_render_outline_includes_import_metadata(self) -> None:
        editable = {
            "format_version": FORMAT_VERSION,
            "export_strategy": "instantiate_project_template",
            "template": {
                "name": "Collaborative Development Task",
                "source_gid": "template-1",
                "requested_dates": [{"name": "Start Date", "value": "2026-03-19"}],
                "description": "",
            },
            "import": {
                "mode": "create_new_versioned_template",
                "version_name_template": "Collaborative Development Task vNEXT",
            },
            "instantiated_project": {"source_gid": "project-1"},
            "sections": [
                {
                    "name": "Planning",
                    "tasks": [
                        {
                            "name": "Define scope",
                            "source_gid": "task-1",
                            "dependency_source_gids": ["task-0"],
                            "notes": "",
                            "subtasks": [],
                        }
                    ],
                }
            ],
            "unsectioned_tasks": [],
        }

        outline = render_outline(editable)

        self.assertIn("source_template_gid: `template-1`", outline)
        self.assertIn("next_version_name: `Collaborative Development Task vNEXT`", outline)
        self.assertIn("## Planning", outline)
        self.assertIn("- Define scope", outline)
        self.assertIn("depends_on_source_gids: `task-0`", outline)


if __name__ == "__main__":
    unittest.main()
