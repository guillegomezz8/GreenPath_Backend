import json
import re
from collections import Counter
from datetime import timedelta

from django.apps import apps
from django.contrib.gis.geos import GEOSGeometry
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.user.management.commands.load_demo_data import Command as LoadCommand


class Command(LoadCommand):
    help = "Actualiza fechas, importes y actividad exclusivamente de una empresa demo cargada."
    mutable_models = {
        "collection.collection", "wholesale.bulkcollection", "sale.sale",
        "sale.saleline", "route.routeday", "collection.collectionrequest",
    }

    def handle(self, *args, **options):
        self.configure_owner(options)
        self.namespace = options["namespace"]
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,12}", self.namespace):
            raise CommandError("Namespace invalido.")
        try:
            records = self.validate_dataset(json.loads(options["fixture"].read_text(encoding="utf-8")))
            self.objects = {}
            self.reference_date = options["date"] or timezone.localdate()
            with transaction.atomic():
                if not self.already_loaded(records):
                    raise ValueError("La empresa demo aun no esta cargada.")
                # Conserva la referencia usada al crear la demo, aunque se ejecute otro dia.
                route_model = apps.get_model("route.route")
                original_route = route_model.objects.get(name=f"{self.namespace} - Ruta 1")
                self.reference_date = options["date"] or original_route.start_date + timedelta(days=365)
                counts = Counter()
                for record in records:
                    obj = self.find_record(record)
                    if record["model"] in self.mutable_models:
                        if obj is None:
                            if not record["key"].startswith("recent-"):
                                raise ValueError(f"Falta el registro demo {record['key']}; no se modificara otra fila.")
                            self.create_record(record)
                            obj = self.objects[record["key"]]
                        else:
                            self.update_record(obj, record)
                        counts[record["model"]] += 1
                    elif obj is None:
                        raise ValueError(f"Falta el registro demo {record['key']}.")
                    self.objects[record["key"]] = obj
                if options["dry_run"]:
                    transaction.set_rollback(True)
        except (OSError, ValueError, KeyError, TypeError, FieldDoesNotExist, ValidationError, IntegrityError,
                apps.get_model("route.route").DoesNotExist) as exc:
            raise CommandError(f"Actualizacion revertida: {exc}") from exc
        message = "Simulacion sin guardar" if options["dry_run"] else "Demo actualizada"
        self.stdout.write(self.style.SUCCESS(f"{message}: {sum(counts.values())} registros de actividad."))

    def find_record(self, record):
        label, fields = record["model"], record["fields"]
        model = apps.get_model(label)
        values = {name: self.resolve(value) for name, value in fields.items()
                  if not model._meta.get_field(name).many_to_many}
        company = self.objects.get("company")
        if label == "user.user":
            query = {"username": values["username"], "email": values["email"]}
        elif label == "company.company":
            query = {"owner": self.objects["owner"], "name": values["name"]}
        elif label in {"company.companysettings", "company.companyhub"}:
            query = {"company": company}
        elif label in {"user.worker", "user.client"}:
            query = {"user": values["user"]}
            if label == "user.worker":
                query["company"] = company
            else:
                query["companies"] = company
        elif label == "zone.zone":
            query = {"company": company, "name": values["name"]}
        elif label == "truck.truck":
            query = {"company": company, "registration_number": values["registration_number"]}
        elif label == "route.route":
            query = {"company": company, "name": values["name"]}
        elif label == "route.routezoneday":
            query = {"route": values["route"], "weekday": values["weekday"]}
        elif label == "route.routeday":
            query = {"route": values["route"], "date": values["date"]}
        elif label == "route.routedayclient":
            query = {"route_day": values["route_day"], "client": values["client"]}
        elif label == "collection.collectionrequest":
            query = {"route_day_client": values["route_day_client"]}
        elif label == "sale.buyer":
            query = {"company": company, "tax_id": values["tax_id"]}
        elif label == "sale.sale":
            query = {"company": company, "invoice_number": values["invoice_number"]}
        elif label == "sale.saleline":
            query = {"sale": values["sale"], "position": values["position"]}
        elif label == "collection.collection" and values.get("route_day_client"):
            query = {"route_day_client": values["route_day_client"]}
        else:
            marker = f"[demo:{self.namespace}:{record['key']}]"
            scope = {"worker__company": company} if label == "collection.collection" else {"company": company}
            marked = model.objects.filter(**scope, notes__contains=marker)
            if marked.count() == 1:
                return marked.get()
            if marked.exists():
                raise ValueError(f"Marcador duplicado: {record['key']}")
            if record["key"].startswith("recent-"):
                return None
            query = {**scope, "client": values["client"],
                     "collection_date": self.resolve(record["lookup"]["collection_date"]),
                     "notes": record["lookup"]["notes"]}
            if label == "collection.collection":
                query.update(worker=values["worker"], route_day_client__isnull=True)
        matches = model.objects.filter(**query).distinct()
        if matches.count() > 1:
            raise ValueError(f"Registro ambiguo: {record['key']}")
        return matches.first()

    def update_record(self, obj, record):
        for name, value in record["fields"].items():
            field = obj._meta.get_field(name)
            value = self.resolve(value)
            if hasattr(field, "geom_type") and value is not None:
                value = GEOSGeometry(value, srid=4326)
            elif not field.is_relation:
                value = field.to_python(value)
            setattr(obj, name, value)
        if record["model"] in {"route.routeday", "collection.collectionrequest"}:
            obj.full_clean()
        obj.save()
