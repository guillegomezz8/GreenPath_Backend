from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("wholesale", "0002_remove_historicalwholesalepurchase_description_and_more")]

    operations = [
        migrations.RenameModel("WholesalePurchase", "BulkCollection"),
        migrations.RenameModel("HistoricalWholesalePurchase", "HistoricalBulkCollection"),
        migrations.RenameField("BulkCollection", "purchase_date", "collection_date"),
        migrations.RenameField("HistoricalBulkCollection", "purchase_date", "collection_date"),
        migrations.AlterModelOptions(
            name="bulkcollection",
            options={
                "ordering": ("-collection_date", "-id"),
                "verbose_name": "Recogida al por mayor",
                "verbose_name_plural": "Recogidas al por mayor",
            },
        ),
        migrations.AlterField(
            model_name="bulkcollection",
            name="invoice_file",
            field=models.FileField(blank=True, null=True, upload_to="bulk_collections/invoices/", verbose_name="Factura adjunta"),
        ),
    ]
