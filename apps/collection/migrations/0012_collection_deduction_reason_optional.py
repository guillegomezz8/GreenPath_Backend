from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("collection", "0011_alter_collection_created_date_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="collection",
            name="deduction_reason",
            field=models.CharField(
                blank=True,
                choices=[
                    ("WATER", "Agua"),
                    ("RESIDUE", "Residuos/posos"),
                    ("MIXED", "Mezcla/impurezas"),
                    ("OTHER", "Otros"),
                ],
                default="",
                max_length=20,
                verbose_name="Motivo descuento",
            ),
        ),
        migrations.AlterField(
            model_name="historicalcollection",
            name="deduction_reason",
            field=models.CharField(
                blank=True,
                choices=[
                    ("WATER", "Agua"),
                    ("RESIDUE", "Residuos/posos"),
                    ("MIXED", "Mezcla/impurezas"),
                    ("OTHER", "Otros"),
                ],
                default="",
                max_length=20,
                verbose_name="Motivo descuento",
            ),
        ),
    ]
