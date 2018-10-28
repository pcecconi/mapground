#!/usr/bin/env bash

# Nos aseguramos de que el script se corra como root
if [ "$(id -u)" != "0" ]; then
   echo "Este script debe correrse root" 1>&2
   exit 1
fi

DEV_USER="$(ls -ld $0 | awk '{print $3}')"
sudo -u ${DEV_USER} bash -c 'virtualenv --system-site-packages venv; source venv/bin/activate; pip install -r requirements.txt'

source venv/bin/activate

python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput

deactivate

service uwsgi restart
service apache2 restart
service nginx restart