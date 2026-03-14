from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError
from django.core.exceptions import ImproperlyConfigured

import json
import logging
from pathlib import Path

from apps.base.logger import configure_logging
 
configure_logging()
 
 
class Command(BaseCommand):
    help = 'Load scheduled tasks from celery_tasks.json into Celery Beat'
 
    def handle(self, *args, **kwargs):
        logging.info("[celery_load_tasks - handle] Iniciando carga de tareas desde celery_tasks.json")
        try:
            json_path = Path(settings.CELERY_DIR) / 'celery_tasks.json'
 
            if not json_path.exists():
                self.stdout.write(self.style.WARNING("Archivo celery_tasks.json no encontrado, omitiendo carga de tareas."))
                logging.warning("[celery_load_tasks - handle] Archivo celery_tasks.json no encontrado, omitiendo carga de tareas.")
                return
 
            with json_path.open('r', encoding='utf-8') as file:
                data = json.load(file)
 
            for task_data in data.get("tareas", []):
                schedule_data = task_data.get("schedule", {})
                schedule_type = schedule_data.get("type")
 
                schedule = None
                if schedule_type == "crontab":
                    schedule, _ = CrontabSchedule.objects.get_or_create(
                        minute=schedule_data["minute"],
                        hour=schedule_data["hour"],
                        day_of_week=schedule_data["day_of_week"],
                        day_of_month=schedule_data["day_of_month"],
                        month_of_year=schedule_data["month_of_year"],
                        timezone="UTC"
                    )
                    logging.info(f"[celery_load_tasks - handle] Horario creado o encontrado: {schedule}")
 
                elif schedule_type == "interval":
                    schedule, _ = IntervalSchedule.objects.get_or_create(
                        every=schedule_data["every"],
                        period=schedule_data["period"]
                    )
                    logging.info(f"[celery_load_tasks - handle] Horario creado o encontrado: {schedule}")
 
                else:
                    logging.warning(f"[celery_load_tasks - handle] Tarea '{task_data['name']}' ignorada: tipo de horario desconocido '{schedule_type}'")
                    continue
 
                if not PeriodicTask.objects.filter(name=task_data["name"]).exists():
                    PeriodicTask.objects.create(
                        crontab=schedule if schedule_type == "crontab" else None,
                        interval=schedule if schedule_type == "interval" else None,
                        name=task_data["name"],
                        task=task_data["task"],
                        args=json.dumps(task_data.get("args", [])),
                        one_off=False
                    )
                    self.stdout.write(self.style.SUCCESS(f"Tarea '{task_data['name']}' creada en Celery Beat"))
                    logging.info(f"[celery_load_tasks - handle] Tarea '{task_data['name']}' creada en Celery Beat")
                else:
                    self.stdout.write(self.style.WARNING(f"La tarea '{task_data['name']}' ya existe."))
                    logging.warning(f"[celery_load_tasks - handle] La tarea '{task_data['name']}' ya existe.")
 
        except (OperationalError, ProgrammingError, json.JSONDecodeError, ImproperlyConfigured) as e:
            self.stderr.write(self.style.ERROR(f"Error al cargar tareas desde JSON: {e}"))
            logging.error(f"[celery_load_tasks - handle] Error al cargar tareas desde JSON: {e}")