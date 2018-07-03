#!/usr/bin/env bash

# Nos aseguramos de que el script se corra como root
if [ "$(id -u)" != "0" ]; then
   echo "Este script debe correrse root" 1>&2
   exit 1
fi

export LC_ALL='es_AR.UTF-8'
export LANGUAGE='es_AR.UTF-8'
export LANG='es_AR.UTF-8'

for i in "$@"
do
case $i in
    -h=*|--dbhost=*)
    dbhost="${i#*=}"
    ;;
    -d=*|--dbname=*)
    dbname="${i#*=}"
    ;;
    -u=*|--dbuser=*)
    dbuser="${i#*=}"
    ;;
    -p=*|--dbpass=*)
    dbpass="${i#*=}"
    ;;
    *)
            # unknown option
    ;;
esac
done

if [ -z "$dbname" ]; then dbname='mapground'; echo "Base de datos por defecto: $dbname"; fi
if [ -z "$dbuser" ]; then dbuser='mapground'; echo "Usuario de base de datos por defecto: $dbuser"; fi

if [ -z "$dbhost" ]; then
   echo "Uso: setup.sh -h=<database host> [[-d=<database name>] [-u=<database user>] [-p=<database pass>]]" 1>&2
   exit 1
fi


if [ "$dbhost" = "localhost" ]; then
  echo "Configurando base de datos en localhost...";
  
  if [ -z "$dbpass" ]; then
    read -s -p "Ingrese el password para asignar al usuario de la base de datos:" dbpass;
    echo;
  fi

  ./setup_db.sh -d=$dbname -u=$dbuser -p=$dbpass ;
fi

if [ -z "$dbpass" ]; then
  read -s -p "Ingrese el password asignado al usuario de la base de datos:" dbpass;
  echo;
fi

SECRET_KEY=$(python mk_secret_key.py)

DIR="$( cd "$(dirname "$0")" ; pwd -P )"

DEV_USER="$(ls -ld $0 | awk '{print $3}')"

sed -e "s/mapground-db/${dbname}/g" MapGround/settings_db.py.template | sed -e "s/mapground-user/${dbname}/g" - | sed -e "s/mapground-password/${dbpass}/g" - | sed -e "s/secret-key/${SECRET_KEY}/g" > MapGround/settings_local_db.py
sed -e "s/\DEBUG = True$/DEBUG = False/" MapGround/settings_local.py.template > MapGround/settings_local.py
sed -e "s:/path/to/your/mapground:${DIR}:g" mapground_uwsgi.ini.template > mapground_uwsgi.ini
chown $DEV_USER MapGround/settings_local_db.py MapGround/settings_local.py mapground_uwsgi.ini

rm -rf /var/cache/mapground 2>/dev/null
rm -rf /var/local/mapground 2>/dev/null

mkdir /var/cache/mapground
mkdir /var/local/mapground
mkdir /var/local/mapground/media
cp -r mapfiles /var/local/mapground
touch /var/local/mapground/mapfiles/map-error.log
chmod 666 /var/local/mapground/mapfiles/map-error.log
cp -r data /var/local/mapground
# chown -R ${USER:=$(/usr/bin/id -run)}:$USER /var/local/mapground
cp mapcache/mapcache.xml.template /var/local/mapground/mapcache.xml

cp mapground_uwsgi.ini /etc/uwsgi/apps-available/mapground.ini
rm /etc/uwsgi/apps-enabled/mapground.ini 2>/dev/null
ln -s /etc/uwsgi/apps-available/mapground.ini /etc/uwsgi/apps-enabled/mapground.ini
sed -e "s:/path/to/your/mapground:${DIR}:g" mapground_nginx+apache.conf.template > /etc/nginx/sites-available/mapground
rm /etc/nginx/sites-enabled/mapground 2>/dev/null
ln -s /etc/nginx/sites-available/mapground /etc/nginx/sites-enabled/mapground
cp mapground_apache.conf.template /etc/apache2/sites-available/mapground.conf
rm /etc/apache2/sites-enabled/mapground.conf 2>/dev/null
ln -s /etc/apache2/sites-available/mapground.conf /etc/apache2/sites-enabled/mapground.conf

sudo -u ${DEV_USER} bash -c 'virtualenv --system-site-packages venv; source venv/bin/activate; pip install -r requirements.txt'

source venv/bin/activate

./mapcache/manage.py add world_borders
# python manage.py makemigrations
python manage.py migrate
python manage.py loaddata MapGround/fixtures/user.json
python manage.py loaddata layers/fixtures/initial_data.json

deactivate

chown -R www-data:www-data /var/local/mapground /var/cache/mapground

service uwsgi restart
service apache2 restart
service nginx restart