import json
from datetime import datetime
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core import serializers
from django.core.management.base import BaseCommand, CommandError


BUSINESS_APP_LABELS = (
    "user",
    "company",
    "truck",
    "zone",
    "route",
    "collection",
    "sale",
)


def _business_models(excluded_labels):
    models = []
    for app_label in BUSINESS_APP_LABELS:
        app_config = apps.get_app_config(app_label)
        for model in app_config.get_models():
            model_label = model._meta.label_lower
            if (
                model_label in excluded_labels
                or model._meta.auto_created
                or model._meta.proxy
                or model._meta.model_name.startswith("historical")
            ):
                continue
            models.append(model)
    return models


def _models_in_dependency_order(models):
    model_set = set(models)
    dependencies = {model: set() for model in models}

    for model in models:
        for field in (*model._meta.fields, *model._meta.local_many_to_many):
            related_model = getattr(field.remote_field, "model", None)
            if related_model in model_set and related_model is not model:
                dependencies[model].add(related_model)

    ordered = []
    pending = set(models)
    while pending:
        ready = sorted(
            (
                model
                for model in pending
                if not (dependencies[model] & pending)
            ),
            key=lambda model: model._meta.label_lower,
        )
        if not ready:
            ready = [min(pending, key=lambda model: model._meta.label_lower)]
        for model in ready:
            pending.remove(model)
            ordered.append(model)
    return ordered


class Command(BaseCommand):
    help = (
        "Exporta los datos propios de GreenPath a un fixture JSON, "
        "sin tablas internas, tokens ni historicos de Django."
    )

    def add_arguments(self, parser):
        default_name = f"greenpath_export_{datetime.now():%Y%m%d_%H%M%S}.json"
        parser.add_argument(
            "--output",
            "-o",
            default=str(Path(settings.BASE_DIR) / "exports" / default_name),
            help="Ruta del archivo JSON de salida.",
        )
        parser.add_argument(
            "--indent",
            type=int,
            default=4,
            help="Numero de espacios de indentacion (por defecto: 4).",
        )
        parser.add_argument(
            "--exclude",
            action="append",
            default=[],
            metavar="APP.MODEL",
            help="Modelo propio que se desea omitir. Se puede repetir.",
        )

    def handle(self, *args, **options):
        output_path = Path(options["output"]).expanduser().resolve()
        indent = options["indent"]
        excluded_labels = {label.lower() for label in options["exclude"]}

        if indent < 0:
            raise CommandError("--indent no puede ser negativo.")

        models = _models_in_dependency_order(
            _business_models(excluded_labels)
        )
        exported_rows = []
        counts = {}

        for model in models:
            queryset = model._default_manager.all().order_by(model._meta.pk.name)
            rows = json.loads(
                serializers.serialize(
                    "json",
                    queryset.iterator(chunk_size=500),
                    use_natural_foreign_keys=False,
                    use_natural_primary_keys=False,
                )
            )
            for row in rows:
                if row["model"] == "user.user":
                    row["fields"].pop("groups", None)
                    row["fields"].pop("user_permissions", None)
            exported_rows.extend(rows)
            counts[model._meta.label_lower] = len(rows)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(exported_rows, ensure_ascii=False, indent=indent),
            encoding="utf-8",
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Exportacion completada: {output_path} "
                f"({len(exported_rows)} registros, {len(counts)} modelos)."
            )
        )
        self.stdout.write(
            "Modelos exportados: "
            + ", ".join(
                f"{label}={count}" for label, count in counts.items()
            )
        )
