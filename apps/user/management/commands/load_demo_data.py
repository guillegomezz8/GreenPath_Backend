import json
import re
from collections import Counter
from datetime import date, datetime, time, timedelta
from pathlib import Path

from django.apps import apps
from django.contrib.auth.hashers import make_password
from django.contrib.gis.geos import GEOSGeometry
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.utils import timezone


FIXTURE_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "demo_datos.json"
ALLOWED_MODELS = {
    "user.user", "user.worker", "user.client", "company.company",
    "company.companysettings", "company.companyhub", "zone.zone", "truck.truck",
    "route.route", "route.routezoneday", "route.routeday", "route.routedayclient",
    "collection.collection", "collection.collectionrequest", "wholesale.bulkcollection",
    "sale.buyer", "sale.sale", "sale.saleline",
}


class Command(BaseCommand):
    help = "Carga una empresa demo desde JSON sin modificar datos existentes."

    def add_arguments(self, parser):
        parser.add_argument("--fixture", type=Path, default=FIXTURE_PATH)
        parser.add_argument("--namespace", default="demo-clientes")
        parser.add_argument("--owner-email", default="propietario@demo.com",
                            help="Email y usuario de acceso del propietario demo.")
        parser.add_argument("--password", default="pass12345")
        parser.add_argument("--date", type=date.fromisoformat, default=None,
                            help="Fecha de referencia YYYY-MM-DD (por defecto hoy).")
        parser.add_argument("--dry-run", action="store_true",
                            help="Valida la carga y revierte todos los cambios.")

    def handle(self, *args, **options):
        namespace = options["namespace"]
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,12}", namespace):
            raise CommandError("Namespace: 1-13 letras minusculas, numeros o guiones.")
        if not options["password"]:
            raise CommandError("La contrasena demo no puede estar vacia.")
        self.configure_owner(options)
        try:
            dataset = json.loads(options["fixture"].read_text(encoding="utf-8"))
            records = self.validate_dataset(dataset)
        except (OSError, ValueError, TypeError, FieldDoesNotExist) as exc:
            raise CommandError(f"JSON demo invalido: {exc}") from exc

        self.namespace = namespace
        self.reference_date = options["date"] or timezone.localdate()
        self.objects = {}
        self.password_hash = make_password(options["password"])
        counts = Counter()
        try:
            with transaction.atomic():
                if self.already_loaded(records):
                    self.stdout.write("La empresa demo ya existe; no se ha modificado ningun dato.")
                    return
                for record in records:
                    self.create_record(record)
                    counts[record["model"]] += 1
                # Solo se modifica la empresa creada en esta transaccion.
                company = self.objects["company"]
                company.owner = self.objects["owner"]
                company.save(update_fields=["owner"])
                if options["dry_run"]:
                    transaction.set_rollback(True)
        except (ValidationError, IntegrityError, ValueError, TypeError, KeyError) as exc:
            raise CommandError(f"Carga cancelada; no se ha guardado ningun dato: {exc}") from exc

        mode = "Simulacion validada (sin guardar)" if options["dry_run"] else "Demo creada"
        self.stdout.write(self.style.SUCCESS(f"{mode}: {sum(counts.values())} registros del JSON."))
        for label, count in sorted(counts.items()):
            self.stdout.write(f"  {label}: {count}")
        self.stdout.write(f"Empresa: {self.objects['company'].name}")
        self.stdout.write(f"Owner: {self.objects['owner'].username}")
        self.stdout.write(f"Worker: {self.objects['worker-user-1'].username}" if "worker-user-1" in self.objects else "")
        self.stdout.write(f"Client: {self.objects['client-user-1'].username}" if "client-user-1" in self.objects else "")
        self.stdout.write("Contrasena: la indicada en --password (por defecto pass12345).")

    def configure_owner(self, options):
        self.owner_email = options["owner_email"].strip()
        try:
            validate_email(self.owner_email)
        except ValidationError as exc:
            raise CommandError("--owner-email debe ser un email valido.") from exc

    def validate_dataset(self, dataset):
        if not isinstance(dataset, dict) or dataset.get("version") != 1:
            raise ValueError("Se requiere un objeto con version=1.")
        records = dataset.get("records")
        if not isinstance(records, list) or not records:
            raise ValueError("records debe ser una lista no vacia.")
        keys = set()
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("Cada registro debe ser un objeto.")
            key, label = record.get("key"), record.get("model")
            if not isinstance(key, str) or not key or key in keys:
                raise ValueError(f"Clave ausente o duplicada: {key}.")
            keys.add(key)
            if label not in ALLOWED_MODELS:
                raise ValueError(f"Modelo no permitido: {label}.")
            fields = record.get("fields")
            if not isinstance(fields, dict):
                raise ValueError(f"fields invalido en {key}.")
            model = apps.get_model(label)
            for name in fields:
                field = model._meta.get_field(name)
                if field.primary_key or name in {"password", "is_staff", "is_superuser", "owner"}:
                    raise ValueError(f"Campo no permitido: {key}.{name}.")
        by_key = {record["key"]: record for record in records}
        if by_key.get("owner", {}).get("model") != "user.user":
            raise ValueError("Falta el usuario owner.")
        if by_key.get("company", {}).get("model") != "company.company":
            raise ValueError("Falta la empresa company.")
        return records

    def already_loaded(self, records):
        by_key = {record["key"]: record for record in records}
        company_name = self.resolve(by_key["company"]["fields"]["name"])
        companies = apps.get_model("company.company").objects.filter(name=company_name)
        if not companies.exists():
            return False
        if companies.count() != 1:
            raise ValueError("Nombre de empresa demo ambiguo.")
        company = companies.select_for_update().get()
        owner = company.owner
        settings = getattr(company, "settings", None)
        if (owner is None or owner.role_type != "owner"
                or owner.worker_profile.company_id != company.pk
                or settings is None or not settings.billing_footer.startswith("DEMOSTRACION:")):
            raise ValueError("La empresa existente no corresponde a una demo reconocida.")
        if owner.username not in {self.owner_email, f"{self.namespace}-owner"} or owner.email != self.owner_email:
            raise ValueError("La demo ya existe con otro acceso; indica su --owner-email. No se modifica ninguna cuenta existente.")
        return True

    def resolve(self, value):
        if isinstance(value, str):
            return value.replace("{namespace}", self.namespace).replace("{owner_email}", self.owner_email)
        if isinstance(value, dict):
            if set(value) == {"ref"}:
                return self.objects[value["ref"]]
            if set(value) == {"date_offset"}:
                return self.reference_date + timedelta(days=value["date_offset"])
            if set(value) == {"datetime_offset", "hour"}:
                day = self.reference_date + timedelta(days=value["datetime_offset"])
                return timezone.make_aware(datetime.combine(day, time(value["hour"])))
            raise ValueError(f"Valor simbolico desconocido: {value}")
        return value

    def create_record(self, record):
        model = apps.get_model(record["model"])
        values, many = {}, {}
        for name, value in record["fields"].items():
            field = model._meta.get_field(name)
            if field.many_to_many:
                related = [self.resolve(item) for item in value]
                if any(not isinstance(item, field.related_model) for item in related):
                    raise ValueError(f"{record['key']}.{name}: se requieren referencias nuevas.")
                many[name] = related
                continue
            resolved = self.resolve(value)
            if field.is_relation and resolved is not None and not isinstance(resolved, field.related_model):
                raise ValueError(f"{record['key']}.{name}: se requiere ref a un registro nuevo.")
            if hasattr(field, "geom_type") and resolved is not None:
                resolved = GEOSGeometry(resolved, srid=4326)
            elif not field.is_relation:
                resolved = field.to_python(resolved)
            values[name] = resolved
        obj = model(**values)
        if record["model"] == "user.user":
            obj.password = self.password_hash
        # Collection/BulkCollection/SaleLine recalculan sus campos derivados en save.
        if record["model"] not in {"collection.collection", "wholesale.bulkcollection", "sale.sale", "sale.saleline"}:
            obj.full_clean()
        obj.save()
        for name, related in many.items():
            getattr(obj, name).set(related)
        self.objects[record["key"]] = obj
