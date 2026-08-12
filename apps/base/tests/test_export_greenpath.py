import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase

from apps.base.tests.helpers import BackendTestMixin
from apps.sale.models import Sale, SaleLine


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

    def test_export_contains_sales_with_lines_and_invoice_issuer_snapshot(self):
        _, _, company = self.create_owner_context("export-sales")
        buyer = self.create_buyer(
            company,
            fiscal_name="EXPORT COMPRADOR S.L.",
            tax_id="B90909090",
        )
        sale = Sale.objects.create(
            company=company,
            buyer=buyer,
            sale_date=date(2026, 8, 12),
            invoice_date=date(2026, 8, 12),
            invoice_number="099/2026",
            product_description="Concepto exportado",
            quantity=Decimal("10.00"),
            unit="kg",
            unit_price=Decimal("2.00"),
            tax_rate=Decimal("21.00"),
            currency="EUR",
        )
        SaleLine.objects.create(
            sale=sale,
            position=0,
            product_description="Linea exportada",
            quantity=Decimal("10.00"),
            unit="kg",
            unit_price=Decimal("2.00"),
            tax_rate=Decimal("21.00"),
        )
        sale.refresh_from_db()

        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "greenpath.json"
            call_command(
                "export_greenpath",
                output=str(output_path),
                verbosity=0,
            )
            rows = json.loads(output_path.read_text(encoding="utf-8"))

        snapshot_row = next(
            row
            for row in rows
            if row["model"] == "sale.saleinvoiceissuersnapshot"
            and row["pk"] == sale.invoice_issuer_id
        )
        sale_row = next(
            row
            for row in rows
            if row["model"] == "sale.sale" and row["pk"] == sale.pk
        )
        line_row = next(
            row
            for row in rows
            if row["model"] == "sale.saleline" and row["fields"]["sale"] == sale.pk
        )

        self.assertEqual(sale_row["fields"]["invoice_issuer"], snapshot_row["pk"])
        self.assertEqual(line_row["fields"]["product_description"], "Linea exportada")
