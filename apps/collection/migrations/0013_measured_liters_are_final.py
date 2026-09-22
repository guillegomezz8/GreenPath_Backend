from decimal import Decimal

import django.core.validators
from django.db import migrations, models


ZERO = Decimal("0.00")


def use_final_measured_liters(apps, schema_editor):
    for model_name in ("Collection", "HistoricalCollection"):
        model = apps.get_model("collection", model_name)
        for collection in model.objects.exclude(measured_liters__isnull=True).iterator():
            final_liters = collection.net_liters
            deduction_liters = max(ZERO, collection.estimated_liters - final_liters)
            collection.measured_liters = final_liters
            collection.deduction_liters = deduction_liters
            if deduction_liters > ZERO and not collection.deduction_reason:
                collection.deduction_reason = "OTHER"
            elif deduction_liters == ZERO:
                collection.deduction_reason = ""
            collection.save(
                update_fields=["measured_liters", "deduction_liters", "deduction_reason"]
            )


def restore_gross_measured_liters(apps, schema_editor):
    for model_name in ("Collection", "HistoricalCollection"):
        model = apps.get_model("collection", model_name)
        for collection in model.objects.exclude(measured_liters__isnull=True).iterator():
            final_liters = collection.measured_liters
            collection.net_liters = final_liters
            collection.measured_liters = final_liters + collection.deduction_liters
            collection.save(update_fields=["measured_liters", "net_liters"])


class Migration(migrations.Migration):
    dependencies = [
        ("collection", "0012_collection_deduction_reason_optional"),
    ]

    operations = [
        migrations.RunPython(use_final_measured_liters, restore_gross_measured_liters),
        migrations.AlterField(
            model_name="collection",
            name="measured_liters",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
                verbose_name="Litros medidos finales",
            ),
        ),
        migrations.AlterField(
            model_name="historicalcollection",
            name="measured_liters",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
                verbose_name="Litros medidos finales",
            ),
        ),
        migrations.RemoveField(
            model_name="collection",
            name="net_liters",
        ),
        migrations.RemoveField(
            model_name="historicalcollection",
            name="net_liters",
        ),
    ]
