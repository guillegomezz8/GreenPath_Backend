from decimal import Decimal

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("company", "0008_companysettings_collections_enabled_and_more")]

    operations = [
        migrations.RenameField("CompanySettings", "wholesale_purchases_enabled", "bulk_collections_enabled"),
        migrations.RenameField("HistoricalCompanySettings", "wholesale_purchases_enabled", "bulk_collections_enabled"),
        migrations.AddField(
            model_name="companysettings",
            name="oil_density_kg_per_liter",
            field=models.DecimalField(decimal_places=4, default=Decimal("0.9200"), max_digits=7, validators=[django.core.validators.MinValueValidator(Decimal("0.0001"))], verbose_name="Densidad del aceite (kg/L)"),
        ),
        migrations.AddField(
            model_name="companysettings",
            name="liters_per_unit",
            field=models.DecimalField(decimal_places=4, default=Decimal("1.0000"), max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal("0.0001"))], verbose_name="Equivalencia por unidad (L/ud)"),
        ),
        migrations.AddField(
            model_name="historicalcompanysettings",
            name="oil_density_kg_per_liter",
            field=models.DecimalField(decimal_places=4, default=Decimal("0.9200"), max_digits=7, validators=[django.core.validators.MinValueValidator(Decimal("0.0001"))], verbose_name="Densidad del aceite (kg/L)"),
        ),
        migrations.AddField(
            model_name="historicalcompanysettings",
            name="liters_per_unit",
            field=models.DecimalField(decimal_places=4, default=Decimal("1.0000"), max_digits=10, validators=[django.core.validators.MinValueValidator(Decimal("0.0001"))], verbose_name="Equivalencia por unidad (L/ud)"),
        ),
    ]
