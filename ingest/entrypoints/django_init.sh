#!/bin/env bash
set -e

echo "Begin Django initialization..."

echo "Apply database migrations..."
python manage.py migrate
# echo "Provision database..."
# python manage.py createcachetable
# echo "Collect static files..."
# python manage.py collectstatic --no-input
echo "Initializing periodic tasks..."
python manage.py initialize_periodic_tasks

echo "Django initialization complete."
