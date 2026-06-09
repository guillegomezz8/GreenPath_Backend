import django.db.models.deletion
from django.db import migrations, models


def assign_zones_to_companies(apps, schema_editor):
    Company = apps.get_model("company", "Company")
    RouteZoneDay = apps.get_model("route", "RouteZoneDay")
    Zone = apps.get_model("zone", "Zone")
    zone_through = RouteZoneDay._meta.get_field("zones").remote_field.through

    company_ids = list(Company.objects.order_by("id").values_list("id", flat=True))
    if not company_ids and Zone.objects.exists():
        raise RuntimeError("No se pueden migrar zonas sin una empresa existente.")

    for zone in Zone.objects.order_by("id"):
        route_company_ids = list(
            RouteZoneDay.objects.filter(zones=zone)
            .order_by("route__company_id")
            .values_list("route__company_id", flat=True)
            .distinct()
        )
        target_company_ids = route_company_ids or company_ids
        if not target_company_ids:
            continue

        zone.company_id = target_company_ids[0]
        zone.save(update_fields=["company"])

        for company_id in target_company_ids[1:]:
            company_zone = Zone.objects.create(
                company_id=company_id,
                name=zone.name,
                polygon=zone.polygon,
                disabled=zone.disabled,
            )
            zone_through.objects.filter(
                routezoneday__route__company_id=company_id,
                zone_id=zone.id,
            ).update(zone_id=company_zone.id)


class Migration(migrations.Migration):

    dependencies = [
        ("company", "0007_alter_company_created_date_and_more"),
        ("route", "0011_alter_historicalroute_created_date_and_more"),
        ("zone", "0003_alter_historicalzone_created_date_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="zone",
            name="name",
            field=models.CharField(max_length=100, verbose_name="Nombre de la zona"),
        ),
        migrations.AlterField(
            model_name="historicalzone",
            name="name",
            field=models.CharField(max_length=100, verbose_name="Nombre de la zona"),
        ),
        migrations.AddField(
            model_name="zone",
            name="company",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="zones",
                to="company.company",
                verbose_name="Empresa",
            ),
        ),
        migrations.AddField(
            model_name="historicalzone",
            name="company",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to="company.company",
                verbose_name="Empresa",
            ),
        ),
        migrations.RunPython(assign_zones_to_companies, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="zone",
            name="company",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="zones",
                to="company.company",
                verbose_name="Empresa",
            ),
        ),
        migrations.AddConstraint(
            model_name="zone",
            constraint=models.UniqueConstraint(
                fields=("company", "name"),
                name="uniq_zone_name_per_company",
            ),
        ),
    ]
