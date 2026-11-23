#!/bin/sh
set -e

# First start with an empty storage volume: copy in the product photos shipped with the image.
if [ ! -d storage/produtos ]; then
    cp -r storage-seed/. storage/
fi

# Creates the tables on a new database and applies new migrations after an update.
python manage.py migrate --noinput

exec "$@"
