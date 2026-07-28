import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase

from apps.base.test_utils import BackendTestMixin


class ExportGreenPathCommandTests(BackendTestMixin, TestCase):
    def test_export_contains_only_business_models(self):
        self.create_owner_context("export")

        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "greenpath.json"
            call_command(
                "export_greenpath",
                output=str(output_path),
                verbosity=0,
            )
            rows = json.loads(output_path.read_text(encoding="utf-8"))

        model_labels = {row["model"] for row in rows}
        self.assertIn("user.user", model_labels)
        self.assertIn("company.company", model_labels)
        self.assertFalse(any(label.startswith("auth.") for label in model_labels))
        self.assertFalse(any(label.startswith("sessions.") for label in model_labels))
        self.assertFalse(any("historical" in label for label in model_labels))
        user_row = next(row for row in rows if row["model"] == "user.user")
        self.assertNotIn("groups", user_row["fields"])
        self.assertNotIn("user_permissions", user_row["fields"])
