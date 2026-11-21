#!/usr/bin/env bash
# Stop the build if any command fails
set -o errexit

pip install -r requirements.txt

# Gather static files (CSS/JS for the site and Django's own pages) so WhiteNoise can serve them
python manage.py collectstatic --noinput

# Create or update the database tables
python manage.py migrate

# Create the admin account from Render environment variables (skipped if it already exists)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
  python manage.py createsuperuser --noinput || true
fi
