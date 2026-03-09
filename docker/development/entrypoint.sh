#!/bin/sh

set -e

# Wait for the database to be ready
/wait_for_db.sh

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Start the RQ worker in the background
rq worker default &

# Start the Django development server (with auto-reload)
python manage.py runserver 0.0.0.0:8000
