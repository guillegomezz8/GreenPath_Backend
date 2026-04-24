#!/bin/bash
if [ "$SERVICE_NAME" = "celery" ]; then
    echo "Esperando a que la base de datos esté lista y migrada..."
 
    until python manage.py migrate --check; do

      echo "Esperando a que se apliquen las migraciones..."

      sleep 3

    done
fi

if [ "$SERVICE_NAME" = "greenpath_backend" ]; then
   echo "Migrate the Database at startup of project"
   # Wait for few minute and run db make migration
   while ! python manage.py makemigrations  2>&1; do
      echo "Make migrations is in progress status"
      sleep 3
   done

   # Wait for few minute and run db migration
   while ! python manage.py migrate  2>&1; do
      echo "Migration is in progress status"
      sleep 3
   done

   # echo "Apply fixtures"
   # # Wait for few minute and load some fixtures
   # while ! python manage.py loaddata apps/user/fixtures/*.json  2>&1; do
   #    echo "Populating db is in progress status"
   #    sleep 3
   # done

   # # Wait for setting passwords
   # while ! python manage.py set_user_passwords  2>&1; do
   #    echo "Setting password for Users"
   #    sleep 3
   # done

   # # Wait for setting passwords
   # while ! python manage.py celery_load_tasks  2>&1; do
   #    echo "Creating Celery Tasks"
   #    sleep 3
   # done

   echo "Django docker is fully configured successfully."
fi
exec "$@"