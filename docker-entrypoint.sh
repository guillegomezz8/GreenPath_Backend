#!/bin/bash

echo "Flush the manage.py command if any"
while ! python manage.py flush --no-input 2>&1; do
  echo "Flusing django manage command"
  sleep 3
done

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

echo "Apply fixtures"
# Wait for few minute and load some fixtures
while ! python manage.py loaddata apps/user/fixtures/*.json  2>&1; do
   echo "Populating db is in progress status"
   sleep 3
done

# Wait for setting passwords
while ! python manage.py set_user_passwords  2>&1; do
   echo "Setting password for Users"
   sleep 3
done

echo "Django docker is fully configured successfully."

exec "$@"