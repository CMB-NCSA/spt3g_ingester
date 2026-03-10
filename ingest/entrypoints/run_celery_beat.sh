#!/bin/bash

set -eo pipefail

cd "${APP_ROOT_DIR:-/opt}/ingest"

# Migrations should be created manually by developers and committed with the source code repo.
# Set the MAKE_MIGRATIONS env var to a non-empty string to create migration scripts
# after changes are made to the Django ORM models.
set +u
if [ "$MAKE_MIGRATIONS" == "true" ]; then
  echo "Generating database migration scripts..."
  python manage.py makemigrations --no-input core
  exit 0
fi
set -u

bash entrypoints/wait-for-it.sh ${DATABASE_HOST}:${DATABASE_PORT:-5432} --timeout=0
bash entrypoints/wait-for-it.sh ${MESSAGE_BROKER_HOST}:${MESSAGE_BROKER_PORT} --timeout=0

echo "Running initialization script..."
bash entrypoints/django_init.sh
echo "Django database initialization complete."

# Start worker
if [[ $DEV_MODE == "true" ]]; then
    watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- \
    celery -A project beat --loglevel ${CELERY_LOG_LEVEL:-DEBUG}
else
    celery -A project beat --loglevel ${CELERY_LOG_LEVEL:-INFO}
fi
